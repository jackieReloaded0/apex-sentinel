# =============================================================================
# Apex-Sentinel Dockerfile
# Cloud Run Service (Web) & Cloud Run Jobs (Batch) 兼用マルチステージビルド
# パッケージ管理: uv (超高速ビルド & 厳密な依存関係再現性)
# =============================================================================

# -----------------------------------------------------------------------------
# 1. ビルドステージ (依存関係の解決・インストール)
# -----------------------------------------------------------------------------
FROM python:3.14-slim@sha256:9aaa474097d094040649f2162a627c0049b408f52138d980916788d80f04802f AS builder

# uv バイナリを公式イメージから取得 (ダイジェスト固定)
COPY --from=ghcr.io/astral-sh/uv:latest@sha256:d3b601f0c7b118bc1753febf7c41cc80981df678445e0254284eecf84db79a7d /uv /bin/uv

# Python バイトコードの事前コンパイルを有効化
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# 依存関係定義のみを先にコピーして Docker キャッシュを最大化
COPY pyproject.toml uv.lock ./

# 本番用パッケージのみを仮想環境 (.venv) にインストール
RUN uv sync --frozen --no-install-project --no-dev


# -----------------------------------------------------------------------------
# 2. 実行用ランタイムステージ (軽量本番イメージ)
# -----------------------------------------------------------------------------
FROM python:3.14-slim@sha256:9aaa474097d094040649f2162a627c0049b408f52138d980916788d80f04802f AS runtime

# Python ランタイム最適化
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# ビルダーから完成した仮想環境 (.venv) のみをコピー
COPY --from=builder /app/.venv /app/.venv

# アプリケーションソースコードをコピー
COPY . .

# 静的ファイルの事前収集 (WhiteNoise による配信準備)
# ※ DB 接続不要でビルド時にアセットを圧縮・配置
RUN python manage.py collectstatic --noinput

# Cloud Run のデフォルト待受ポート
EXPOSE 8080

# -----------------------------------------------------------------------------
# 起動コマンド (1コンテナ・2ロール設計)
# - Cloud Run Service (Web): デフォルトの CMD (Gunicorn) で起動
# - Cloud Run Jobs (Batch): 実行時に "python manage.py check_apex" で上書き実行
# -----------------------------------------------------------------------------
CMD exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:${PORT:-8080} \
    --workers 2 \
    --threads 4 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -
