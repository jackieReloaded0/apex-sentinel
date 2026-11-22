# Apex-Sentinel

> Oracle APEX Uptime & Cloud-Native Observability Dashboard  
> (Django + Firestore NoSQL + Neon Serverless Postgres + Cloud Run)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Framework-Django-green.svg)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/Database-Neon%20Postgres-blue.svg)](https://neon.tech/)
[![GCP](https://img.shields.io/badge/Cloud-Google%20Cloud-yellow.svg)](https://cloud.google.com/)

---

## 📌 概要

Oracle Cloud Free Tier の Autonomous Database (Oracle APEX) は、約7日間の無通信で自動停止・削除される制約があります。  
本プロジェクトは、外部から定期的にヘルスチェックを行い稼働を維持（Keep-Alive）するとともに、直近の稼働メトリクスを収集・可視化する**クラウドネイティブな死活監視ダッシュボード**です。

バックエンドエンジニアとしての「適材適所のデータストア選定（Polyglot Persistence: Oracle RDB × Firestore NoSQL × Neon Serverless Postgres）」や「サーバーレスコンテナ設計（FinOps $0運用）」を実践したポートフォリオシステムです。

---

## 🏗️ アーキテクチャ

- **監視対象**: Oracle APEX (Autonomous Database / ORDS REST API)
- **定期実行バッチ**: Google Cloud Run Jobs + Cloud Scheduler（毎日 09:00 JST 自動実行）
- **時系列メトリクス保持**: Google Cloud Firestore (NoSQL, Native Mode)
- **管理情報・認証・セッション**: Neon (Serverless PostgreSQL, Scale-to-Zero)
- **Web API & ダッシュボード**: Google Cloud Run Service (Django)
  - 🌐 **本番公開 URL**: [https://apex-sentinel-web-961312396366.asia-northeast1.run.app](https://apex-sentinel-web-961312396366.asia-northeast1.run.app)
  - 🛡️ **FinOps / $0 運用**: 常時起動インスタンス 0 台。完全サーバーレス・自動スリープ構成。

---

## 🚀 ローカル起動・クイックスタート

### 1. 依存関係のセットアップ
```bash
# パッケージの同期・仮想環境構築 (uv を使用)
uv sync
```

### 2. 環境変数の準備
`.env.example` をコピーして `.env` を作成し、Neon の接続文字列を設定します。
```bash
cp .env.example .env
# .env を編集して DATABASE_URL などを設定
```

### 3. データベースのマイグレーション
```bash
uv run python manage.py migrate
```

### 4. 管理者アカウント（スーパーユーザー）の作成
```bash
uv run python manage.py createsuperuser
```

### 5. Web 開発サーバーの起動
```bash
uv run python manage.py runserver
```
起動後、ブラウザで以下にアクセスします：
- **ダッシュボード画面**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Django 管理画面**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

### 6. APEX 死活監視バッチの手動実行
```bash
uv run python manage.py check_apex
```

---

## 🧪 テストの実行 (pytest)

本プロジェクトでは `pytest` + `pytest-django` + `pytest-mock` による自動テストスイートを完備しています。  
テスト実行時はテスト用設定（`config/settings_test.py`）により、**本番 Neon (PostgreSQL) へのアクセスを自動遮断し、インメモリ SQLite を使用**するため、外部リソースを汚さず高速かつ安全にテストを実行できます。

### 1. 全テストスイートの実行
```bash
uv run pytest
```
（※ 単体テスト、結合テスト、セキュリティアクセス制御テストなど計 14 件が約 0.5 秒で実行されます）

### 2. 詳細ログ付き・特定ファイルのテスト実行
```bash
# 詳細出力 (-v) と標準出力キャプチャ無効 (-s)
uv run pytest -v -s

# 特定のテストモジュールのみ実行
uv run pytest tests/test_views.py
uv run pytest tests/test_apex_client.py
uv run pytest tests/test_security.py
```

### 3. 主なテスト内容
- **APEX HTTP 通信**: 正常 (200 OK)・異常 (503)・タイムアウト発生時の挙動検証
- **Firestore リポジトリ**: モックを用いたログ保存・取得クエリの検証
- **ダッシュボード & API**: 画面描画、手動ヘルスチェック API (`POST /api/check-apex/`)、Firestore 障害時フォールバック
- **セキュリティ・ルーティング**: 本番モード（`DEBUG=False`）時の Django 管理画面（`/admin/`）404 隠蔽回帰テスト

---

## 🐳 Docker Compose による完全ローカル起動

Neon や Google Cloud Firestore に接続せず、すべてローカルコンテナ（PostgreSQL + Firestore Emulator + Web）で自己完結させて起動することも可能です。

```bash
# 全コンテナのビルド & 起動 (PostgreSQL, Firestore Emulator, Django Web)
docker compose up -d

# ログの確認
docker compose logs -f web

# バッチ処理（APEX監視 -> ローカルFirestore保存）の実行テスト
docker compose run --rm batch
```

起動後、ブラウザで [http://127.0.0.1:8080/](http://127.0.0.1:8080/) にアクセスしてダッシュボードを確認できます。

コンテナの停止:
```bash
docker compose down
```

---

## 🌿 ブランチ運用ルール

本リポジトリはプロダクションの安全性を保つため、以下のブランチ戦略を採用しています：

- **`main`**: 保護された本番用ブランチ（直接の Push・削除・フォースプッシュは禁止）。PR 経由でのみマージ可能。
- **`develop`**: 開発・機能改修用のメインブランチ。改修作業は基本的にここから行い、検証後に `main` へ PR を作成します。

---

## 📚 ドキュメント

- [企画・設計書 (Portfolio Project Plan)](docs/portfolio_project_plan.md)
- [Neon (Serverless PostgreSQL) 導入・連携ガイド](docs/neon_integration_guide.md)
- [Oracle APEX ORDS 設定仕様書 & 手順書](docs/oracle_apex_ords_setup.md)
