"""Authentication helpers for local development only."""

from django.conf import settings
from rest_framework.authentication import BaseAuthentication


class _LocalDevelopmentUser:
    """Minimal authenticated principal used only while local auth is disabled."""

    is_authenticated = True
    is_anonymous = False
    username = "desarrollo-local"
    email = ""

    def __str__(self):
        return self.username


class LocalDevelopmentAuthentication(BaseAuthentication):
    """Authenticates local DEBUG requests when ``AUTH_ENABLED`` is false.

    It never bypasses authentication outside DEBUG, even if the environment
    variable is set accidentally.
    """

    def authenticate(self, request):
        if not settings.DEBUG or getattr(settings, "AUTH_ENABLED", True):
            return None
        return _LocalDevelopmentUser(), None
