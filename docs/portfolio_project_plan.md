# 【ポートフォリオ企画・設計書】Oracle APEX Keep-Alive & 死活監視システム

**プロジェクト名:** `Apex-Sentinel` (Oracle APEX Uptime & Cloud-Native Observability Dashboard)  
**アーキテクチャ:** Django + Google Cloud Firestore (NoSQL) + Cloud Run (Jobs / Service)

---

## 1. プロジェクトの背景・目的

### 1.1 背景と課題
- **Oracle APEX Free Tier の仕様**: 約7日間無通信だとインスタンスが自動休眠・停止される。
- **解決策**: 外部から定期的に REST API へヘルスチェックリクエストを送信し、インスタンスの生存を維持（Keep-Alive）する。

### 1.2 バックエンドエンジニア職種認定でのアピールポイント
単なるバッチスクリプトではなく、**実務で評価されるバックエンド設計思想**を盛り込んだシステムとして構成。

> [!IMPORTANT]
> **職種認定・面談での最重要アピール項目**
> 1. **Polyglot Persistence（適材適所のデータストア選定）**:
>    - トランザクション・基幹データ: **Oracle APEX (RDB)**
>    - 時系列監視ログ・メトリクス: **Google Cloud Firestore (NoSQL)**
>    - 「なぜNoSQLを選んだか（追記専用、JOIN不要、1日5万読取無料枠による$0運用）」を論理的に説明可能。
> 2. **Django × NoSQL のハイブリッドアーキテクチャ**:
>    - Djangoのルーティング・テンプレート・管理機構を活用しつつ、Service / Repository 層で Firestore SDK を抽象化するクリーンな設計。
> 3. **クラウドネイティブ (Google Cloud Run Jobs & Service)**:
>    - 常時起動サーバーを排除し、完全サーバーレスでインフラ費用ゼロ（FinOps）を実現。
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

    subgraph Database["NoSQL データストア (完全無料枠)"]
        FS[("Google Cloud Firestore<br/>(Collection: apex_health_logs)")]
    end

    subgraph WebApp["ポートフォリオ Web (Cloud Run Service)"]
        CRS["Django Web Application<br/>- 直近5日ステータス可視化 UI<br/>- REST API (JSON)<br/>- エンジニア実績解説"]
    end

    subgraph Client["閲覧者 / 評価者"]
        Browser["ブラウザ (面談官・エンジニア)"]
    end

    %% バッチフロー
    CS -->|HTTP / OIDC 起動| CRJ
    CRJ -->|1. Ping (HTTP GET)| APEX
    APEX -->|2. レスポンス (200 OK / Time)| CRJ
    CRJ -->|3. ログ保存 (insert)| FS

    %% Webフロー
    Browser -->|閲覧| CRS
    CRS -->|直近5日ログクエリ| FS
    CRS -->|HTML / JSON レスポンス| Browser
```

---

## 3. データモデル設計（Firestore Collection）

Firestore のドキュメント指向を活かし、時系列ログを管理します。

### コレクション名: `apex_health_logs`
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

### クエリ設計
- **直近5日分の取得**:  
  `db.collection("apex_health_logs").order_by("checked_at", direction=DESCENDING).limit(5)`  
  インデックスを活用し、最小の読み取り回数（5件分）で高速に描画。

---

## 4. アプリケーション設計（Django構成）

Django の責務をきれいに分離し、テスタビリティの高いバックエンド構成にします。

```
apex_sentinel/
├── manage.py
├── config/                  # Django プロジェクト設定
│   ├── settings.py
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

## 5. 画面（ポートフォリオUI）の要件

### 5.1 直近5日分の稼働状況インジケーター
- GitHub の Contributions や ステータスページ（UptimeRobot 風）の直感的なUI。
- 直近5日分の丸アイコン（● 緑: 正常 / ● 赤: 異常）を並べ、ホバーで日付とレスポンスタイム（例: `142ms`）を表示。
- 最新ステータスバッジ（例: `ALL SYSTEMS OPERATIONAL`）。

### 5.2 バックエンドエンジニアとしての解説エリア
- システム構成図（Mermaid / SVG）。
- 技術選定理由（Polyglot Persistence: Oracle RDB × Firestore NoSQL の対比）。
- スキルセット、GitHub リポジトリリンク。

---

## 6. 実装ロードマップ

1. **Step 1: Oracle APEX 側の REST API (ORDS) 準備** 【✅ 完了】
   - APEX SQL Workshop にてヘルスチェック用 GET エンドポイントを作成・curlテスト完了。
   - 詳細仕様書: [docs/oracle_apex_ords_setup.md](file:///c:/nakamura/study/202610以降/antigravity/docs/oracle_apex_ords_setup.md)
2. **Step 2: GCP 環境準備（Firestore 有効化 & サービスアカウント作成）**
   - Firestore を Native モードで作成（完全無料枠）。
3. **Step 3: Django プロジェクトの骨組み作成**
   - `monitor` アプリ、Firestore リポジトリ層、バッチコマンドの実装。
4. **Step 4: ポートフォリオダッシュボード画面の実装**
   - 直近5日ステータス表示（Tailwind CSS）。
5. **Step 5: Cloud Run へのデプロイ**
   - Cloud Run Jobs（バッチ）と Cloud Run Service（Web）のコンテナ作成・自動化。
