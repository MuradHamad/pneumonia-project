"""Root URL configuration."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.defaults import page_not_found as _django_404

from .views import dashboard, page_not_found, server_error

handler404 = "pneumonia.views.page_not_found"
handler500 = "pneumonia.views.server_error"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("patients/", include("apps.patients.urls")),
    path("cases/", include("apps.cases.urls")),
    path("chat/", include("apps.chat.urls")),
    path("reports/", include("apps.reports.urls")),
    path("", dashboard, name="dashboard"),
    # Catch-all so the custom 404 renders in DEBUG mode too
    re_path(r"^.*$", lambda req, *a, **kw: page_not_found(req, None)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / "static")
