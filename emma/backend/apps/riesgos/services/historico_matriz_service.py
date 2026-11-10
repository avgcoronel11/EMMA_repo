"""Append-only functional history for matrix operations."""

from django.db.models import Max
from django.utils import timezone

from backend.apps.riesgos.models import (
    ControlEvaluacionHistorico,
    HistorialRiesgoCausa,
    HistorialRiesgoCausaControl,
)

OPERACION = "OPERACION"
BACKFILL = "BACKFILL"


def _next(queryset):
    return (queryset.aggregate(max_version=Max("version"))["max_version"] or 0) + 1


def registrar_evaluacion(control, *, usuario=None, origen_registro=OPERACION):
    """Caller must have locked ``control`` with select_for_update()."""
    return ControlEvaluacionHistorico.objects.create(
        control=control, usuario=usuario, version=_next(ControlEvaluacionHistorico.objects.filter(control=control)),
        fecha_evaluacion=timezone.now(), origen_registro=origen_registro,
        **{campo: getattr(control, campo) for campo in ("d1", "d2", "d3", "d4", "o1", "o2", "o3", "o4", "o5", "cumple_diseno", "cumple_oper", "falla_vpr", "efectividad")},
    )


def registrar_riesgo_causa(riesgo, causa, evento, *, usuario=None, origen_registro=OPERACION):
    return HistorialRiesgoCausa.objects.create(
        riesgo=riesgo, causa=causa,
        version=_next(HistorialRiesgoCausa.objects.filter(riesgo=riesgo, causa=causa)),
        evento=evento, fecha_evento=timezone.now(), usuario=usuario, origen_registro=origen_registro,
    )


def registrar_riesgo_causa_control(riesgo, causa, control, evento, *, usuario=None, origen_registro=OPERACION):
    return HistorialRiesgoCausaControl.objects.create(
        riesgo=riesgo, causa=causa, control=control,
        version=_next(HistorialRiesgoCausaControl.objects.filter(riesgo=riesgo, causa=causa, control=control)),
        evento=evento, fecha_evento=timezone.now(), usuario=usuario, origen_registro=origen_registro,
    )
