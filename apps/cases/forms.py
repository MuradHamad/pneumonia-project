"""Forms for the 3-step case creation wizard."""

from django import forms
from django.core.exceptions import ValidationError

from .models import ClinicalData

INPUT_CLASSES = (
    "w-full bg-white border border-border rounded-lg px-3 py-2 "
    "focus:border-primary focus:ring-2 focus:ring-primary-light focus:outline-none"
)

ALLOWED_XRAY_CONTENT_TYPES = {"image/jpeg", "image/png"}
ALLOWED_XRAY_EXTENSIONS = (".jpg", ".jpeg", ".png")
MAX_XRAY_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

# Model fields that map 1-to-1 with ClinicalData columns.
CLINICAL_MODEL_FIELDS = frozenset(
    [
        "age",
        "bun",
        "hr",
        "sys_bp",
        "rr",
        "temp_fahrenheit",
        "spo2",
        "gcs_total",
    ]
)


class XrayUploadForm(forms.Form):
    """Step 1: upload an X-ray image. Validates content-type, extension, size."""

    xray_image = forms.ImageField(
        label="Chest X-ray",
        widget=forms.ClearableFileInput(
            attrs={
                "class": INPUT_CLASSES,
                "accept": ",".join(ALLOWED_XRAY_EXTENSIONS),
            }
        ),
    )

    def clean_xray_image(self):
        f = self.cleaned_data["xray_image"]
        if f.size > MAX_XRAY_SIZE_BYTES:
            raise ValidationError("X-ray file exceeds 10 MB limit.")
        content_type = getattr(f, "content_type", "") or ""
        name = (f.name or "").lower()
        if content_type and content_type not in ALLOWED_XRAY_CONTENT_TYPES:
            raise ValidationError("Unsupported file type. Use JPEG, PNG.")
        if not name.endswith(ALLOWED_XRAY_EXTENSIONS):
            raise ValidationError("Unsupported extension. Use .jpg, .jpeg, or .png.")
        return f


class ClinicalDataForm(forms.ModelForm):
    """Step 2: 8 clinical fields in display order + temperature unit toggle.

    Display order (per ui-design.md 3.8):
        Row 1: age, spo2
        Row 2: hr, rr
        Row 3: sys_bp, temp_fahrenheit (with unit toggle)
        Row 4: bun, gcs_total

    temp_unit is a form-only field — not stored in ClinicalData. The clean()
    method converts the entered temperature to Fahrenheit before saving.
    """

    TEMP_FAHRENHEIT = "F"
    TEMP_CELSIUS = "C"
    TEMP_UNIT_CHOICES = [(TEMP_FAHRENHEIT, "°F"), (TEMP_CELSIUS, "°C")]

    temp_unit = forms.ChoiceField(
        choices=TEMP_UNIT_CHOICES,
        initial=TEMP_FAHRENHEIT,
        required=False,
        label="Temperature unit",
    )

    class Meta:
        model = ClinicalData
        fields = [
            "age",
            "spo2",
            "hr",
            "rr",
            "sys_bp",
            "temp_fahrenheit",
            "bun",
            "gcs_total",
        ]
        labels = {
            "age": "Age (years)",
            "spo2": "SpO₂ (%)",
            "hr": "Heart Rate (bpm)",
            "rr": "Respiratory Rate (breaths/min)",
            "sys_bp": "Systolic Blood Pressure (mmHg)",
            "temp_fahrenheit": "Temperature",
            "bun": "BUN — Blood Urea Nitrogen (mg/dL)",
            "gcs_total": "GCS Total — Glasgow Coma Scale",
        }
        help_texts = {
            "age": "Patient age in years",
            "spo2": "Normal: 95–100%",
            "hr": "Normal: 60–100 bpm",
            "rr": "Normal: 12–20 breaths/min",
            "sys_bp": "Normal: 90–120 mmHg",
            "temp_fahrenheit": "Normal: 97–99°F (36.1–37.2°C)",
            "bun": "Normal: 7–20 mg/dL",
            "gcs_total": "15 = normal, 3 = deep coma",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == "temp_unit":
                continue
            field.widget.attrs.setdefault("class", INPUT_CLASSES)

    def clean_age(self) -> int:
        v = self.cleaned_data["age"]
        if not (0 <= v <= 130):
            raise ValidationError("Age must be between 0 and 130.")
        return v

    def clean_spo2(self) -> float:
        v = self.cleaned_data["spo2"]
        if not (0 <= v <= 100):
            raise ValidationError("SpO₂ must be between 0 and 100%.")
        return v

    def clean_hr(self) -> int:
        v = self.cleaned_data["hr"]
        if not (20 <= v <= 300):
            raise ValidationError("Heart rate must be between 20 and 300 bpm.")
        return v

    def clean_rr(self) -> int:
        v = self.cleaned_data["rr"]
        if not (4 <= v <= 80):
            raise ValidationError(
                "Respiratory rate must be between 4 and 80 breaths/min."
            )
        return v

    def clean_sys_bp(self) -> int:
        v = self.cleaned_data["sys_bp"]
        if not (50 <= v <= 300):
            raise ValidationError("Systolic BP must be between 50 and 300 mmHg.")
        return v

    def clean_bun(self) -> float:
        v = self.cleaned_data["bun"]
        if not (0 <= v <= 300):
            raise ValidationError("BUN must be between 0 and 300 mg/dL.")
        return v

    def clean_gcs_total(self) -> int:
        v = self.cleaned_data["gcs_total"]
        if not (3 <= v <= 15):
            raise ValidationError("GCS Total must be between 3 and 15.")
        return v

    def clean(self):
        cleaned = super().clean()
        temp = cleaned.get("temp_fahrenheit")
        unit = cleaned.get("temp_unit") or self.TEMP_FAHRENHEIT
        if temp is not None:
            if unit == self.TEMP_CELSIUS:
                cleaned["temp_fahrenheit"] = round(temp * 9 / 5 + 32, 2)
            final_f = cleaned["temp_fahrenheit"]
            if not (80.0 <= final_f <= 115.0):
                self.add_error(
                    "temp_fahrenheit",
                    "Temperature out of plausible range (80–115°F / 27–46°C).",
                )
        return cleaned
