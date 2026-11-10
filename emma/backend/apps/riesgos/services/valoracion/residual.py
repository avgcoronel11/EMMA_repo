"""Residual risk rules approved for the EMMA Risk Matrix."""

from decimal import Decimal

from rest_framework.exceptions import ValidationError

from backend.apps.riesgos.services.valoracion.probabilidad import ETIQUETAS
from backend.apps.riesgos.services.valoracion.severidad import calcular_severidad
from backend.apps.riesgos.services.valoracion.utils import normalizar_texto


def _normalizar(valor):
    return (normalizar_texto(valor) or "").casefold()


def _movimiento(promedio):
    """ED/EE/EF: >0.20=2; >=0.10=1; otherwise=0."""
    if promedio > Decimal("0.20"):
        return 2
    if promedio >= Decimal("0.10"):
        return 1
    return 0


def _promedios_por_tipo(controles):
    # Solo participan controles activos al momento de valorar. Un mismo código
    # no puede afectar dos veces los promedios del mismo riesgo.
    controles_unicos = {}
    for control in controles:
        codigo = normalizar_texto(getattr(control, "codigo_control", None))
        clave = codigo.casefold() if codigo else f"__sin_codigo__{id(control)}"
        controles_unicos.setdefault(clave, control)
    controles_asociados = [control for control in controles_unicos.values() if _normalizar(control.estado) == "activo"]
    if not controles_asociados:
        return {}, 0

    total = Decimal(len(controles_asociados))
    promedios = {}
    for tipo in ("preventivo", "detectivo", "correctivo"):
        aportes = sum(
            1
            for control in controles_asociados
            if _normalizar(control.tipo_control) == tipo
            and _normalizar(control.efectividad) in {"fuerte", "moderado"}
        )
        promedios[tipo] = Decimal(aportes) / total
    return promedios, len(controles_asociados)


def _nivel_residual(nivel_inherente, reduccion):
    if nivel_inherente not in range(1, 6):
        raise ValidationError("El nivel inherente debe estar entre 1 y 5 para calcular el residual.")
    return min(5, max(1, nivel_inherente - reduccion))


def calcular_residual(*, probabilidad_inherente, impacto_inherente, controles, version=None, fecha=None):
    """Deriva el residual desde controles activos, sin sumar reducciones."""
    promedios, cantidad_controles = _promedios_por_tipo(controles)
    if not cantidad_controles:
        nivel_probabilidad = probabilidad_inherente
        nivel_impacto = impacto_inherente
        movimientos = {"preventivo": 0, "detectivo": 0, "correctivo": 0}
        promedios = {"preventivo": Decimal("0"), "detectivo": Decimal("0"), "correctivo": Decimal("0")}
    else:
        movimientos = {tipo: _movimiento(promedio) for tipo, promedio in promedios.items()}
        nivel_probabilidad = _nivel_residual(probabilidad_inherente, movimientos["preventivo"])
        reduccion_impacto = movimientos["correctivo"] or movimientos["detectivo"]
        nivel_impacto = _nivel_residual(impacto_inherente, reduccion_impacto)

    probabilidad_etiqueta = ETIQUETAS[nivel_probabilidad]
    impacto_etiqueta = {1: "Inferior", 2: "Menor", 3: "Importante", 4: "Mayor", 5: "Superior"}[nivel_impacto]
    severidad = calcular_severidad(
        probabilidad_etiqueta=probabilidad_etiqueta,
        impacto_etiqueta=impacto_etiqueta,
        version=version,
        fecha=fecha,
    )
    return {
        "probabilidad": {"nivel": nivel_probabilidad, "etiqueta": probabilidad_etiqueta},
        "impacto": {"nivel": nivel_impacto, "etiqueta": impacto_etiqueta},
        "severidad": severidad["severidad"],
        "controles_activos": cantidad_controles,
        "promedios": {tipo: str(valor) for tipo, valor in promedios.items()},
        "movimientos": movimientos,
    }
