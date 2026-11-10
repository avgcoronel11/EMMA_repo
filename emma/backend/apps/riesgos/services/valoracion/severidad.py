"""Severity valuation rules."""

from rest_framework.exceptions import ValidationError

from backend.apps.catalogos.models import CfgSeveridad
from backend.apps.riesgos.services.valoracion.utils import normalizar_concatenado, reglas_vigentes


def calcular_severidad(*, probabilidad_etiqueta, impacto_etiqueta, version=None, fecha=None):
    concatenado = normalizar_concatenado(probabilidad_etiqueta, impacto_etiqueta)
    if not concatenado:
        raise ValidationError("No fue posible calcular el concatenado de severidad.")

    regla = (
        reglas_vigentes(CfgSeveridad, version=version, fecha=fecha)
        .filter(concatenado__iexact=concatenado)
        .first()
    )
    if regla is None:
        raise ValidationError("No existe regla activa de severidad para los datos enviados.")

    return {
        "severidad": regla.severidad,
        "concatenado": regla.concatenado,
        "version": regla.version,
    }
