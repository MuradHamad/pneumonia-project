"""Patient views — list, register, detail."""
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.accounts.decorators import clinician_required

from .forms import PatientForm
from .models import Patient


@clinician_required
def patient_list(request):
    """List + search patients. Search: full_name or national_id. Optional gender filter."""
    query = request.GET.get("q", "").strip()
    gender = request.GET.get("gender", "").strip().upper()

    patients = Patient.objects.select_related("registered_by").all()
    if query:
        patients = patients.filter(
            Q(full_name__icontains=query) | Q(national_id__icontains=query)
        )
    if gender in {Patient.GENDER_MALE, Patient.GENDER_FEMALE}:
        patients = patients.filter(gender=gender)

    paginator = Paginator(patients, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "patients/list.html", {
        "page_obj": page_obj,
        "q": query,
        "gender_filter": gender,
        "genders": Patient.GENDER_CHOICES,
    })


@clinician_required
def patient_new(request):
    """Register a new patient. Duplicate national_id shows inline warning with link to existing."""
    existing = None

    if request.method == "POST":
        form = PatientForm(request.POST)
        nid = (request.POST.get("national_id") or "").strip()
        if nid:
            existing = Patient.objects.filter(national_id=nid).first()

        if form.is_valid():
            patient = form.save(commit=False)
            patient.registered_by = request.user
            patient.save()
            messages.success(request, f"Patient {patient.full_name} registered.")
            if request.POST.get("action") == "register_and_case":
                return redirect(f"{reverse('cases:new')}?patient_id={patient.id}")
            return redirect("patients:detail", patient_id=patient.id)
    else:
        form = PatientForm()

    return render(request, "patients/new.html", {"form": form, "existing": existing})


@clinician_required
def patient_detail(request, patient_id: int):
    """Patient info card + case history table."""
    patient = get_object_or_404(Patient.objects.select_related("registered_by"), pk=patient_id)
    # Cases relation arrives in Phase 4; empty list for now.
    cases: list = []
    return render(request, "patients/detail.html", {"patient": patient, "cases": cases})
