"""Admin for Report."""
from django.contrib import admin

from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("id", "patient_case", "format", "generated_at")
    list_filter = ("format",)
    search_fields = ("patient_case__patient__full_name",)
    readonly_fields = ("generated_at",)
