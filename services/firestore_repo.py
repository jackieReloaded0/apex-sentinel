"""
Google Cloud Firestore (NoSQL) とのやり取りを抽象化するリポジトリクラス。
時系列ログの保存・取得を担当します。
"""
from datetime import datetime, timezone
import logging
from google.cloud import firestore

logger = logging.getLogger(__name__)

COLLECTION_NAME = "apex_health_logs"


class FirestoreRepository:
    """
    Firestore の apex_health_logs コレクションに対するデータアクセスクラス。
    """

    def __init__(self, project_id: str | None = None):
        # 明示的な指定がなければ GOOGLE_CLOUD_PROJECT 環境変数またはデフォルト認証を利用
        self.db = firestore.Client(project=project_id)

    def save_log(self, log_data: dict) -> str:
        """
        ヘルスチェック結果を Firestore に保存します。
        ドキュメントID: YYYYMMDD-HHmmss
        """
        now = datetime.now(timezone.utc)
        doc_id = now.strftime("%Y%m%d-%H%M%S")

        payload = {
            "id": doc_id,
            "target_url": log_data.get("target_url"),
            "checked_at": now.isoformat(),
            "status_code": log_data.get("status_code"),
            "response_time_ms": log_data.get("response_time_ms"),
            "is_healthy": log_data.get("is_healthy", False),
            "error_message": log_data.get("error_message"),
        }

        doc_ref = self.db.collection(COLLECTION_NAME).document(doc_id)
        doc_ref.set(payload)
        return doc_id

    def get_recent_logs(self, limit: int = 5) -> list[dict]:
        """
        直近 N 件のヘルスチェックログを取得します（最新順）。
        """
        query = (
            self.db.collection(COLLECTION_NAME)
            .order_by("checked_at", direction=firestore.Query.DESCENDING)
            .limit(limit)
        )
        docs = query.stream()
        return [doc.to_dict() for doc in docs]
