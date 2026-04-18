"""Admin for Patient."""
from django.contrib import admin

from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("full_name", "national_id", "gender", "date_of_birth", "registered_by", "created_at")
    list_filter = ("gender",)
    search_fields = ("full_name", "national_id", "phone_number")
    autocomplete_fields = ("registered_by",)
    readonly_fields = ("created_at",)
