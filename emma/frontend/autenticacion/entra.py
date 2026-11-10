from django.conf import settings


class EntraConfigError(RuntimeError):
    pass


def _require_setting(name):
    value = getattr(settings, name, "")
    if not value:
        raise EntraConfigError(f"Falta configurar {name}.")
    return value


def _client_app():
    try:
        import msal
    except ImportError as exc:
        raise EntraConfigError("Falta instalar la dependencia msal.") from exc

    return msal.ConfidentialClientApplication(
        client_id=_require_setting("ENTRA_CLIENT_ID"),
        authority=_require_setting("ENTRA_AUTHORITY"),
        client_credential=_require_setting("ENTRA_CLIENT_SECRET"),
    )


def iniciar_flujo_login():
    return _client_app().initiate_auth_code_flow(
        scopes=settings.ENTRA_SCOPE,
        redirect_uri=_require_setting("ENTRA_REDIRECT_URI"),
    )


def completar_flujo_login(flow, auth_response):
    return _client_app().acquire_token_by_auth_code_flow(flow, auth_response)
