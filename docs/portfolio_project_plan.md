# 【ポートフォリオ企画・設計書】Oracle APEX Keep-Alive & 死活監視システム

**プロジェクト名:** `Apex-Sentinel` (Oracle APEX Uptime & Cloud-Native Observability Dashboard)  
**アーキテクチャ:** Django + Google Cloud Firestore (NoSQL) + Neon (Serverless PostgreSQL) + Cloud Run (Jobs / Service)

---

## 1. プロジェクトの背景・目的

### 1.1 背景と課題
- **Oracle APEX Free Tier の仕様**: 約7日間無通信だとインスタンスが自動休眠・停止される。
- **解決策**: 外部から定期的に REST API へヘルスチェックリクエストを送信し、インスタンスの生存を維持（Keep-Alive）する。

### 1.2 バックエンドエンジニア職種認定でのアピールポイント
単なるバッチスクリプトではなく、**実務で評価されるバックエンド設計思想**を盛り込んだシステムとして構成。

> [!IMPORTANT]
> **職種認定・面談での最重要アピール項目**
> 1. **Polyglot Persistence（3種の適材適所データストア選定）**:
>    - **基幹・監視対象 (RDB)**: Oracle APEX (Autonomous Database)
>    - **時系列監視メトリクス (NoSQL)**: Google Cloud Firestore（書き込み最適化、追記専用、JOIN不要、無料枠活用）
>    - **管理情報・認証・設定 (サーバーレス RDB)**: Neon PostgreSQL（Django Admin・セッションの永続化、Scale-to-Zero による完全$0運用、ステートレスコンテナとの親和性）
> 2. **Django × NoSQL × Serverless RDB のハイブリッド設計**:
>    - Djangoの標準認証・Admin・ORMの恩恵を Neon で享受しつつ、高頻度なログ収集は Firestore SDK（Repository パターン）で疎結合に分離。
> 3. **クラウドネイティブ & FinOps ($0運用)**:
>    - Cloud Run（Service/Jobs）+ Firestore + Neon により、常時起動サーバーを排除し、完全無料枠内でエンタープライズ級の堅牢性を実現。
> 4. **Django カスタム管理コマンドによるバッチ実装**:
>    - バッチ処理を `python manage.py check_apex` として実装し、Cloud Run Jobs から実行。コード資産の共通化とテスト容易性を確保。

---

## 2. 全体システムアーキテクチャ

```mermaid
flowchart TD
    subgraph Trigger["定期実行トリガー"]
        CS["Google Cloud Scheduler<br/>(1日1回 09:00 JST)"]
    end

    subgraph Batch["監視バッチ (Cloud Run Jobs)"]
        CRJ["Django Batch Worker<br/><code>python manage.py check_apex</code>"]
    end

    subgraph Target["監視対象"]
        APEX["Oracle APEX (ORDS)<br/>REST API Endpoint"]
    end

    subgraph DataStores["データストア群 (Polyglot Persistence)"]
        FS[("Google Cloud Firestore<br/>(時系列ログ: apex_health_logs)")]
        NEON[("Neon Serverless PostgreSQL<br/>(管理情報・認証・セッション)")]
    end

    subgraph WebApp["ポートフォリオ Web (Cloud Run Service)"]
        CRS["Django Web Application<br/>- 直近5日ステータス可視化 UI<br/>- REST API (JSON)<br/>- エンジニア実績解説<br/>- Django Admin (管理画面)"]
    end

    subgraph Client["閲覧者 / 評価者 / 管理者"]
        Browser["ブラウザ (面談官・エンジニア・管理者)"]
    end

    %% バッチフロー
    CS -->|HTTP / OIDC 起動| CRJ
    CRJ -->|1. Ping (HTTP GET)| APEX
    APEX -->|2. レスポンス (200 OK / Time)| CRJ
    CRJ -->|3. 時系列ログ保存| FS

    %% Webフロー
    Browser -->|閲覧・管理画面アクセス| CRS
    CRS -->|直近ログクエリ| FS
    CRS -->|認証・セッション・管理データ読み書き| NEON
    CRS -->|HTML / JSON レスポンス| Browser
```

---

## 3. データストア選定理由（Polyglot Persistence）

なぜ複数のデータベースを組み合わせるのか、技術的理由を明確に定義します。

| データストア | 種別 | 役割・格納データ | 選定理由・技術的メリット |
| :--- | :--- | :--- | :--- |
| **Oracle APEX** | RDB (クラウド) | 監視対象・業務データ | ポートフォリオの対象システム。Autonomous Database の制約（7日休眠）を解消する。 |
| **Google Cloud Firestore** | NoSQL (ドキュメント) | 時系列ヘルスチェックログ | ・追記専用（Append-only）でスキーマレス。<br>・1日5万回読み取り、2万回書き込みが完全無料。<br>・日付範囲や最新N件のクエリが高速。 |
| **Neon** | サーバーレス PostgreSQL | Django Admin、認証、セッション、設定 | ・Cloud Run のステートレス性（複数インスタンス、揮発性ディスク）で SQLite は使えない。<br>・Cloud SQL は月額固定費が発生するが、Neon は Scale-to-Zero で完全$0運用可能。<br>・Supabase のような「1週間放置で手動復帰が必要」な休眠がなく、リクエスト時に自動起動する。 |

---

## 4. データモデル設計

### 4.1 Firestore Collection: `apex_health_logs` (時系列ログ)
- ドキュメントID: `YYYYMMDD-HHmmss` (時系列ソート可能なID)

```json
{
  "id": "20261106-090000",
  "target_url": "https://.../ords/.../v1/health",
  "checked_at": "2026-11-06T09:00:00+09:00",
  "status_code": 200,
  "response_time_ms": 142,
  "is_healthy": true,
  "error_message": null
}
```

### 4.2 Neon (PostgreSQL): Django 管理情報
- Django 標準テーブル群:
  - `auth_user`, `auth_group`, `auth_permission` (管理者アカウント・権限)
  - `django_session` (管理画面セッション)
  - `django_admin_log` (管理画面操作ログ)
  - `django_migrations` (マイグレーション履歴)
- 将来的な拡張テーブル（監視対象エンドポイント設定マスタなど）

---

## 5. アプリケーション設計（Django構成）

Django の責務をきれいに分離し、テスタビリティの高いバックエンド構成にします。

```
apex_sentinel/
├── manage.py
├── config/                  # Django プロジェクト設定
│   ├── settings.py          # DATABASE_URL (Neon / ローカルSQLite切替)
│   ├── urls.py
│   └── wsgi.py
├── monitor/                 # 監視・ポートフォリオアプリ
│   ├── services/
│   │   ├── apex_client.py   # Oracle APEX への HTTP 通信クラス
│   │   └── firestore_repo.py# Firestore との読み書き抽象化クラス
│   ├── management/
│   │   └── commands/
│   │       └── check_apex.py# Cloud Run Jobs で動かすバッチコマンド
│   ├── views.py             # ダッシュボード画面 & API View
│   ├── urls.py
│   └── templates/
│       └── monitor/
│           └── dashboard.html# 直近5日間のステータス画面 (Tailwind CSS)
├── Dockerfile               # Cloud Run 用コンテナ定義
└── requirements.txt
```

---

## 6. 全体タスク一覧（ロードマップ）

今後の実装・環境構築作業の全ステップです。

### Phase 1: データベース・基盤準備
- [x] **Task 1.1: Oracle APEX ORDS REST API 構築・疎通確認**
  - GET エンドポイント作成、curl 疎通テスト完了（[oracle_apex_ords_setup.md](oracle_apex_ords_setup.md)）
- [ ] **Task 1.2: Neon アカウント開設 & PostgreSQL インスタンス作成**
  - プロジェクト作成（リージョン: 東京 or シンガポール）
  - 接続文字列（`DATABASE_URL`）の取得（Pooled URL / Direct URL）
  - 詳細手順: [neon_integration_guide.md](neon_integration_guide.md)
- [ ] **Task 1.3: Google Cloud 環境準備**
  - GCP プロジェクト作成
  - Firestore 有効化（Native モード、東京 `asia-northeast1`）
  - Secret Manager 有効化（`DATABASE_URL`, `DJANGO_SECRET_KEY` 等を格納）
  - サービスアカウント作成（Cloud Run 用: Secret Manager 閲覧、Firestore 読み書き権限）

### Phase 2: Django プロジェクト基盤実装
- [ ] **Task 2.1: Python 依存パッケージ定義 (`requirements.txt`)**
  - `django`, `psycopg[binary]`, `dj-database-url`, `google-cloud-firestore`, `requests`, `gunicorn`, `whitenoise`
- [ ] **Task 2.2: Django 初期化 & 設定 (`config/settings.py`)**
  - `dj-database-url` による Neon (本番) / SQLite (ローカル) の自動フォールバック設定
  - `whitenoise` による静的ファイル配信設定
- [ ] **Task 2.3: 初回マイグレーション & 管理者アカウント作成**
  - Neon への `migrate` 実行確認
  - スーパーユーザー作成（`createsuperuser`）および Django Admin ログイン検証

### Phase 3: コア機能実装（バッチ & ダッシュボード）
- [ ] **Task 3.1: APEX HTTP クライアント実装 (`monitor/services/apex_client.py`)**
  - タイムアウト設定、レスポンスタイム計測、ステータス判定
- [ ] **Task 3.2: Firestore リポジトリ実装 (`monitor/services/firestore_repo.py`)**
  - ログ保存（`save_log`）、直近ログ取得（`get_recent_logs`）
- [ ] **Task 3.3: バッチコマンド実装 (`monitor/management/commands/check_apex.py`)**
  - APEX ヘルスチェック実行 $\to$ Firestore 保存の単体実行コマンド
- [ ] **Task 3.4: ダッシュボード画面 & REST API 実装**
  - 直近5日稼働インジケーター（Tailwind CSS）
  - 技術解説セクション（構成図・Polyglot Persistence 選定理由）

### Phase 4: コンテナ化 & デプロイ
- [ ] **Task 4.1: Dockerfile & .dockerignore 作成**
  - マルチステージビルド、軽量 Python イメージ選定
- [ ] **Task 4.2: Cloud Run Service (Web) デプロイ**
  - Secret Manager 連携（Neon 接続文字列、Django 秘密鍵）
  - カスタムドメインまたは Cloud Run URL での疎通・Admin 動作確認
- [ ] **Task 4.3: Cloud Run Jobs (バッチ) デプロイ**
  - `python manage.py check_apex` 実行ジョブの作成
- [ ] **Task 4.4: Cloud Scheduler 定期実行設定**
  - 1日1回（JST 09:00）の Cloud Run Jobs トリガー設定
- [ ] **Task 4.5: E2E テスト & 監視自動化の検証**
  - バッチ実行 $\to$ Firestore 保存 $\to$ Web ダッシュボード反映の一連フロー確認
