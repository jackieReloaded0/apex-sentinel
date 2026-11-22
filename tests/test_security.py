"""
セキュリティおよびルーティング制御のテスト
"""
import pytest
from django.conf import settings
from django.urls import clear_url_caches
from importlib import reload
import config.urls


def test_admin_hidden_when_disabled(client, monkeypatch):
    """ENABLE_DJANGO_ADMIN=False のとき、/admin/ は 404 Not Found になること"""
    monkeypatch.setattr(settings, "ENABLE_DJANGO_ADMIN", False)
    clear_url_caches()
    reload(config.urls)

    response = client.get("/admin/")
    assert response.status_code == 404


def test_admin_accessible_when_enabled(client, monkeypatch):
    """ENABLE_DJANGO_ADMIN=True のとき、/admin/ は利用可能（リダイレクトまたは200）であること"""
    monkeypatch.setattr(settings, "ENABLE_DJANGO_ADMIN", True)
    clear_url_caches()
    reload(config.urls)

    response = client.get("/admin/")
    # 未ログイン時はログイン画面へリダイレクト (302) または 200
    assert response.status_code in [200, 302]
