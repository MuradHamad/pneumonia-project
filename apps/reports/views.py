"""Reports views — Phase 2 stub (real generation in Phase 7)."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def report_list(request):
    return render(request, "coming_soon.html", {
        "page_title": "Reports",
        "description": "Generated clinical reports across cases. Available in Phase 7.",
    })
