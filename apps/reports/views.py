"""Reports views — preview, generate, export (PDF/CSV), list."""
import csv
from io import BytesIO

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from apps.accounts.decorators import clinician_required
from apps.cases.models import PatientCase
from services import report_builder

from .models import Report


# Built-in reportlab fonts (Helvetica/Times) lack many Unicode glyphs.
# Replace known medical/scientific symbols with ASCII equivalents before
# rendering. Registering a Unicode TTF would also work, but requires
# bundling a font file.
PDF_UNICODE_REPLACEMENTS = {
    "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4",
    "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9",
    "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
    "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
    "°": " deg", "±": "+/-", "×": "x", "·": ".",
    "≥": ">=", "≤": "<=", "≠": "!=",
    "—": "-", "–": "-", "…": "...",
    "“": '"', "”": '"', "‘": "'", "’": "'",
}


def _pdf_safe(text: str) -> str:
    for src, dst in PDF_UNICODE_REPLACEMENTS.items():
        text = text.replace(src, dst)
    return text


@clinician_required
def report_list(request):
    """All generated reports across cases."""
    reports = (
        Report.objects
        .select_related("patient_case", "patient_case__patient", "patient_case__clinician")
        .all()
    )
    return render(request, "reports/list.html", {"reports": reports})


@clinician_required
def report_preview(request, case_id: int):
    """Draft preview for a case's report. Shows existing Report if present."""
    case = get_object_or_404(
        PatientCase.objects.select_related("patient", "clinician", "clinical_data"),
        pk=case_id,
    )
    report = Report.objects.filter(patient_case=case).first()
    draft = report_builder.build_content(case)
    return render(request, "reports/preview.html", {
        "case": case,
        "report": report,
        "draft": draft,
    })


@clinician_required
@require_POST
def report_generate(request, case_id: int):
    """Persist the report for a case (idempotent — updates existing row)."""
    case = get_object_or_404(PatientCase, pk=case_id)
    if case.status != PatientCase.STATUS_DONE:
        messages.error(request, "Diagnosis must be complete before generating a report.")
        return redirect("cases:detail", case_id=case.id)

    content = report_builder.build_content(case)
    fmt = (request.POST.get("format") or Report.FORMAT_PDF).upper()
    if fmt not in dict(Report.FORMAT_CHOICES):
        fmt = Report.FORMAT_PDF

    report, created = Report.objects.update_or_create(
        patient_case=case,
        defaults={
            "simplified_text": content["simplified_text"],
            "medication_instructions": content["medication_instructions"],
            "format": fmt,
        },
    )
    messages.success(
        request,
        f"Report {'created' if created else 'updated'} for case #{case.id}.",
    )
    return redirect("reports:preview", case_id=case.id)


@clinician_required
def report_export_pdf(request, case_id: int):
    """Stream a styled PDF of the report."""
    case = get_object_or_404(
        PatientCase.objects.select_related("patient", "clinician", "clinical_data"),
        pk=case_id,
    )
    content = _content_for(case)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title=f"Case #{case.id} Report",
    )
    styles = getSampleStyleSheet()
    h1 = styles["Heading1"]
    h2 = styles["Heading2"]
    body = ParagraphStyle("body", parent=styles["BodyText"], leading=14, fontSize=10)

    story = [
        Paragraph(_pdf_safe(f"Pneumonia Severity Report - Case #{case.id}"), h1),
        Spacer(1, 0.4 * cm),
        Paragraph("Case Summary", h2),
    ]
    for para in _pdf_safe(content["simplified_text"]).split("\n\n"):
        story.append(Paragraph(para.replace("\n", "<br/>"), body))
        story.append(Spacer(1, 0.2 * cm))

    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Medication Instructions", h2))
    story.append(Paragraph(_pdf_safe(content["medication_instructions"]).replace("\n", "<br/>"), body))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="case-{case.id}-report.pdf"'
    _touch_report_format(case, Report.FORMAT_PDF, content)
    return response


@clinician_required
def report_export_csv(request, case_id: int):
    """Stream a CSV dump of the report key-value rows."""
    case = get_object_or_404(
        PatientCase.objects.select_related("patient", "clinician", "clinical_data"),
        pk=case_id,
    )
    content = _content_for(case)
    cd = case.clinical_data

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="case-{case.id}-report.csv"'
    writer = csv.writer(response)
    writer.writerow(["field", "value"])
    writer.writerow(["case_id", case.id])
    writer.writerow(["patient_name", case.patient.full_name])
    writer.writerow(["national_id", case.patient.national_id])
    writer.writerow(["clinician", case.clinician.name or case.clinician.email])
    writer.writerow(["created_at", case.created_at.isoformat()])
    writer.writerow(["risk_class", case.risk_class or ""])
    writer.writerow(["severity_score", case.severity_score if case.severity_score is not None else ""])
    writer.writerow(["confidence_score", case.confidence_score if case.confidence_score is not None else ""])
    writer.writerow(["age", cd.age])
    writer.writerow(["spo2", cd.spo2])
    writer.writerow(["blood_pressure", cd.blood_pressure])
    writer.writerow(["respiratory_rate", cd.respiratory_rate])
    writer.writerow(["temperature", cd.temperature])
    writer.writerow(["urea", cd.urea])
    writer.writerow(["ph", cd.ph])
    writer.writerow(["wbc_count", cd.wbc_count])
    writer.writerow(["confusion", "Yes" if cd.confusion else "No"])
    writer.writerow(["simplified_text", content["simplified_text"]])
    writer.writerow(["medication_instructions", content["medication_instructions"]])

    _touch_report_format(case, Report.FORMAT_CSV, content)
    return response


def _content_for(case) -> dict:
    """Pull content from the saved Report if present, otherwise compose it fresh."""
    existing = Report.objects.filter(patient_case=case).first()
    if existing:
        return {
            "simplified_text": existing.simplified_text,
            "medication_instructions": existing.medication_instructions,
        }
    return report_builder.build_content(case)


def _touch_report_format(case, fmt: str, content: dict) -> None:
    """Ensure a Report row exists and remember the last-used export format."""
    Report.objects.update_or_create(
        patient_case=case,
        defaults={
            "simplified_text": content["simplified_text"],
            "medication_instructions": content["medication_instructions"],
            "format": fmt,
        },
    )
