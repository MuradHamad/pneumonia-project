"""Forms for the 3-step case creation wizard."""
from django import forms
from django.core.exceptions import ValidationError

from .models import ClinicalData

INPUT_CLASSES = (
    "w-full bg-white border border-border rounded-lg px-3 py-2 "
    "focus:border-primary focus:ring-2 focus:ring-primary-light focus:outline-none"
)

ALLOWED_XRAY_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_XRAY_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
MAX_XRAY_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class XrayUploadForm(forms.Form):
    """Step 1: upload an X-ray image. Validates content-type, extension, size."""

    xray_image = forms.ImageField(
        label="Chest X-ray",
        widget=forms.ClearableFileInput(attrs={
            "class": INPUT_CLASSES,
            "accept": ",".join(ALLOWED_XRAY_EXTENSIONS),
        }),
    )

    def clean_xray_image(self):
        f = self.cleaned_data["xray_image"]
        if f.size > MAX_XRAY_SIZE_BYTES:
            raise ValidationError("X-ray file exceeds 10 MB limit.")
        content_type = getattr(f, "content_type", "") or ""
        name = (f.name or "").lower()
        if content_type and content_type not in ALLOWED_XRAY_CONTENT_TYPES:
            raise ValidationError("Unsupported file type. Use JPEG, PNG, or WEBP.")
        if not name.endswith(ALLOWED_XRAY_EXTENSIONS):
            raise ValidationError("Unsupported extension. Use .jpg, .jpeg, .png, or .webp.")
        return f


class ClinicalDataForm(forms.ModelForm):
    """Step 2: 9 clinical fields + confusion toggle."""

    class Meta:
        model = ClinicalData
        fields = [
            "age",
            "spo2",
            "blood_pressure",
            "respiratory_rate",
            "temperature",
            "urea",
            "ph",
            "wbc_count",
            "confusion",
        ]
        widgets = {
            "blood_pressure": forms.TextInput(attrs={"placeholder": "e.g. 120/80"}),
            "confusion": forms.CheckboxInput(),
        }
        labels = {
            "spo2": "SpO₂ (%)",
            "blood_pressure": "Blood Pressure (mmHg)",
            "respiratory_rate": "Respiratory Rate (breaths/min)",
            "temperature": "Temperature (°C)",
            "urea": "Urea (mmol/L)",
            "ph": "Blood pH",
            "wbc_count": "WBC Count (×10⁹/L)",
            "confusion": "Confusion present (CURB-65)",
        }
        help_texts = {
            "age": "Age at time of diagnosis.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault(
                    "class",
                    "w-4 h-4 text-primary border-border rounded focus:ring-primary-light",
                )
                continue
            field.widget.attrs.setdefault("class", INPUT_CLASSES)

    def clean_spo2(self) -> float:
        v = self.cleaned_data["spo2"]
        if not (0 <= v <= 100):
            raise ValidationError("SpO₂ must be between 0 and 100.")
        return v

    def clean_temperature(self) -> float:
        v = self.cleaned_data["temperature"]
        if not (25 <= v <= 45):
            raise ValidationError("Temperature must be between 25°C and 45°C.")
        return v

    def clean_ph(self) -> float:
        v = self.cleaned_data["ph"]
        if not (6.5 <= v <= 8.0):
            raise ValidationError("Blood pH must be between 6.5 and 8.0.")
        return v

    def clean_respiratory_rate(self) -> int:
        v = self.cleaned_data["respiratory_rate"]
        if v <= 0 or v > 80:
            raise ValidationError("Respiratory rate must be between 1 and 80.")
        return v

    def clean_age(self) -> int:
        v = self.cleaned_data["age"]
        if v < 0 or v > 130:
            raise ValidationError("Age must be between 0 and 130.")
        return v
