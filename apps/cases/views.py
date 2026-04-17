"""Cases views — Phase 2 stubs (real flow arrives in Phase 4)."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def case_list(request):
    return render(request, "coming_soon.html", {
        "page_title": "All Cases",
        "description": "Browse and filter all diagnostic cases. Available in Phase 5.",
    })


@login_required
def case_new(request):
    return render(request, "coming_soon.html", {
        "page_title": "New Case",
        "description": "Three-step case creation flow. Available in Phase 4.",
    })
