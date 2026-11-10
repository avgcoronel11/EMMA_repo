"""Contract-compliant API exceptions and error handling."""

import logging

from django.http import Http404
from django.db.models.deletion import ProtectedError
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    NotFound,
    ParseError,
    PermissionDenied,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.views import set_rollback


logger = logging.getLogger(__name__)


class ReglaNegocioError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "La operacion viola una regla de negocio."
    default_code = "regla_negocio"


ERROR_DEFINITIONS = {
    status.HTTP_400_BAD_REQUEST: ("VALIDACION", "Hay errores en los datos enviados."),
    status.HTTP_401_UNAUTHORIZED: ("NO_AUTENTICADO", "Sin sesion o token."),
    status.HTTP_403_FORBIDDEN: ("SIN_PERMISO", "El rol no puede realizar la accion."),
    status.HTTP_404_NOT_FOUND: ("NO_ENCONTRADO", "El registro no existe."),
    status.HTTP_409_CONFLICT: ("REGLA_NEGOCIO", "La operacion viola una regla de negocio."),
    status.HTTP_500_INTERNAL_SERVER_ERROR: ("ERROR_INTERNO", "Ocurrio un error inesperado."),
}


def api_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    if response is None:
        if isinstance(exc, Http404):
            status_code = status.HTTP_404_NOT_FOUND
            detalles = {"detail": [str(exc)]}
            _log_expected_error(exc, context, status_code)
        elif isinstance(exc, ProtectedError):
            set_rollback()
            status_code = status.HTTP_409_CONFLICT
            detalles = {"detail": ["El registro no se puede eliminar porque tiene informacion relacionada."]}
            _log_expected_error(exc, context, status_code)
        else:
            set_rollback()
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            detalles = {}
            _log_unexpected_error(exc, context)
        return Response(_error_payload(status_code, detalles), status=status_code)

    status_code = response.status_code
    detalles = _detalles_from_response(response.data)
    response.data = _error_payload(status_code, detalles, exc=exc)
    _log_expected_error(exc, context, status_code)
    return response


def _error_payload(status_code, detalles, exc=None):
    codigo, mensaje = ERROR_DEFINITIONS.get(
        status_code,
        ERROR_DEFINITIONS[status.HTTP_500_INTERNAL_SERVER_ERROR],
    )

    if isinstance(exc, (ValidationError, ParseError)):
        codigo, mensaje = ERROR_DEFINITIONS[status.HTTP_400_BAD_REQUEST]
    elif isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
        codigo, mensaje = ERROR_DEFINITIONS[status.HTTP_401_UNAUTHORIZED]
    elif isinstance(exc, PermissionDenied):
        codigo, mensaje = ERROR_DEFINITIONS[status.HTTP_403_FORBIDDEN]
    elif isinstance(exc, (NotFound, Http404)):
        codigo, mensaje = ERROR_DEFINITIONS[status.HTTP_404_NOT_FOUND]
    elif isinstance(exc, ReglaNegocioError):
        codigo, mensaje = ERROR_DEFINITIONS[status.HTTP_409_CONFLICT]

    return {
        "error": {
            "codigo": codigo,
            "mensaje": mensaje,
            "detalles": detalles or {},
        }
    }


def _log_expected_error(exc, context, status_code):
    request = context.get("request") if context else None
    logger.warning(
        "API error handled status=%s method=%s path=%s exception=%s",
        status_code,
        getattr(request, "method", "-"),
        _safe_path(request),
        exc.__class__.__name__,
    )


def _log_unexpected_error(exc, context):
    request = context.get("request") if context else None
    logger.exception(
        "Unexpected API error method=%s path=%s exception=%s",
        getattr(request, "method", "-"),
        _safe_path(request),
        exc.__class__.__name__,
    )


def _safe_path(request):
    if request is None:
        return "-"
    return getattr(request, "path", "-")


def _detalles_from_response(data):
    if isinstance(data, dict):
        return {key: _as_list(value) for key, value in data.items()}
    if isinstance(data, list):
        return {"non_field_errors": data}
    if data in ("", None):
        return {}
    return {"detail": [str(data)]}


def _as_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return value
    return [str(value)]
