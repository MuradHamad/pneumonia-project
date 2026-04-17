"""Force users with must_change_password=True to reset their password."""
from django.shortcuts import redirect
from django.urls import reverse


class ForcePasswordChangeMiddleware:
    """Redirect authenticated users flagged must_change_password to /change-password."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and getattr(user, "must_change_password", False):
            allowed_paths = {
                reverse("accounts:change_password"),
                reverse("accounts:logout"),
            }
            path = request.path
            is_static = path.startswith(("/static/", "/media/"))
            is_admin = path.startswith("/admin/")
            if path not in allowed_paths and not is_static and not is_admin:
                return redirect("accounts:change_password")
        return self.get_response(request)
