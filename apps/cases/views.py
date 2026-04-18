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
from services import fusion_model

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


CLINICAL_FIELDS = (
    "age", "spo2", "blood_pressure", "respiratory_rate",
    "temperature", "urea", "ph", "wbc_count", "confusion",
)


def _run_diagnosis(case: "PatientCase") -> None:
    """Call fusion_model.diagnose() and persist results. Flip status to DONE."""
    cd = case.clinical_data
    clinical = {f: getattr(cd, f) for f in CLINICAL_FIELDS}
    result = fusion_model.diagnose(case.xray_image.name, clinical)
    case.severity_score = result["severity_score"]
    case.risk_class = result["risk_class"]
    case.heatmap_path = result.get("heatmap_path")
    case.confidence_score = result["confidence_score"]
    case.status = PatientCase.STATUS_DONE
    case.save(update_fields=[
        "severity_score", "risk_class", "heatmap_path",
        "confidence_score", "status",
    ])


@clinician_required
def case_list(request):
    """List + filter all diagnostic cases."""
    from django.core.paginator import Paginator

    status = request.GET.get("status", "").strip().upper()
    risk = request.GET.get("risk", "").strip().upper()
    query = request.GET.get("q", "").strip()

    cases = PatientCase.objects.select_related("patient", "clinician").all()
    if status in {PatientCase.STATUS_PENDING, PatientCase.STATUS_DONE}:
        cases = cases.filter(status=status)
    if risk in dict(PatientCase.RISK_CLASS_CHOICES):
        cases = cases.filter(risk_class=risk)
    if query:
        from django.db.models import Q
        cases = cases.filter(
            Q(patient__full_name__icontains=query)
            | Q(patient__national_id__icontains=query)
        )

    paginator = Paginator(cases, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "cases/list.html", {
        "page_obj": page_obj,
        "status_filter": status,
        "risk_filter": risk,
        "q": query,
        "status_choices": PatientCase.STATUS_CHOICES,
        "risk_choices": PatientCase.RISK_CLASS_CHOICES,
    })


@clinician_required
def case_detail(request, case_id: int):
    """Case detail: X-ray, clinical data, diagnosis result card.

    Placeholder diagnose() is synchronous; any case still at PENDING
    (e.g. created before the service was wired up) gets diagnosed on
    first view. When Phase 11 swaps in the real async model, this
    backfill will be removed.
    """
    case = get_object_or_404(
        PatientCase.objects.select_related("patient", "clinician", "clinical_data"),
        pk=case_id,
    )
    if case.status == PatientCase.STATUS_PENDING:
        _run_diagnosis(case)
    chat_messages = case.chat_messages.all()
    return render(request, "cases/detail.html", {
        "case": case,
        "chat_messages": chat_messages,
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
        final_name = Path(xray_temp).name
        with default_storage.open(xray_temp, "rb") as src:
            case.xray_image.save(final_name, src, save=False)
        case.save()
        if default_storage.exists(xray_temp):
            default_storage.delete(xray_temp)

        _run_diagnosis(case)

        _clear_wizard_state(request)
        messages.success(request, f"Case #{case.id} diagnosed — Risk Class {case.risk_class}.")
        return redirect("cases:detail", case_id=case.id)

    xray_url = settings.MEDIA_URL + xray_temp

    return render(request, "cases/new_review.html", {
        "patient": patient,
        "clinical": clinical,
        "xray_url": xray_url,
        "current_step": 3,
    })
