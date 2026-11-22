from django.urls import path
from . import views

app_name = "monitor"

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("api/status/", views.status_api_view, name="status_api"),
    path("api/check-apex/", views.manual_check_view, name="manual_check"),
]
