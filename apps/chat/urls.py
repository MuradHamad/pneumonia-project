"""Chat URLs — per-case message endpoint."""
from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("cases/<int:case_id>/send/", views.send_message, name="send"),
]
