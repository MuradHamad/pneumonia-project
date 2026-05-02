"""Reports views — preview, generate, export (PDF/CSV), list."""

import csv
from io import BytesIO
from pathlib import Path

from django.conf import settings

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image as RLImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
)

from apps.accounts.decorators import clinician_required
from apps.cases.models import PatientCase
from services import report_builder

from .models import Report


PDF_UNICODE_REPLACEMENTS = {
    "₀": "0",
    "₁": "1",
    "₂": "2",
    "₃": "3",
    "₄": "4",
    "₅": "5",
    "₆": "6",
    "₇": "7",
    "₈": "8",
    "₉": "9",
    "⁰": "0",
    "¹": "1",
    "²": "2",
    "³": "3",
    "⁴": "4",
    "⁵": "5",
    "⁶": "6",
    "⁷": "7",
    "⁸": "8",
    "⁹": "9",
    "°": " deg",
    "±": "+/-",
    "×": "x",
    "·": ".",
    "≥": ">=",
    "≤": "<=",
    "≠": "!=",
    "—": "-",
    "–": "-",
    "…": "...",
    "“": '"',
    "”": '"',
    "‘": "'",
    "’": "'",
}


def _pdf_safe(text: str) -> str:
    for src, dst in PDF_UNICODE_REPLACEMENTS.items():
        text = text.replace(src, dst)
    return text


def _image_elem(path: str, width: float, height: float):
    try:
        return RLImage(str(path), width=width, height=height)
    except Exception:
        return None


@clinician_required
def report_list(request):
    reports = Report.objects.select_related(
        "patient_case", "patient_case__patient", "patient_case__clinician"
    ).all()
    return render(request, "reports/list.html", {"reports": reports})


@clinician_required
def report_preview(request, case_id: int):
    case = get_object_or_404(
        PatientCase.objects.select_related("patient", "clinician", "clinical_data"),
        pk=case_id,
    )
    report = Report.objects.filter(patient_case=case).first()
    draft = report_builder.build_content(case)
    return render(
        request,
        "reports/preview.html",
        {
            "case": case,
            "report": report,
            "draft": draft,
        },
    )


@clinician_required
@require_POST
def report_generate(request, case_id: int):
    case = get_object_or_404(PatientCase, pk=case_id)
    if case.status != PatientCase.STATUS_DONE:
        messages.error(
            request, "Diagnosis must be complete before generating a summary."
        )
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
        f"Summary {'created' if created else 'updated'} for case #{case.id}.",
    )
    return redirect("reports:preview", case_id=case.id)


@clinician_required
def report_export_pdf(request, case_id: int):
    case = get_object_or_404(
        PatientCase.objects.select_related("patient", "clinician", "clinical_data"),
        pk=case_id,
    )
    content = _content_for(case)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"Case #{case.id} Summary",
    )
    styles = getSampleStyleSheet()
    h1 = styles["Heading1"]
    h2 = styles["Heading2"]
    body = ParagraphStyle("body", parent=styles["BodyText"], leading=14, fontSize=10)

    story = [
        Paragraph(_pdf_safe(f"Pneumonia Assessment Summary — Case #{case.id}"), h1),
        Spacer(1, 0.4 * cm),
        Paragraph("Clinical Summary", h2),
    ]
    for para in _pdf_safe(content["simplified_text"]).split("\n\n"):
        story.append(Paragraph(para.replace("\n", "<br/>"), body))
        story.append(Spacer(1, 0.2 * cm))

    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Medication Instructions", h2))
    story.append(
        Paragraph(
            _pdf_safe(content["medication_instructions"]).replace("\n", "<br/>"), body
        )
    )

    img_top_margin = Spacer(1, 0.4 * cm)
    story.append(img_top_margin)

    xray_path = case.xray_image.path if case.xray_image else None
    heatmap_rel = case.heatmap_path
    heatmap_path = str(settings.MEDIA_ROOT / heatmap_rel) if heatmap_rel else None

    has_xray = xray_path and Path(xray_path).exists()
    has_heatmap = heatmap_path and Path(heatmap_path).exists()

    if has_xray and has_heatmap:
        img_w = 8 * cm
        img_h = 8 * cm
        xray_img = _image_elem(xray_path, img_w, img_h)
        heatmap_img = _image_elem(heatmap_path, img_w, img_h)
        if xray_img and heatmap_img:
            story.append(Paragraph("X-Ray Images", h2))
            story.append(Table([[xray_img, heatmap_img]], colWidths=[9 * cm, 9 * cm]))
            story.append(
                Paragraph(
                    "<i>Left: Original X-Ray | Right: AI Focus (Grad-CAM heatmap — red/yellow regions "
                    "most influential to diagnosis)</i>",
                    body,
                )
            )
        elif xray_img:
            story.append(Paragraph("X-Ray Image", h2))
            story.append(xray_img)
        elif heatmap_img:
            story.append(Paragraph("AI Focus (Heatmap)", h2))
            story.append(heatmap_img)
    elif has_xray:
        img_w = 10 * cm
        img_h = 10 * cm
        xray_img = _image_elem(xray_path, img_w, img_h)
        if xray_img:
            story.append(Paragraph("X-Ray Image", h2))
            story.append(xray_img)
    elif has_heatmap:
        img_w = 10 * cm
        img_h = 10 * cm
        heatmap_img = _image_elem(heatmap_path, img_w, img_h)
        if heatmap_img:
            story.append(Paragraph("AI Focus (Heatmap)", h2))
            story.append(heatmap_img)

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="case-{case.id}-summary.pdf"'
    )
    _touch_report_format(case, Report.FORMAT_PDF, content)
    return response


@clinician_required
def report_export_csv(request, case_id: int):
    case = get_object_or_404(
        PatientCase.objects.select_related("patient", "clinician", "clinical_data"),
        pk=case_id,
    )
    content = _content_for(case)
    cd = case.clinical_data

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="case-{case.id}-summary.csv"'
    )
    writer = csv.writer(response)
    writer.writerow(["field", "value"])
    writer.writerow(["case_id", case.id])
    writer.writerow(["patient_name", case.patient.full_name])
    writer.writerow(["national_id", case.patient.national_id])
    writer.writerow(["clinician", case.clinician.name or case.clinician.email])
    writer.writerow(["created_at", case.created_at.isoformat()])
    writer.writerow(["status", case.status])
    writer.writerow(["has_pneumonia", case.has_pneumonia])
    writer.writerow(["is_severe", case.is_severe])
    writer.writerow(
        [
            "diag_probability",
            case.diag_probability if case.diag_probability is not None else "",
        ]
    )
    writer.writerow(
        [
            "severity_probability",
            case.severity_probability if case.severity_probability is not None else "",
        ]
    )
    writer.writerow(["age", cd.age])
    writer.writerow(["bun", cd.bun])
    writer.writerow(["hr", cd.hr])
    writer.writerow(["sys_bp", cd.sys_bp])
    writer.writerow(["rr", cd.rr])
    writer.writerow(["temp_fahrenheit", cd.temp_fahrenheit])
    writer.writerow(["spo2", cd.spo2])
    writer.writerow(["gcs_total", cd.gcs_total])
    writer.writerow(["simplified_text", content["simplified_text"]])
    writer.writerow(["medication_instructions", content["medication_instructions"]])

    _touch_report_format(case, Report.FORMAT_CSV, content)
    return response


def _content_for(case) -> dict:
    existing = Report.objects.filter(patient_case=case).first()
    if existing:
        return {
            "simplified_text": existing.simplified_text,
            "medication_instructions": existing.medication_instructions,
        }
    return report_builder.build_content(case)


def _touch_report_format(case, fmt: str, content: dict) -> None:
    Report.objects.update_or_create(
        patient_case=case,
        defaults={
            "simplified_text": content["simplified_text"],
            "medication_instructions": content["medication_instructions"],
            "format": fmt,
        },
    )
