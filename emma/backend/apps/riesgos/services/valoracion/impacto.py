"""Impact valuation rules."""

from rest_framework.exceptions import ValidationError

from backend.apps.catalogos.models import CfgNivelImpacto
from backend.apps.riesgos.services.valoracion.utils import extraer_nivel, normalizar_texto, reglas_vigentes


DIMENSIONES_IMPACTO = (
    "Impacto Legal",
    "Impacto Reputacional",
    "Impacto servicio al cliente",
    "Información",
    "Continuidad",
    "Contagio",
    "Financiero",
)


def calcular_impacto(*, tipo_impacto, nivel, version=None, fecha=None):
    tipo_impacto = normalizar_texto(tipo_impacto)
    nivel = normalizar_texto(nivel)

    if not tipo_impacto:
        raise ValidationError({"tipo_impacto": "El tipo de impacto es requerido."})
    if not nivel:
        raise ValidationError({"nivel": "El nivel de impacto es requerido."})

    regla = (
        reglas_vigentes(CfgNivelImpacto, version=version, fecha=fecha)
        .filter(tipo_impacto__iexact=tipo_impacto, nivel__iexact=nivel)
        .first()
    )
    if regla is None:
        raise ValidationError("No existe regla activa de impacto para los datos enviados.")

    nivel_resultado = extraer_nivel(regla.nivel)
    if nivel_resultado not in range(1, 6):
        raise ValidationError("La dimensión de impacto debe resolverse en un nivel entre 1 y 5.")

    return {
        "nivel": nivel_resultado,
        "etiqueta": regla.impacto_inherente,
        "tipo_impacto": regla.tipo_impacto,
        "version": regla.version,
    }


def calcular_impacto_mayor(*, impactos: dict, version=None, fecha=None):
    recibidas = set((impactos or {}).keys())
    requeridas = set(DIMENSIONES_IMPACTO)
    faltantes = sorted(requeridas - recibidas)
    adicionales = sorted(recibidas - requeridas)
    if faltantes or adicionales:
        detalle = {}
        if faltantes:
            detalle["faltantes"] = faltantes
        if adicionales:
            detalle["no_reconocidas"] = adicionales
        raise ValidationError({"impactos": detalle})

    resultados = [
        calcular_impacto(tipo_impacto=tipo_impacto, nivel=nivel, version=version, fecha=fecha)
        for tipo_impacto, nivel in impactos.items()
    ]

    return max(resultados, key=lambda item: item["nivel"] or 0)
