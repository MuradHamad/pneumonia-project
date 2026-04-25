"""Cases domain: ClinicalData (1-to-1) and PatientCase (core diagnosis entity)."""
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class ClinicalData(models.Model):
    """Vitals/labs snapshot at time of diagnosis.

    Field order matches the trained model's expected input:
    age, bun, hr, sys_bp, rr, temp_fahrenheit, spo2, gcs_total.
    """

    age = models.PositiveIntegerField()
    bun = models.FloatField()
    hr = models.PositiveIntegerField()
    sys_bp = models.PositiveIntegerField()
    rr = models.PositiveIntegerField()
    temp_fahrenheit = models.FloatField()
    spo2 = models.FloatField()
    gcs_total = models.PositiveIntegerField(
        validators=[MinValueValidator(3), MaxValueValidator(15)],
    )

    class Meta:
        db_table = "clinical_data"

    def __str__(self) -> str:
        return f"ClinicalData #{self.pk} (age={self.age})"


class PatientCase(models.Model):
    """One diagnosis session. AI fields stay NULL until fusion model finishes."""

    STATUS_PENDING = "PENDING"
    STATUS_DONE = "DONE"
    STATUS_FAILED = "FAILED"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_DONE, "Done"),
        (STATUS_FAILED, "Failed"),
    ]

    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="cases",
    )
    clinician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cases",
    )
    clinical_data = models.OneToOneField(
        ClinicalData,
        on_delete=models.CASCADE,
        related_name="case",
    )
    xray_image = models.ImageField(upload_to="xrays/")
    heatmap_path = models.CharField(max_length=255, null=True, blank=True)
    diag_probability = models.FloatField(null=True, blank=True)
    severity_probability = models.FloatField(null=True, blank=True)
    has_pneumonia = models.BooleanField(null=True, blank=True)
    is_severe = models.BooleanField(null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "patient_cases"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["patient", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"Case #{self.pk} — {self.patient.full_name}"

    @property
    def xray_image_path(self) -> str:
        return self.xray_image.name if self.xray_image else ""
