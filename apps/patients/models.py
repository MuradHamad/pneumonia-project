"""Patient model — demographics + registering clinician."""
from datetime import date

from django.conf import settings
from django.db import models


class Patient(models.Model):
    """A patient registered in the system. Owns many PatientCases."""

    GENDER_MALE = "MALE"
    GENDER_FEMALE = "FEMALE"
    GENDER_CHOICES = [
        (GENDER_MALE, "Male"),
        (GENDER_FEMALE, "Female"),
    ]

    national_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=150)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="registered_patients",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "patients"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["full_name"]),
            models.Index(fields=["national_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.full_name} ({self.national_id})"

    @property
    def age(self) -> int:
        today = date.today()
        dob = self.date_of_birth
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
