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
