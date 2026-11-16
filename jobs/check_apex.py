"""
Oracle APEX Keep-Alive & Health Check Batch Job.
Cloud Run Jobs または Django 管理コマンドから実行されるバッチ処理本体です。
"""
import logging
from services.apex_client import ApexClient
from services.firestore_repo import FirestoreRepository

logger = logging.getLogger(__name__)


def run_check_apex():
    """
    Oracle APEX の ORDS REST API にヘルスチェックを送信し、
    結果（ステータスコード、レスポンスタイム等）を Firestore に保存します。
    """
    client = ApexClient()
    repo = FirestoreRepository()

    logger.info("Starting Oracle APEX health check...")
    result = client.check_health()
    logger.info(f"Health check result: {result}")

    saved_id = repo.save_log(result)
    logger.info(f"Successfully recorded health check log with ID: {saved_id}")
    return result


if __name__ == "__main__":
    import os
    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()
    run_check_apex()
