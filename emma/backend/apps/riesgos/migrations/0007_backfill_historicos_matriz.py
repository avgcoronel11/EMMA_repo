"""Create technical baseline history from the current DEV matrix state.

The recorded timestamp is the incorporation date into the functional history,
not evidence of the original business operation date.
"""

from django.db import migrations
from django.utils import timezone


def crear_baseline(apps, schema_editor):
    Control = apps.get_model("riesgos", "Control")
    RiesgoCausa = apps.get_model("riesgos", "RiesgoCausa")
    RiesgoCausaControl = apps.get_model("riesgos", "RiesgoCausaControl")
    ControlEvaluacionHistorico = apps.get_model("riesgos", "ControlEvaluacionHistorico")
    HistorialRiesgoCausa = apps.get_model("riesgos", "HistorialRiesgoCausa")
    HistorialRiesgoCausaControl = apps.get_model("riesgos", "HistorialRiesgoCausaControl")

    fecha_incorporacion = timezone.now()
    campos_evaluacion = (
        "d1", "d2", "d3", "d4", "o1", "o2", "o3", "o4", "o5",
        "cumple_diseno", "cumple_oper", "falla_vpr", "efectividad",
    )

    for control in Control.objects.all().iterator():
        if not any(getattr(control, campo) is not None for campo in campos_evaluacion):
            continue
        if not ControlEvaluacionHistorico.objects.filter(control_id=control.control_id).exists():
            ControlEvaluacionHistorico.objects.create(
                control_id=control.control_id,
                version=1,
                fecha_evaluacion=fecha_incorporacion,
                origen_registro="BACKFILL",
                **{campo: getattr(control, campo) for campo in campos_evaluacion},
            )

    for relacion in RiesgoCausa.objects.all().iterator():
        if not HistorialRiesgoCausa.objects.filter(
            riesgo_id=relacion.riesgo_id, causa_id=relacion.causa_id
        ).exists():
            HistorialRiesgoCausa.objects.create(
                riesgo_id=relacion.riesgo_id,
                causa_id=relacion.causa_id,
                version=1,
                evento="ASSOCIATE",
                fecha_evento=fecha_incorporacion,
                origen_registro="BACKFILL",
            )

    for relacion in RiesgoCausaControl.objects.all().iterator():
        if not HistorialRiesgoCausaControl.objects.filter(
            riesgo_id=relacion.riesgo_causa.riesgo_id,
            causa_id=relacion.riesgo_causa.causa_id,
            control_id=relacion.control_id,
        ).exists():
            HistorialRiesgoCausaControl.objects.create(
                riesgo_id=relacion.riesgo_causa.riesgo_id,
                causa_id=relacion.riesgo_causa.causa_id,
                control_id=relacion.control_id,
                version=1,
                evento="ASSOCIATE",
                fecha_evento=fecha_incorporacion,
                origen_registro="BACKFILL",
            )


class Migration(migrations.Migration):

    dependencies = [
        ("riesgos", "0006_historicos_matriz"),
    ]

    operations = [
        migrations.RunPython(crear_baseline, migrations.RunPython.noop),
    ]
