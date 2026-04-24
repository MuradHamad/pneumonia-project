"""Project-level views (dashboard + error handlers)."""
from datetime import timedelta

from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone

from apps.accounts.decorators import clinician_required
from apps.cases.models import PatientCase
from apps.patients.models import Patient


def page_not_found(request, exception):
    """Custom 404 handler — renders even when DEBUG=True."""
    return render(request, "404.html", status=404)


def server_error(request):
    """Custom 500 handler — self-contained, no DB calls."""
    return render(request, "500.html", status=500)


@clinician_required
def dashboard(request):
    """Dashboard: stat counts, recent cases, severity distribution."""
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

    counts_by_class = dict(
        PatientCase.objects
        .filter(status=PatientCase.STATUS_DONE, risk_class__isnull=False)
        .values_list("risk_class")
        .annotate(n=Count("id"))
        .values_list("risk_class", "n")
    )
    total_done = sum(counts_by_class.values())
    severity_distribution = []
    for code, label in PatientCase.RISK_CLASS_CHOICES:
        count = counts_by_class.get(code, 0)
        pct = (count / total_done * 100) if total_done else 0
        severity_distribution.append({
            "code": code,
            "label": label,
            "count": count,
            "pct": round(pct, 1),
        })

    return render(request, "dashboard.html", {
        "stats": stats,
        "recent_cases": recent_cases,
        "severity_distribution": severity_distribution,
        "severity_total": total_done,
    })
