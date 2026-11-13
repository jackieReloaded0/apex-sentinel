# Neon (Serverless PostgreSQL) 導入・連携ガイド & タスク詳細

本ドキュメントは、`Apex-Sentinel` における Django 管理情報・認証用のデータストアとして **Neon (Serverless PostgreSQL)** を導入するための詳細手順と設定ガイドです。

---

## 1. Neon の役割と設計方針

- **役割**: Django Admin、セッション管理（`django_session`）、ユーザー認証（`auth_user`）、マイグレーション履歴の永続化。
- **コスト**: Scale-to-Zero（無通信時の自動停止）により、無料枠内で完全 $0 運用。
- **ハイブリッド接続設計**:
  - **ローカル開発**: 環境変数 `DATABASE_URL` が未設定の場合は、手軽な `sqlite3` に自動フォールバック。
  - **ステージング / 本番 (Cloud Run)**: Secret Manager 経由で Neon の `DATABASE_URL` を注入して接続。

---

## 2. 接続方式の使い分け（Direct vs Pooled）

Neon はダッシュボードで2種類の接続文字列（URL）を提供します。

| 接続タイプ | ポート / 特徴 | 推奨用途 |
| :--- | :--- | :--- |
| **Pooled (推奨)** | `ep-xxx-pooler...:6543`<br>PgBouncer によるコネクションプーリング | **Cloud Run Service (Web)**<br>インスタンスの急な増減でも DB 接続数が枯渇しない。 |
| **Direct** | `ep-xxx...:5432`<br>PostgreSQL 直接接続 | **マイグレーション (`migrate`) 実行時**<br>DDL やトランザクションロックを伴う処理で推奨。 |

> [!TIP]
> Django + Cloud Run での通常運用は、**Pooled（PgBouncer 経由）の接続URL**を `DATABASE_URL` として指定すればOKです。

---

## 3. 具体的な導入ステップ & チェックリスト

### Step 1: Neon アカウント開設 & プロジェクト作成
- [ ] 1. [Neon 公式サイト](https://neon.tech/) にサインアップ（GitHub / Google アカウントでOK）。
- [ ] 2. 新規プロジェクトを作成:
  - **Project Name**: `apex-sentinel`
  - **Postgres Version**: `16` (推奨)
  - **Region**: Cloud Run と物理的に近いリージョンを選択（例: `AWS / ap-southeast-1 (Singapore)` または `ap-northeast-1 (Tokyo)` ※利用可能な場合）。
- [ ] 3. ダッシュボードから **Connection String** をコピー:
  - 形式: `postgresql://[user]:[password]@[endpoint]-pooler.neon.tech/[dbname]?sslmode=require`

### Step 2: Django 側の設定準備
- [ ] 1. `requirements.txt` に PostgreSQL アダプタと設定ライブラリを追加:
  ```txt
  psycopg[binary]>=3.1.0
  dj-database-url>=2.1.0
  ```
- [ ] 2. `config/settings.py` の `DATABASES` を環境変数連動型に設定:
  ```python
  import dj_database_url
  import os
  from pathlib import Path

  BASE_DIR = Path(__file__).resolve().parent.parent

  # DATABASE_URL が設定されていれば Neon (PostgreSQL) を利用、なければローカル sqlite3
  default_db_url = f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
  DATABASES = {
      'default': dj_database_url.config(
          default=os.environ.get('DATABASE_URL', default_db_url),
          conn_max_age=600,
          conn_health_checks=True,
          ssl_require=True if os.environ.get('DATABASE_URL') else False,
      )
  }
  ```

### Step 3: Google Cloud Secret Manager への登録
- [ ] 1. GCP Secret Manager にシークレットを作成:
  - シークレット名: `DATABASE_URL`
  - 値: Neon の接続文字列 (`postgresql://...`)
- [ ] 2. Cloud Run のサービスアカウントに `roles/secretmanager.secretAccessor` を付与。
- [ ] 3. Cloud Run Service のデプロイ時に環境変数としてシークレットをマウント:
  ```bash
  gcloud run deploy apex-sentinel-web \
    --image gcr.io/[PROJECT_ID]/apex-sentinel \
    --set-secrets="DATABASE_URL=DATABASE_URL:latest" \
    ...
  ```

### Step 4: 初回マイグレーションと管理者作成
- [ ] 1. ローカルから Neon へマイグレーションを適用:
  ```bash
  export DATABASE_URL="postgresql://[user]:[password]@[endpoint].neon.tech/[dbname]?sslmode=require"
  python manage.py migrate
  python manage.py createsuperuser
  ```
- [ ] 2. Cloud Run Service 起動後、`/admin` にアクセスし、Neon 経由でログインできることを確認。

