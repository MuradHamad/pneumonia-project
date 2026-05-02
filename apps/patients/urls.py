"""Patients URLs."""

from django.urls import path

from . import views

app_name = "patients"

urlpatterns = [
    path("", views.patient_list, name="list"),
    path("new/", views.patient_new, name="new"),
    path("<int:patient_id>/", views.patient_detail, name="detail"),
    path("<int:patient_id>/edit/", views.patient_edit, name="edit"),
]
