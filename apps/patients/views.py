"""Patients views — Phase 2 stubs (real CRUD arrives in Phase 3)."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def patient_list(request):
    return render(request, "coming_soon.html", {
        "page_title": "Patients",
        "description": "Search and manage patient records. Available in Phase 3.",
    })


@login_required
def patient_new(request):
    return render(request, "coming_soon.html", {
        "page_title": "Register New Patient",
        "description": "Register a new patient. Available in Phase 3.",
    })
