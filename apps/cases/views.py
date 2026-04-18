"""Cases views — 3-step case creation wizard + stubs for list view."""
import uuid
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.accounts.decorators import clinician_required
from apps.patients.models import Patient

from .forms import ClinicalDataForm, XrayUploadForm
from .models import ClinicalData, PatientCase

WIZARD_SESSION_KEY = "case_wizard"


def _wizard_state(request) -> dict:
    return request.session.get(WIZARD_SESSION_KEY, {})


def _save_wizard_state(request, data: dict) -> None:
    request.session[WIZARD_SESSION_KEY] = data
    request.session.modified = True


def _clear_wizard_state(request) -> None:
    request.session.pop(WIZARD_SESSION_KEY, None)


def _resolve_patient(request):
    """Pull patient_id from GET or session. Returns Patient or None."""
    patient_id = request.GET.get("patient_id") or _wizard_state(request).get("patient_id")
    if not patient_id:
        return None
    return get_object_or_404(Patient, pk=patient_id)


@clinician_required
def case_list(request):
    """Stub — full list lands in Phase 5."""
    return render(request, "coming_soon.html", {
        "page_title": "All Cases",
        "description": "Browse and filter all diagnostic cases. Available in Phase 5.",
    })


@clinician_required
def case_new(request):
    """Step 1: upload X-ray. Persist temp file path + patient_id in session."""
    patient = _resolve_patient(request)
    if patient is None:
        messages.error(request, "Select a patient before starting a case.")
        return redirect("patients:list")

    if request.method == "POST":
        form = XrayUploadForm(request.POST, request.FILES)
        if form.is_valid():
            xray = form.cleaned_data["xray_image"]
            ext = Path(xray.name).suffix.lower()
            temp_name = f"xrays/_pending/{uuid.uuid4().hex}{ext}"
            saved_path = default_storage.save(temp_name, xray)

            state = _wizard_state(request)
            # If the user re-uploaded, drop the previous temp file.
            old = state.get("xray_temp_path")
            if old and old != saved_path and default_storage.exists(old):
                default_storage.delete(old)

            state.update({
                "patient_id": patient.id,
                "xray_temp_path": saved_path,
                "xray_original_name": xray.name,
            })
            _save_wizard_state(request, state)
            return redirect("cases:new_clinical")
    else:
        form = XrayUploadForm()

    return render(request, "cases/new_xray.html", {
        "patient": patient,
        "form": form,
        "current_step": 1,
    })


@clinician_required
def case_new_clinical(request):
    """Step 2: clinical data form."""
    state = _wizard_state(request)
    patient = _resolve_patient(request)
    if patient is None or not state.get("xray_temp_path"):
        messages.error(request, "Start the case by uploading an X-ray.")
        return redirect(f"{reverse('cases:new')}")

    initial = state.get("clinical_data") or {}
    if not initial.get("age") and patient.age is not None:
        initial["age"] = patient.age

    if request.method == "POST":
        form = ClinicalDataForm(request.POST)
        if form.is_valid():
            state["clinical_data"] = {
                k: (v if not hasattr(v, "isoformat") else v.isoformat())
                for k, v in form.cleaned_data.items()
            }
            _save_wizard_state(request, state)
            return redirect("cases:new_review")
    else:
        form = ClinicalDataForm(initial=initial)

    return render(request, "cases/new_clinical.html", {
        "patient": patient,
        "form": form,
        "current_step": 2,
    })


@clinician_required
def case_new_review(request):
    """Step 3: review + submit. Creates PatientCase with status=PENDING."""
    state = _wizard_state(request)
    patient = _resolve_patient(request)
    clinical = state.get("clinical_data")
    xray_temp = state.get("xray_temp_path")

    if patient is None or not clinical or not xray_temp:
        messages.error(request, "Complete earlier steps before reviewing.")
        return redirect("cases:new")

    if request.method == "POST":
        clinical_data = ClinicalData.objects.create(**clinical)
        case = PatientCase(
            patient=patient,
            clinician=request.user,
            clinical_data=clinical_data,
            status=PatientCase.STATUS_PENDING,
        )
        # Move the temp upload into the case's xray_image field.
        final_name = Path(xray_temp).name
        with default_storage.open(xray_temp, "rb") as src:
            case.xray_image.save(final_name, src, save=False)
        case.save()
        # Delete the temp-staging copy (xray_image.save created a new file under xrays/).
        if default_storage.exists(xray_temp):
            default_storage.delete(xray_temp)

        _clear_wizard_state(request)
        messages.success(request, f"Case #{case.id} created. Awaiting diagnosis.")
        return redirect("patients:detail", patient_id=patient.id)

    xray_url = settings.MEDIA_URL + xray_temp

    return render(request, "cases/new_review.html", {
        "patient": patient,
        "clinical": clinical,
        "xray_url": xray_url,
        "current_step": 3,
    })
