"""Cases URLs."""
from django.urls import path

from . import views

app_name = "cases"

urlpatterns = [
    path("", views.case_list, name="list"),
    path("new/", views.case_new, name="new"),
    path("new/clinical/", views.case_new_clinical, name="new_clinical"),
    path("new/review/", views.case_new_review, name="new_review"),
    path("<int:case_id>/", views.case_detail, name="detail"),
]
