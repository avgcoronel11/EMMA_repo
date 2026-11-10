"""Opciones de entrada aprobadas para el formulario de valoración."""

from backend.apps.catalogos.models import CfgNivelImpacto, CfgProbabilidad
from backend.apps.riesgos.services.valoracion.utils import reglas_vigentes


EXPOSICION = (
    ("1 - Anualmente", "Muy Baja — Anualmente"),
    ("2 - Entre trimestral y semestral", "Baja — Entre trimestral y semestral"),
    ("3 - Mensual", "Moderada — Mensual"),
    ("4 - Semanal", "Alta — Semanal"),
    ("5 - Diaria o quincenal", "Muy Alta — Diaria o quincenal"),
)
OCURRENCIA = (
    ("1 - Menos del 1 % de los casos", "Muy Baja — Menos del 1 % de los casos"),
    ("2 - Entre el 1 % y el 4,99 % de los casos", "Baja — Entre el 1 % y el 4,99 % de los casos"),
    ("3 - Entre el 5 % y el 9,99 % de los casos", "Moderada — Entre el 5 % y el 9,99 % de los casos"),
    ("4 - Entre el 10 % y el 15 % de los casos", "Alta — Entre el 10 % y el 15 % de los casos"),
    ("5 - Más del 15 % de los casos", "Muy Alta — Más del 15 % de los casos"),
)
ETIQUETAS_IMPACTO = {
    "1": "Inferior", "2": "Menor", "3": "Importante", "4": "Mayor", "5": "Superior"
}


def _opciones(valores):
    return [{"valor": valor, "etiqueta": etiqueta} for valor, etiqueta in valores]


def obtener_configuracion(*, version=None):
    reglas_probabilidad = list(reglas_vigentes(CfgProbabilidad, version=version))
    reglas_impacto = list(reglas_vigentes(CfgNivelImpacto, version=version))
    complejidad = sorted({regla.complejidad for regla in reglas_probabilidad if regla.complejidad})
    entorno = sorted({regla.condiciones_entorno for regla in reglas_probabilidad if regla.condiciones_entorno})
    impactos = {}
    for regla in reglas_impacto:
        if regla.tipo_impacto and regla.nivel:
            impactos.setdefault(regla.tipo_impacto, set()).add(str(regla.nivel))
    return {
        "version": version or (reglas_probabilidad[0].version if reglas_probabilidad else None),
        "exposicion": _opciones(EXPOSICION),
        "complejidad": _opciones((valor, valor) for valor in complejidad),
        "condiciones_entorno": _opciones((valor, valor) for valor in entorno),
        "grado_ocurrencia": _opciones(OCURRENCIA),
        "impactos": [
            {
                "nombre": nombre,
                "opciones": _opciones((nivel, f"{nivel} — {ETIQUETAS_IMPACTO.get(nivel, nivel)}") for nivel in sorted(niveles)),
            }
            for nombre, niveles in sorted(impactos.items())
        ],
    }
