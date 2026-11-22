"""
URL configuration for Apex-Sentinel project.
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("", include("monitor.urls")),
]

# ローカル開発環境 (または ENABLE_DJANGO_ADMIN=True 時) のみ /admin/ を登録
# 本番環境ではルーティング自体を除外して 404 とし、管理画面の存在を隠蔽します
if getattr(settings, "ENABLE_DJANGO_ADMIN", False):
    urlpatterns.insert(0, path("admin/", admin.site.urls))
