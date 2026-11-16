"""
Oracle APEX (ORDS REST API) との通信を担当するクライアントアダプタ。
"""
import time
import requests
from django.conf import settings


class ApexClient:
    """
    Oracle APEX の ORDS REST API に対する HTTP 通信および計測を行うクラス。
    """

    def __init__(self, target_url: str | None = None, timeout: int = 10):
        self.target_url = target_url or getattr(settings, "APEX_HEALTH_URL", "")
        self.timeout = timeout

    def check_health(self) -> dict:
        """
        ヘルスチェックエンドポイントへ GET リクエストを送信し、
        レスポンスコード、所要時間(ms)、死活状態を返します。
        """
        if not self.target_url:
            raise ValueError("APEX_HEALTH_URL is not configured in settings or environment.")

        start_time = time.perf_counter()
        try:
            response = requests.get(self.target_url, timeout=self.timeout)
            duration_ms = int((time.perf_counter() - start_time) * 1000)

            return {
                "target_url": self.target_url,
                "status_code": response.status_code,
                "response_time_ms": duration_ms,
                "is_healthy": response.status_code == 200,
                "error_message": None if response.status_code == 200 else response.text[:200],
            }
        except requests.RequestException as e:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return {
                "target_url": self.target_url,
                "status_code": 0,
                "response_time_ms": duration_ms,
                "is_healthy": False,
                "error_message": str(e),
            }
