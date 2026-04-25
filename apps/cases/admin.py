"""Admin for ClinicalData and PatientCase."""
from django.contrib import admin

from .models import ClinicalData, PatientCase


@admin.register(ClinicalData)
class ClinicalDataAdmin(admin.ModelAdmin):
    list_display = ("id", "age", "spo2", "hr", "rr", "temp_fahrenheit", "gcs_total")
    search_fields = ("id",)


@admin.register(PatientCase)
class PatientCaseAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "clinician", "status", "has_pneumonia", "is_severe", "created_at")
    list_filter = ("status", "has_pneumonia", "is_severe")
    search_fields = ("patient__full_name", "patient__national_id")
    autocomplete_fields = ("patient", "clinician")
    readonly_fields = ("created_at",)
