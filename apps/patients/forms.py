"""Patient registration form."""
from django import forms

from .models import Patient

INPUT_CLASSES = (
    "w-full bg-white border border-border rounded-lg px-3 py-2 "
    "focus:border-primary focus:ring-2 focus:ring-primary-light focus:outline-none"
)


class PatientForm(forms.ModelForm):
    """ModelForm for registering/editing a patient. Uniqueness on national_id is enforced by the DB."""

    class Meta:
        model = Patient
        fields = ["national_id", "full_name", "date_of_birth", "gender", "phone_number"]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "gender": forms.RadioSelect,
            "phone_number": forms.TextInput(attrs={"placeholder": "Optional"}),
        }
        labels = {
            "national_id": "National ID",
            "full_name": "Full Name",
            "date_of_birth": "Date of Birth",
            "phone_number": "Phone Number",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == "gender":
                continue
            field.widget.attrs.setdefault("class", INPUT_CLASSES)
        self.fields["phone_number"].required = False

    def clean_national_id(self) -> str:
        nid = self.cleaned_data["national_id"].strip()
        if not nid:
            raise forms.ValidationError("National ID is required.")
        return nid
