"""
URL configuration for Apex-Sentinel project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("monitor.urls")),
]
