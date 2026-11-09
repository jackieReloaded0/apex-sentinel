# Oracle APEX ORDS (RESTful サービス) 設定仕様書 & セットアップ手順

**対象システム:** `Apex-Sentinel` (Oracle APEX Uptime & Cloud-Native Observability Dashboard)  
**作成日:** 2026-11-06  
**ステータス:** 構築・疎通確認完了 (Verified)

---

## 1. 概要と目的

Oracle APEX (Oracle Cloud Free Tier / Autonomous Database) の自動休眠・停止を防止するため、外部（Google Cloud Run Jobs）から定期的に呼び出す軽量なヘルスチェック用 REST API エンドポイントを ORDS (Oracle REST Data Services) 上に構築します。

### 設計上の考慮点（バックエンドエンジニア視点）
- **高可用性・低負荷**: 業務テーブルには一切アクセスせず、Oracleの仮想表 `dual` を用いることで、データベースに負荷をかけずにインスタンスとリスナーの生存（HTTP 200）を確認。
- **セキュリティ**: 個人情報や業務データを一切返さない固定レスポンス設計のため、パブリックGETエンドポイントとして安全に公開。

---

## 2. エンドポイント仕様

| 項目 | 設定値 |
| :--- | :--- |
| **HTTP Method** | `GET` |
| **モジュール名 (Module)** | `sentinel` |
| **ベースパス (Base Path)** | `sentinel/` |
| **URIテンプレート (Template)** | `ping` |
| **完全なパス (Path)** | `/ords/{workspace_schema}/sentinel/ping` |
| **認証 (Authentication)** | なし（公開ヘルスチェック用） |
| **レスポンス形式 (Format)** | `application/json` |

---

## 3. APEX 設定手順（再現手順）

1. **APEX 管理画面へのログイン**:
   - ワークスペース管理者または開発者としてログイン。
2. **RESTful サービスの有効化**:
   - 上部メニュー `SQLワークショップ (SQL Workshop)` > `RESTful サービス (RESTful Services)` を開く。
   - ※初回のみ: `スキーマの有効化 (Enable Schema)` を実行。
3. **モジュールの作成**:
   - `モジュール名`: `sentinel`
   - `ベース・パス`: `sentinel/`
   - `公開`: `はい (Yes)`
4. **テンプレートの作成**:
   - `URIテンプレート`: `ping`
5. **GET ハンドラの作成**:
   - `メソッド`: `GET`
   - `ソース・タイプ`: `コレクション問合せ (Collection Query)`
   - `形式`: `JSON`
   - `問合せ (SQL Query)`:
     ```sql
     select 
         'ok' as status,
         current_timestamp as server_time,
         'apex-sentinel' as service
     from dual
     ```

---

## 4. レスポンス仕様（JSON）

### 正常系レスポンス (`HTTP 200 OK`)
ORDS により、SQL の問い合わせ結果が以下の JSON 構造で自動ラップされて返却されます。

```json
{
  "items": [
    {
      "status": "ok",
      "server_time": "2026-11-06T09:22:00Z",
      "service": "apex-sentinel"
    }
  ],
  "hasMore": false,
  "limit": 25,
  "offset": 0,
  "count": 1,
  "links": [
    {
      "rel": "self",
      "href": "https://.../ords/.../sentinel/ping"
    }
  ]
}
```

---

## 5. 疎通確認（テスト結果）

以下のコマンドにより、HTTP 200 OK および JSON ペイロードの正常返却を確認済み：

```bash
curl -i -X GET "https://<your-oracle-domain>/ords/<schema>/sentinel/ping"
```
