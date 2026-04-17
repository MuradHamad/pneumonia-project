"""Auth forms."""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm

INPUT_CLASSES = (
    "w-full bg-white border border-border rounded-lg px-3 py-2 "
    "focus:border-primary focus:ring-2 focus:ring-primary-light focus:outline-none"
)


class EmailAuthenticationForm(AuthenticationForm):
    """Login form — email as USERNAME_FIELD, Tailwind styling."""

    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": INPUT_CLASSES, "autofocus": True, "autocomplete": "email"}),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": INPUT_CLASSES, "autocomplete": "current-password"}),
    )

    error_messages = {
        "invalid_login": "Invalid email or password.",
        "inactive": "This account is inactive.",
    }


class StyledPasswordChangeForm(PasswordChangeForm):
    """Password change with Tailwind-styled inputs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT_CLASSES
