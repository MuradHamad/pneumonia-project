"""URL routes for accounts app."""
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.EmailLoginView.as_view(), name="login"),
    path("logout/", views.AppLogoutView.as_view(), name="logout"),
    path("change-password/", views.change_password_view, name="change_password"),
    path("settings/", views.settings_view, name="settings"),
    path("admin-panel/clinicians/", views.admin_clinicians, name="admin_clinicians"),
    path("admin-panel/overview/", views.admin_overview, name="admin_overview"),
]
