"""Admin for ClinicalData and PatientCase."""
from django.contrib import admin

from .models import ClinicalData, PatientCase


@admin.register(ClinicalData)
class ClinicalDataAdmin(admin.ModelAdmin):
    list_display = ("id", "age", "spo2", "respiratory_rate", "temperature", "confusion")
    search_fields = ("id",)


@admin.register(PatientCase)
class PatientCaseAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "clinician", "status", "risk_class", "created_at")
    list_filter = ("status", "risk_class")
    search_fields = ("patient__full_name", "patient__national_id")
    autocomplete_fields = ("patient", "clinician")
    readonly_fields = ("created_at",)
