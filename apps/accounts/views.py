"""Auth views: login, logout, forced + voluntary password change, settings, admin panel."""
import secrets
import string
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone

from apps.cases.models import PatientCase
from apps.patients.models import Patient
from apps.reports.models import Report

from .decorators import admin_required
from .forms import ClinicianCreateForm, EmailAuthenticationForm, StyledPasswordChangeForm
from .models import User


class EmailLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        if getattr(user, "must_change_password", False):
            return reverse_lazy("accounts:change_password")
        return super().get_success_url()


class AppLogoutView(LogoutView):
    next_page = reverse_lazy("accounts:login")


@login_required
def change_password_view(request):
    """Forced password change. Clears must_change_password on success."""
    if request.method == "POST":
        form = StyledPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            if user.must_change_password:
                user.must_change_password = False
                user.save(update_fields=["must_change_password"])
            messages.success(request, "Password updated.")
            return redirect("dashboard")
    else:
        form = StyledPasswordChangeForm(request.user)
    return render(request, "accounts/change_password.html", {"form": form})


TEMP_PASSWORD_ALPHABET = string.ascii_letters + string.digits


def _generate_temp_password(length: int = 12) -> str:
    """Cryptographically-random temp password. User must change on first login."""
    return "".join(secrets.choice(TEMP_PASSWORD_ALPHABET) for _ in range(length))


@admin_required
def admin_clinicians(request):
    """List all clinicians."""
    clinicians = (
        User.objects
        .filter(role=User.ROLE_CLINICIAN)
        .order_by("-created_at")
    )
    return render(request, "accounts/admin_clinicians.html", {
        "clinicians": clinicians,
    })


@admin_required
def admin_clinician_new(request):
    """Create a clinician account: temp password generated, email dispatched."""
    if request.method == "POST":
        form = ClinicianCreateForm(request.POST)
        if form.is_valid():
            temp_password = _generate_temp_password()
            clinician = form.save(commit=False)
            clinician.role = User.ROLE_CLINICIAN
            clinician.must_change_password = True
            clinician.set_password(temp_password)
            clinician.save()

            send_mail(
                subject="Your PneuDx clinician account",
                message=(
                    f"Hello {clinician.name},\n\n"
                    f"An admin has created a PneuDx clinician account for you.\n\n"
                    f"Email: {clinician.email}\n"
                    f"Temporary password: {temp_password}\n\n"
                    f"You will be prompted to change this password on first login.\n"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[clinician.email],
                fail_silently=False,
            )
            messages.success(
                request,
                f"Clinician {clinician.email} created. Temp credentials emailed to the console backend.",
            )
            return redirect("accounts:admin_clinicians")
    else:
        form = ClinicianCreateForm()

    return render(request, "accounts/admin_clinician_new.html", {"form": form})


@admin_required
def admin_overview(request):
    """System-wide stats + recent activity."""
    week_ago = timezone.now() - timedelta(days=7)

    stats = {
        "patients": Patient.objects.count(),
        "clinicians": User.objects.filter(role=User.ROLE_CLINICIAN).count(),
        "cases": PatientCase.objects.count(),
        "cases_this_week": PatientCase.objects.filter(created_at__gte=week_ago).count(),
        "pending": PatientCase.objects.filter(status=PatientCase.STATUS_PENDING).count(),
        "done": PatientCase.objects.filter(status=PatientCase.STATUS_DONE).count(),
        "reports": Report.objects.count(),
    }
    recent_cases = (
        PatientCase.objects
        .select_related("patient", "clinician")
        .order_by("-created_at")[:5]
    )
    recent_clinicians = (
        User.objects
        .filter(role=User.ROLE_CLINICIAN)
        .order_by("-created_at")[:5]
    )
    return render(request, "accounts/admin_overview.html", {
        "stats": stats,
        "recent_cases": recent_cases,
        "recent_clinicians": recent_clinicians,
    })


@login_required
def settings_view(request):
    """Profile view + voluntary password change."""
    if request.method == "POST":
        form = StyledPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Password updated.")
            return redirect("accounts:settings")
    else:
        form = StyledPasswordChangeForm(request.user)
    return render(request, "accounts/settings.html", {"form": form})
