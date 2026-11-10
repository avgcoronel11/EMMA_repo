from django.shortcuts import redirect, render
from django.conf import settings
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_http_methods

from .decoradores import login_requerido
from .entra import EntraConfigError, completar_flujo_login, iniciar_flujo_login


def _next_url(request, default="inicio"):
    next_url = request.GET.get("next") or request.session.pop("auth_next", "")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return reverse(default)


@require_GET
def login(request):
    if settings.DEBUG and not settings.AUTH_ENABLED:
        return redirect("riesgos:list")
    if request.session.get("access_token"):
        return redirect(_next_url(request))

    return render(
        request,
        "autenticacion/login.html",
        {
            "next_url": request.GET.get("next", ""),
            "error": request.GET.get("error", ""),
        },
    )


@require_GET
def iniciar_sesion(request):
    if settings.DEBUG and not settings.AUTH_ENABLED:
        return redirect(_next_url(request, default="riesgos:list"))
    next_url = request.GET.get("next", "")
    if next_url:
        request.session["auth_next"] = next_url

    try:
        flow = iniciar_flujo_login()
    except EntraConfigError as exc:
        return render(
            request,
            "autenticacion/login.html",
            {
                "next_url": next_url,
                "error": str(exc),
            },
            status=500,
        )

    request.session["auth_flow"] = flow
    return redirect(flow["auth_uri"])


@require_GET
def callback(request):
    if "error" in request.GET:
        return render(
            request,
            "autenticacion/login.html",
            {
                "error": request.GET.get("error_description") or request.GET["error"],
                "next_url": request.session.get("auth_next", ""),
            },
            status=401,
        )

    flow = request.session.pop("auth_flow", None)
    if not flow:
        return redirect(f"{reverse('login')}?error=No hay una solicitud de login activa.")

    try:
        result = completar_flujo_login(flow, request.GET.dict())
    except ValueError:
        return redirect(f"{reverse('login')}?error=La respuesta de autenticacion no es valida.")
    except EntraConfigError as exc:
        return render(
            request,
            "autenticacion/login.html",
            {
                "error": str(exc),
                "next_url": request.session.get("auth_next", ""),
            },
            status=500,
        )

    if "access_token" not in result:
        error = result.get("error_description") or result.get("error") or "No fue posible iniciar sesion."
        return render(
            request,
            "autenticacion/login.html",
            {
                "error": error,
                "next_url": request.session.get("auth_next", ""),
            },
            status=401,
        )

    claims = result.get("id_token_claims", {})
    request.session["access_token"] = result["access_token"]
    request.session["usuario"] = {
        "nombre": claims.get("name", ""),
        "correo": claims.get("preferred_username") or claims.get("email", ""),
        "oid": claims.get("oid", ""),
    }
    request.session["token_expires_in"] = result.get("expires_in")

    return redirect(_next_url(request))


@require_GET
@login_requerido
def inicio(request):
    return render(
        request,
        "autenticacion/inicio.html",
        {
            "usuario": request.session.get("usuario", {}),
        },
    )


@require_http_methods(["GET", "POST"])
def cerrar_sesion(request):
    request.session.flush()
    return redirect("login")
