"""Report model — generated on demand per case."""
from django.db import models


class Report(models.Model):
    """Clinical report for a single case. At most one per case (UNIQUE FK)."""

    FORMAT_PDF = "PDF"
    FORMAT_CSV = "CSV"
    FORMAT_CHOICES = [
        (FORMAT_PDF, "PDF"),
        (FORMAT_CSV, "CSV"),
    ]

    patient_case = models.OneToOneField(
        "cases.PatientCase",
        on_delete=models.CASCADE,
        related_name="report",
    )
    simplified_text = models.TextField()
    medication_instructions = models.TextField()
    format = models.CharField(max_length=3, choices=FORMAT_CHOICES, default=FORMAT_PDF)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reports"
        ordering = ["-generated_at"]

    def __str__(self) -> str:
        return f"Report for case #{self.patient_case_id} ({self.format})"
