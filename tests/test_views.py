"""
ビューおよび API エンドポイントのテスト
"""
import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_dashboard_view_success(client, mocker):
    """ダッシュボード画面が正常に表示されること (HTTP 200)"""
    mock_repo = mocker.patch("monitor.views.FirestoreRepository")
    mock_repo.return_value.get_recent_logs.return_value = [
        {
            "id": "20261122-120000",
            "checked_at": "2026-11-22T12:00:00Z",
            "status_code": 200,
            "response_time_ms": 120,
            "is_healthy": True,
            "error_message": None,
        }
    ]

    response = client.get(reverse("monitor:dashboard"))
    assert response.status_code == 200
    assert "サービス管理画面" in response.content.decode("utf-8")
    assert "120" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_dashboard_view_firestore_error_fallback(client, mocker):
    """Firestore 接続失敗時でもダッシュボードがクラッシュせず表示されること"""
    mock_repo = mocker.patch("monitor.views.FirestoreRepository")
    mock_repo.return_value.get_recent_logs.side_effect = Exception("Firestore unavailable")

    response = client.get(reverse("monitor:dashboard"))
    assert response.status_code == 200
    assert "Firestore 接続待機中" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_status_api_view_success(client, mocker):
    """JSON API エンドポイント (/api/status/) が正常に JSON を返却すること"""
    mock_repo = mocker.patch("monitor.views.FirestoreRepository")
    mock_repo.return_value.get_recent_logs.return_value = [
        {"id": "test-1", "status_code": 200, "is_healthy": True}
    ]

    response = client.get(reverse("monitor:status_api"))
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert len(data["logs"]) == 1


@pytest.mark.django_db
def test_manual_check_view_success(client, mocker):
    """手動ヘルスチェック API (POST) が正常に動作し、結果が Firestore に保存されること"""
    mock_client = mocker.patch("monitor.views.ApexClient")
    mock_client.return_value.check_health.return_value = {
        "target_url": "https://apex.oracle.com/test",
        "status_code": 200,
        "response_time_ms": 130,
        "is_healthy": True,
        "error_message": None,
    }

    mock_repo = mocker.patch("monitor.views.FirestoreRepository")
    mock_repo.return_value.save_log.return_value = "manual-20261122-120000"

    response = client.post(reverse("monitor:manual_check"))
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["result"]["status_code"] == 200
    assert data["result"]["id"] == "manual-20261122-120000"
    mock_repo.return_value.save_log.assert_called_once()


@pytest.mark.django_db
def test_manual_check_view_method_not_allowed(client):
    """手動ヘルスチェック API に GET でアクセスした場合は 405 Method Not Allowed になること"""
    response = client.get(reverse("monitor:manual_check"))
    assert response.status_code == 405


@pytest.mark.django_db
def test_manual_check_view_failure(client, mocker):
    """APEX 通信で想定外の例外が発生した際、500 とエラーメッセージが返ること"""
    mock_client = mocker.patch("monitor.views.ApexClient")
    mock_client.return_value.check_health.side_effect = RuntimeError("Fatal connection error")

    response = client.post(reverse("monitor:manual_check"))
    assert response.status_code == 500
    data = response.json()
    assert data["status"] == "error"
    assert "Fatal connection error" in data["message"]
