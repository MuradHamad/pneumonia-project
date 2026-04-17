"""Auth views: login, logout, forced + voluntary password change, settings."""
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .decorators import admin_required
from .forms import EmailAuthenticationForm, StyledPasswordChangeForm


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


@admin_required
def admin_clinicians(request):
    return render(request, "coming_soon.html", {
        "page_title": "Clinicians",
        "description": "Admin: manage clinician accounts. Available in Phase 8.",
    })


@admin_required
def admin_overview(request):
    return render(request, "coming_soon.html", {
        "page_title": "System Overview",
        "description": "Admin: system-wide stats. Available in Phase 8.",
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
