"""Probability rules approved in EMMA Tarea 3."""

from decimal import Decimal
import unicodedata

from rest_framework.exceptions import ValidationError

from backend.apps.catalogos.models import CfgProbabilidad
from backend.apps.riesgos.services.valoracion.utils import extraer_nivel, normalizar_texto, reglas_vigentes


ETIQUETAS = {1: "Muy Baja", 2: "Baja", 3: "Moderada", 4: "Alta", 5: "Muy Alta"}
NIVELES_ETIQUETA = {etiqueta.casefold(): nivel for nivel, etiqueta in ETIQUETAS.items()}


def _clave_normalizada(valor):
    texto = normalizar_texto(valor) or ""
    return "".join(
        caracter for caracter in unicodedata.normalize("NFD", texto).casefold()
        if unicodedata.category(caracter) != "Mn"
    )


def _nivel_cfg_probabilidad(valor, *, campo, version=None):
    """Resuelve complejidad o entorno desde la configuración vigente en PostgreSQL."""
    clave = _clave_normalizada(valor)
    if not clave:
        raise ValidationError({campo: "Este dato es requerido para calcular la probabilidad inherente."})

    niveles = set()
    for regla in reglas_vigentes(CfgProbabilidad, version=version):
        configurado = getattr(regla, campo)
        if _clave_normalizada(configurado) == clave:
            nivel = extraer_nivel(regla.nivel)
            if nivel in range(1, 6):
                niveles.add(nivel)
    if len(niveles) == 1:
        return niveles.pop()
    if len(niveles) > 1:
        raise ValidationError(
            {campo: "CFG_PROBABILIDAD contiene niveles vigentes contradictorios para el valor enviado."}
        )
    raise ValidationError(
        {campo: "No existe una equivalencia vigente en CFG_PROBABILIDAD para el valor enviado."}
    )


def _nivel_por_texto(valor, *, componente, equivalencias=None):
    """Obtiene el nivel Tarea 3 sin sustituir una regla por un valor recibido."""
    texto = normalizar_texto(valor)
    if not texto:
        raise ValidationError({componente: "Este dato es requerido para calcular la probabilidad inherente."})

    clave = texto.casefold()
    if equivalencias and clave in equivalencias:
        return equivalencias[clave]
    if clave in NIVELES_ETIQUETA:
        return NIVELES_ETIQUETA[clave]
    # Los catálogos fuente comienzan por nivel: "5 - Diaria" y "3-1 ...".
    if texto[0] in "12345" and (len(texto) == 1 or texto[1] in " -"):
        return int(texto[0])
    raise ValidationError({componente: "El valor no corresponde a una equivalencia aprobada de Tarea 3."})


def _probabilidad_historica(*, eventos_riesgo, poblacion_expuesta):
    if eventos_riesgo is None or poblacion_expuesta is None:
        raise ValidationError(
            {"probabilidad_historica": "Eventos de riesgo y población expuesta son requeridos."}
        )
    if poblacion_expuesta <= 0:
        raise ValidationError({"poblacion_expuesta": "Debe ser mayor que cero."})
    if eventos_riesgo < 0:
        raise ValidationError({"eventos_riesgo": "No puede ser negativo."})

    porcentaje = Decimal(eventos_riesgo) / Decimal(poblacion_expuesta)
    # Regla aprobada Tarea 3 (MATRIZ!AJ12): las comparaciones son estrictas.
    # Las fronteras exactas 1 %, 5 %, 10 % y 15 % caen en el valor por defecto
    # Muy Baja, igual que cualquier valor no cubierto por los intervalos.
    if porcentaje > Decimal("0.15"):
        nivel = 5
    elif Decimal("0.10") < porcentaje < Decimal("0.15"):
        nivel = 4
    elif Decimal("0.05") < porcentaje < Decimal("0.10"):
        nivel = 3
    elif Decimal("0.01") < porcentaje < Decimal("0.05"):
        nivel = 2
    else:
        nivel = 1
    return nivel, porcentaje


def calcular_probabilidad(
    *,
    exposicion,
    complejidad,
    condiciones_entorno,
    grado_ocurrencia,
    eventos_riesgo,
    poblacion_expuesta,
    version=None,
    **_ignored,
):
    """Calcula y compara los tres componentes inherentes de Tarea 3."""
    nivel_exposicion = _nivel_por_texto(exposicion, componente="exposicion")
    nivel_complejidad = _nivel_cfg_probabilidad(complejidad, campo="complejidad", version=version)
    nivel_entorno = _nivel_cfg_probabilidad(
        condiciones_entorno, campo="condiciones_entorno", version=version
    )
    promedio = (nivel_exposicion + nivel_complejidad + nivel_entorno) / 3
    # El aplicativo original usa el redondeo nativo de Python (half-to-even).
    nivel_cualitativo = round(promedio)
    nivel_ocurrencia = _nivel_por_texto(grado_ocurrencia, componente="grado_ocurrencia")
    nivel_historico, porcentaje_historico = _probabilidad_historica(
        eventos_riesgo=eventos_riesgo,
        poblacion_expuesta=poblacion_expuesta,
    )
    # Tarea 3 / MATRIZ!AZ12: prevalece la probabilidad de mayor nivel.
    nivel_final = max(nivel_cualitativo, nivel_ocurrencia, nivel_historico)

    return {
        "nivel": nivel_final,
        "etiqueta": ETIQUETAS[nivel_final],
        "componentes": {
            "cualitativa": {
                "nivel": nivel_cualitativo,
                "etiqueta": ETIQUETAS[nivel_cualitativo],
                "exposicion": nivel_exposicion,
                "complejidad": nivel_complejidad,
                "condiciones_entorno": nivel_entorno,
            },
            "ocurrencia": {"nivel": nivel_ocurrencia, "etiqueta": ETIQUETAS[nivel_ocurrencia]},
            "historica": {
                "nivel": nivel_historico,
                "etiqueta": ETIQUETAS[nivel_historico],
                "porcentaje": str(porcentaje_historico),
            },
        },
    }
