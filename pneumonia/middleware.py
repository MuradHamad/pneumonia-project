import logging
import traceback

from django.conf import settings
from django.http import HttpResponseForbidden
from django.template import loader
from django.views import defaults

logger = logging.getLogger(__name__)


class GlobalExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if settings.DEBUG:
            return None

        logger.exception(
            "Unhandled exception during request %s %s", request.method, request.path
        )

        try:
            template = loader.get_template("500.html")
            context = {}
            response = template.render(context, request)
            return HttpResponseForbidden(response) if response else None
        except Exception:
            return defaults.server_error(request)
