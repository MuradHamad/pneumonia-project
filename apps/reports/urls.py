"""Reports URLs."""
from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.report_list, name="list"),
    path("cases/<int:case_id>/", views.report_preview, name="preview"),
    path("cases/<int:case_id>/generate/", views.report_generate, name="generate"),
    path("cases/<int:case_id>/export.pdf", views.report_export_pdf, name="export_pdf"),
    path("cases/<int:case_id>/export.csv", views.report_export_csv, name="export_csv"),
]
