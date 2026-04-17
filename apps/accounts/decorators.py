"""Role-based access decorators."""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def admin_required(view_func):
    """Allow only users with role=ADMIN."""

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not getattr(request.user, "is_admin", False):
            raise PermissionDenied("Admin access required.")
        return view_func(request, *args, **kwargs)

    return wrapper


def clinician_required(view_func):
    """Allow users with role=CLINICIAN (admins may also pass)."""

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user
        if not (getattr(user, "is_clinician", False) or getattr(user, "is_admin", False)):
            raise PermissionDenied("Clinician access required.")
        return view_func(request, *args, **kwargs)

    return wrapper
