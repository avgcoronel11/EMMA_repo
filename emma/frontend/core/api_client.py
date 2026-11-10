import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings

from .errors import ApiClientError


ERROR_MESSAGES = {
    400: ("VALIDACION", "Hay errores en los datos enviados."),
    401: ("NO_AUTENTICADO", "Sin sesion o token."),
    403: ("SIN_PERMISO", "El rol no puede realizar la accion."),
    404: ("NO_ENCONTRADO", "El registro no existe."),
    409: ("REGLA_NEGOCIO", "La operacion viola una regla de negocio."),
    500: ("ERROR_INTERNO", "Ocurrio un error inesperado."),
}


def _build_url(path, params=None):
    base_url = settings.API_BASE_URL.rstrip("/")
    clean_path = path.strip("/")
    url = f"{base_url}/{clean_path}/"

    if params:
        filtered_params = {key: value for key, value in params.items() if value not in ("", None)}
        if filtered_params:
            url = f"{url}?{urlencode(filtered_params, doseq=True)}"

    return url


def request_json(method, path, data=None, params=None, headers=None, token=None):
    body = None
    request_headers = {"Accept": "application/json"}
    request_headers.update(headers or {})
    bearer_token = token or getattr(settings, "API_BEARER_TOKEN", "")
    if bearer_token and "Authorization" not in request_headers:
        request_headers["Authorization"] = f"Bearer {bearer_token}"

    if data is not None:
        body = json.dumps(data).encode("utf-8")
        request_headers["Content-Type"] = "application/json"

    request = Request(
        _build_url(path, params=params),
        data=body,
        headers=request_headers,
        method=method.upper(),
    )

    try:
        with urlopen(request, timeout=settings.API_TIMEOUT_SECONDS) as response:
            payload = response.read().decode("utf-8")
            return json.loads(payload) if payload else None
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        payload = _normalize_error_payload(exc.code, detail)
        raise ApiClientError(status_code=exc.code, detail=detail, payload=payload) from exc
    except URLError as exc:
        payload = _normalize_error_payload(None, str(exc.reason))
        raise ApiClientError(status_code=None, detail=str(exc.reason), payload=payload) from exc
    except TimeoutError as exc:
        detail = "Tiempo de espera agotado"
        payload = _normalize_error_payload(None, detail)
        raise ApiClientError(status_code=None, detail=detail, payload=payload) from exc
    except json.JSONDecodeError as exc:
        detail = "La API devolvio una respuesta invalida"
        payload = _normalize_error_payload(None, detail)
        raise ApiClientError(status_code=None, detail=detail, payload=payload) from exc


def get_json(path, params=None, headers=None, token=None):
    return request_json("GET", path, params=params, headers=headers, token=token)


def post_json(path, data=None, headers=None, token=None):
    return request_json("POST", path, data=data, headers=headers, token=token)


def patch_json(path, data=None, headers=None, token=None):
    return request_json("PATCH", path, data=data, headers=headers, token=token)


def delete_json(path, data=None, headers=None, token=None):
    return request_json("DELETE", path, data=data, headers=headers, token=token)


def _normalize_error_payload(status_code, raw_detail):
    parsed = _parse_json(raw_detail)
    if isinstance(parsed, dict) and isinstance(parsed.get("error"), dict):
        return parsed

    codigo, mensaje = ERROR_MESSAGES.get(status_code, ("ERROR_INTERNO", "No fue posible comunicarse con la API."))
    return {
        "error": {
            "codigo": codigo,
            "mensaje": mensaje,
            "detalles": _extract_details(parsed, raw_detail),
        }
    }


def _parse_json(raw_detail):
    try:
        return json.loads(raw_detail)
    except (TypeError, json.JSONDecodeError):
        return None


def _extract_details(parsed, raw_detail):
    if isinstance(parsed, dict):
        return parsed
    if isinstance(parsed, list):
        return {"non_field_errors": parsed}
    if raw_detail:
        return {"detail": [raw_detail]}
    return {}
