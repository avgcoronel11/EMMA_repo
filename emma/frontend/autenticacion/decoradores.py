from functools import wraps
from urllib.parse import urlencode

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse


def login_requerido(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if settings.DEBUG and not settings.AUTH_ENABLED:
            return view_func(request, *args, **kwargs)
        if request.session.get("access_token"):
            return view_func(request, *args, **kwargs)

        login_url = reverse("login")
        query = urlencode({"next": request.get_full_path()})
        return redirect(f"{login_url}?{query}")

    return wrapper
