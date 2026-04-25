"""Project-level views (dashboard + error handlers)."""
from datetime import timedelta

from django.shortcuts import render
from django.utils import timezone

from apps.accounts.decorators import clinician_required
from apps.cases.models import PatientCase
from apps.patients.models import Patient


def page_not_found(request, exception):
    return render(request, "404.html", status=404)


def server_error(request):
    return render(request, "500.html", status=500)


@clinician_required
def dashboard(request):
    """Dashboard: stat counts, recent cases, two-bucket diagnosis distribution."""
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

    done_qs = PatientCase.objects.filter(status=PatientCase.STATUS_DONE)
    no_pneu = done_qs.filter(has_pneumonia=False).count()
    pneu_mild = done_qs.filter(has_pneumonia=True, is_severe=False).count()
    pneu_severe = done_qs.filter(has_pneumonia=True, is_severe=True).count()
    total_done = no_pneu + pneu_mild + pneu_severe

    def _pct(n):
        return round(n / total_done * 100, 1) if total_done else 0

    severity_distribution = [
        {"label": "No Pneumonia",           "count": no_pneu,    "pct": _pct(no_pneu),    "color": "bg-success"},
        {"label": "Pneumonia (non-severe)", "count": pneu_mild,  "pct": _pct(pneu_mild),  "color": "bg-warning"},
        {"label": "Pneumonia (severe)",     "count": pneu_severe, "pct": _pct(pneu_severe), "color": "bg-danger"},
    ]

    return render(request, "dashboard.html", {
        "stats": stats,
        "recent_cases": recent_cases,
        "severity_distribution": severity_distribution,
        "severity_total": total_done,
    })
