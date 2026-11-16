# AGENTS.md - Workspace Agent Rules & Guidelines

本ファイルは、本プロジェクト（`Apex-Sentinel`）で作業を行うすべての AI エージェントが厳守すべき基本ルールおよび制約事項を定義したものです。

---

## 1. セキュリティ & プライバシー規約（最重要・厳守）

- **`.env` および機密ファイルの読み込み禁止**:
  - `.env`, `*.env`, `service-account.json`, `credentials.json`, `*.pem`, `*.key` 等の機密情報・シークレットファイルを、`read_file` やシェルコマンド（`cat`, `head`, `tail`, `grep`, `python` スクリプト等）で**読み込むこと、中身を検査すること、チャット・ログに出力することは固く禁止**します。
  - パスワード、APIキー、データベース接続URL等のクレデンシャルは、いかなる場合もプレーンテキストとして出力してはなりません。
- **環境変数の扱い**:
  - 新たな環境変数が必要になった場合は、公開可能なダミー値を用いて [`.env.example`](.env.example) を更新し、実際の値はユーザー自身に `.env` に設定してもらってください。

---

## 2. 開発・アーキテクチャ標準

- **パッケージ管理**:
  - パッケージ管理およびスクリプト実行には `uv` を使用してください（`pip` や `pipenv` ではなく `uv add`, `uv run` を使用）。
- **データストアの責務分離（Polyglot Persistence）**:
  - **Oracle APEX**: 外部監視対象（ORDS REST API）
  - **Google Cloud Firestore**: 時系列ヘルスチェックログ・メトリクス（NoSQL）
  - **Neon (PostgreSQL)**: Django Admin、ユーザー認証、セッション、マイグレーション管理
- **コード設計**:
  - Web画面（`monitor/`）と定期バッチ（`jobs/`）の共通ロジック（APEX通信・Firestore操作）は、必ず `services/` 層に切り出して再利用してください。

