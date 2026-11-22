"""
APEX HTTP クライアントの単体テスト
"""
import pytest
import requests
from services.apex_client import ApexClient


def test_apex_client_success(mocker):
    """正常時 (200 OK) のヘルスチェック検証"""
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.text = '{"status": "UP"}'
    mocker.patch("requests.get", return_value=mock_response)

    client = ApexClient(target_url="https://apex.oracle.com/test", timeout=5)
    result = client.check_health()

    assert result["is_healthy"] is True
    assert result["status_code"] == 200
    assert result["error_message"] is None
    assert result["target_url"] == "https://apex.oracle.com/test"
    assert "response_time_ms" in result


def test_apex_client_http_error(mocker):
    """APEX 側が 503 などのエラーを返したときの検証"""
    mock_response = mocker.Mock()
    mock_response.status_code = 503
    mock_response.text = "Service Unavailable"
    mocker.patch("requests.get", return_value=mock_response)

    client = ApexClient(target_url="https://apex.oracle.com/test")
    result = client.check_health()

    assert result["is_healthy"] is False
    assert result["status_code"] == 503
    assert "Service Unavailable" in result["error_message"]


def test_apex_client_network_timeout(mocker):
    """ネットワークタイムアウト等の例外発生時の検証"""
    mocker.patch("requests.get", side_effect=requests.Timeout("Connection timed out"))

    client = ApexClient(target_url="https://apex.oracle.com/test")
    result = client.check_health()

    assert result["is_healthy"] is False
    assert result["status_code"] == 0
    assert "Connection timed out" in result["error_message"]


def test_apex_client_missing_url():
    """ターゲット URL 未設定時の例外発生を検証"""
    client = ApexClient(target_url="")
    with pytest.raises(ValueError, match="APEX_HEALTH_URL is not configured"):
        client.check_health()
