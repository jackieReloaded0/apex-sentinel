import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from services.apex_client import ApexClient
from services.firestore_repo import FirestoreRepository

logger = logging.getLogger(__name__)


def dashboard_view(request):
    """
    ダッシュボード画面を表示するビュー。
    直近5日分のヘルスチェックログを取得してテンプレートに渡します。
    """
    recent_logs = []
    error_message = None

    try:
        repo = FirestoreRepository()
        recent_logs = repo.get_recent_logs(limit=5)
    except Exception as e:
        logger.warning(f"Could not fetch Firestore logs: {e}")
        error_message = "Firestore 接続待機中、または設定確認中"

    context = {
        "recent_logs": recent_logs,
        "latest_log": recent_logs[0] if recent_logs else None,
        "error_message": error_message,
    }
    return render(request, "monitor/dashboard.html", context)


def status_api_view(request):
    """
    最新のヘルスチェックステータスを返却する JSON API ビュー。
    """
    try:
        repo = FirestoreRepository()
        recent_logs = repo.get_recent_logs(limit=5)
        return JsonResponse({"status": "ok", "logs": recent_logs})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@require_POST
def manual_check_view(request):
    """
    手動で即時ヘルスチェックを実行し、結果を Firestore に保存して返却する API ビュー。
    """
    try:
        client = ApexClient()
        result = client.check_health()

        repo = FirestoreRepository()
        doc_id = repo.save_log(result)
        result["id"] = doc_id

        return JsonResponse({
            "status": "ok",
            "message": "ヘルスチェックが正常に完了しました。",
            "result": result
        })
    except Exception as e:
        logger.error(f"Manual health check failed: {e}")
        return JsonResponse({
            "status": "error",
            "message": f"ヘルスチェック実行に失敗しました: {str(e)}"
        }, status=500)
