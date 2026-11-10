from urllib.parse import urlsplit, urlunsplit

from django.conf import settings
from django.http import HttpResponseRedirect


class CanonicalLocalHostMiddleware:
    """Unifica localhost y 127.0.0.1 para no perder cookies de sesion."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        aliases = set(getattr(settings, "LOCAL_HOST_ALIASES", []))
        canonical_host = getattr(settings, "LOCAL_CANONICAL_HOST", "")
        current_host = request.get_host()

        if canonical_host and current_host in aliases:
            scheme = "https" if request.is_secure() else "http"
            target = urlunsplit(
                (
                    scheme,
                    canonical_host,
                    request.path,
                    request.META.get("QUERY_STRING", ""),
                    "",
                )
            )
            return HttpResponseRedirect(target)

        return self.get_response(request)
