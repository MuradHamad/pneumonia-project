"""Project-level views (dashboard)."""
from datetime import timedelta

from django.shortcuts import render
from django.utils import timezone

from apps.accounts.decorators import clinician_required
from apps.cases.models import PatientCase
from apps.patients.models import Patient


@clinician_required
def dashboard(request):
    """Dashboard: real stat counts + recent cases list."""
    week_ago = timezone.now() - timedelta(days=7)

    stats = {
        "patients": Patient.objects.count(),
        "cases": PatientCase.objects.count(),
        "cases_this_week": PatientCase.objects.filter(created_at__gte=week_ago).count(),
        "pending": PatientCase.objects.filter(status=PatientCase.STATUS_PENDING).count(),
    }

    recent_cases = (
        PatientCase.objects
        .select_related("patient")
        .order_by("-created_at")[:5]
    )

    return render(request, "dashboard.html", {
        "stats": stats,
        "recent_cases": recent_cases,
    })
