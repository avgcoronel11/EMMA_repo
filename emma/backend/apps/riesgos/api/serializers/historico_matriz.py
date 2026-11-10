"""Read-only serializers for functional matrix history."""

from rest_framework import serializers

from backend.apps.riesgos.models import (
    ControlEvaluacionHistorico,
    HistorialRiesgoCausa,
    HistorialRiesgoCausaControl,
)


class ControlEvaluacionHistoricoSerializer(serializers.ModelSerializer):
    usuario_id = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = ControlEvaluacionHistorico
        fields = (
            "control_evaluacion_historico_id", "control_id", "usuario_id", "version",
            "fecha_evaluacion", "origen_registro", "d1", "d2", "d3", "d4",
            "o1", "o2", "o3", "o4", "o5", "cumple_diseno", "cumple_oper",
            "falla_vpr", "efectividad",
        )
        read_only_fields = fields


class HistorialRiesgoCausaSerializer(serializers.ModelSerializer):
    usuario_id = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = HistorialRiesgoCausa
        fields = (
            "historial_riesgo_causa_id", "riesgo_id", "causa_id", "version", "evento",
            "fecha_evento", "usuario_id", "origen_registro",
        )
        read_only_fields = fields


class HistorialRiesgoCausaControlSerializer(serializers.ModelSerializer):
    usuario_id = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = HistorialRiesgoCausaControl
        fields = (
            "historial_riesgo_causa_control_id", "riesgo_id", "causa_id", "control_id",
            "version", "evento", "fecha_evento", "usuario_id", "origen_registro",
        )
        read_only_fields = fields
