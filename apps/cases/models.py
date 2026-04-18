"""Cases domain: ClinicalData (1-to-1) and PatientCase (core diagnosis entity)."""
from django.conf import settings
from django.db import models


class ClinicalData(models.Model):
    """Vitals/labs snapshot at time of diagnosis. Composed inside a PatientCase."""

    age = models.PositiveIntegerField()
    spo2 = models.FloatField()
    blood_pressure = models.CharField(max_length=15)
    respiratory_rate = models.PositiveIntegerField()
    temperature = models.FloatField()
    urea = models.FloatField()
    ph = models.FloatField()
    wbc_count = models.FloatField()
    confusion = models.BooleanField(default=False)

    class Meta:
        db_table = "clinical_data"

    def __str__(self) -> str:
        return f"ClinicalData #{self.pk} (age={self.age})"


class PatientCase(models.Model):
    """One diagnosis session. AI fields stay NULL until fusion model finishes."""

    RISK_I = "I"
    RISK_II = "II"
    RISK_III = "III"
    RISK_IV = "IV"
    RISK_V = "V"
    RISK_CLASS_CHOICES = [
        (RISK_I, "Class I"),
        (RISK_II, "Class II"),
        (RISK_III, "Class III"),
        (RISK_IV, "Class IV"),
        (RISK_V, "Class V"),
    ]

    STATUS_PENDING = "PENDING"
    STATUS_DONE = "DONE"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_DONE, "Done"),
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
    severity_score = models.FloatField(null=True, blank=True)
    risk_class = models.CharField(
        max_length=3,
        choices=RISK_CLASS_CHOICES,
        null=True,
        blank=True,
    )
    heatmap_path = models.CharField(max_length=255, null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
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
