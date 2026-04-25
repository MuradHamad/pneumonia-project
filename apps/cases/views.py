"""Cases views — 3-step case creation wizard + list + detail."""
import logging
import traceback
import uuid
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.accounts.decorators import clinician_required
from apps.patients.models import Patient
from services import fusion_model

from .forms import CLINICAL_MODEL_FIELDS, ClinicalDataForm, XrayUploadForm
from .models import ClinicalData, PatientCase

logger = logging.getLogger(__name__)

WIZARD_SESSION_KEY = "case_wizard"


def _wizard_state(request) -> dict:
    return request.session.get(WIZARD_SESSION_KEY, {})


def _save_wizard_state(request, data: dict) -> None:
    request.session[WIZARD_SESSION_KEY] = data
    request.session.modified = True


def _clear_wizard_state(request) -> None:
    request.session.pop(WIZARD_SESSION_KEY, None)


def _resolve_patient(request):
    patient_id = request.GET.get("patient_id") or _wizard_state(request).get("patient_id")
    if not patient_id:
        return None
    return get_object_or_404(Patient, pk=patient_id)


def _run_diagnosis(case: PatientCase) -> None:
    """Call fusion_model.diagnose() and persist results.

    On success: fills AI output fields, sets status=DONE.
    On failure: sets status=FAILED, logs full traceback. Never raises.
    """
    try:
        cd = case.clinical_data
        clinical = {f: getattr(cd, f) for f in CLINICAL_MODEL_FIELDS}
        result = fusion_model.diagnose(case.xray_image.name, clinical, case_id=case.id)
        case.diag_probability = result["diag_probability"]
        case.severity_probability = result["severity_probability"]
        case.has_pneumonia = result["has_pneumonia"]
        case.is_severe = result["is_severe"]
        case.heatmap_path = result.get("heatmap_path")
        case.status = PatientCase.STATUS_DONE
        case.save(update_fields=[
            "diag_probability", "severity_probability", "has_pneumonia",
            "is_severe", "heatmap_path", "status",
        ])
    except Exception:
        logger.error(
            "Diagnosis failed for case #%s:\n%s", case.id, traceback.format_exc()
        )
        case.status = PatientCase.STATUS_FAILED
        case.save(update_fields=["status"])


@clinician_required
def case_list(request):
    """List + filter all diagnostic cases."""
    from django.core.paginator import Paginator
    from django.db.models import Q

    status = request.GET.get("status", "").strip().upper()
    diag_filter = request.GET.get("diag", "").strip()
    query = request.GET.get("q", "").strip()

    cases = PatientCase.objects.select_related("patient", "clinician").all()

    if status in {PatientCase.STATUS_PENDING, PatientCase.STATUS_DONE, PatientCase.STATUS_FAILED}:
        cases = cases.filter(status=status)

    if diag_filter == "pneumonia":
        cases = cases.filter(has_pneumonia=True)
    elif diag_filter == "no_pneumonia":
        cases = cases.filter(has_pneumonia=False)
    elif diag_filter == "severe":
        cases = cases.filter(has_pneumonia=True, is_severe=True)

    if query:
        cases = cases.filter(
            Q(patient__full_name__icontains=query)
            | Q(patient__national_id__icontains=query)
        )

    paginator = Paginator(cases, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "cases/list.html", {
        "page_obj": page_obj,
        "status_filter": status,
        "diag_filter": diag_filter,
        "q": query,
        "status_choices": PatientCase.STATUS_CHOICES,
    })


@clinician_required
def case_detail(request, case_id: int):
    """Case detail: X-ray + heatmap tabs, clinical data, diagnosis result."""
    case = get_object_or_404(
        PatientCase.objects.select_related("patient", "clinician", "clinical_data"),
        pk=case_id,
    )
    chat_messages = case.chat_messages.all()
    return render(request, "cases/detail.html", {
        "case": case,
        "chat_messages": chat_messages,
    })


@clinician_required
@require_POST
def case_retry(request, case_id: int):
    """Retry diagnosis for a FAILED case."""
    case = get_object_or_404(PatientCase, pk=case_id)
    if case.status != PatientCase.STATUS_FAILED:
        messages.error(request, "Case is not in a failed state.")
        return redirect("cases:detail", case_id=case.id)
    case.status = PatientCase.STATUS_PENDING
    case.save(update_fields=["status"])
    _run_diagnosis(case)
    if case.status == PatientCase.STATUS_DONE:
        messages.success(request, f"Retry successful — case #{case.id} diagnosed.")
    else:
        messages.error(request, f"Retry failed. Check the server log for details.")
    return redirect("cases:detail", case_id=case.id)


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
        return redirect(reverse("cases:new"))

    initial = state.get("clinical_data") or {}
    if not initial.get("age") and patient.age is not None:
        initial["age"] = patient.age

    if request.method == "POST":
        form = ClinicalDataForm(request.POST)
        if form.is_valid():
            # Store only model fields — temp_unit is form-only
            state["clinical_data"] = {
                k: (v if not hasattr(v, "isoformat") else v.isoformat())
                for k, v in form.cleaned_data.items()
                if k in CLINICAL_MODEL_FIELDS
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
    """Step 3: review + submit. Creates PatientCase, runs diagnosis synchronously."""
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
        final_name = Path(xray_temp).name
        with default_storage.open(xray_temp, "rb") as src:
            case.xray_image.save(final_name, src, save=False)
        case.save()
        if default_storage.exists(xray_temp):
            default_storage.delete(xray_temp)

        _run_diagnosis(case)
        _clear_wizard_state(request)

        if case.status == PatientCase.STATUS_DONE:
            messages.success(request, f"Case #{case.id} submitted — diagnosis complete.")
        else:
            messages.error(
                request,
                f"Case #{case.id} submitted but diagnosis failed. "
                "Check the case page for details.",
            )
        return redirect("cases:detail", case_id=case.id)

    xray_url = settings.MEDIA_URL + xray_temp

    return render(request, "cases/new_review.html", {
        "patient": patient,
        "clinical": clinical,
        "xray_url": xray_url,
        "current_step": 3,
    })
