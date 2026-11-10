"""Serializers for action plan API endpoints."""

from rest_framework import serializers

from backend.apps.eventos.models import EventoRiesgo
from backend.apps.planes.models import PlanAccion
from backend.apps.riesgos.models import Control


class PlanListSerializer(serializers.ModelSerializer):
    evento_id = serializers.IntegerField()
    control_id = serializers.IntegerField(allow_null=True, required=False)

    class Meta:
        model = PlanAccion
        fields = (
            "plan_id",
            "evento_id",
            "codigo_plan",
            "nombre_evento_snapshot",
            "descripcion_accion",
            "tipo_accion",
            "fecha_inicio",
            "fecha_cierre",
            "estado_plan",
            "avance_plan",
            "control_id",
        )


class PlanDetailSerializer(serializers.ModelSerializer):
    evento_id = serializers.IntegerField()
    control_id = serializers.IntegerField(allow_null=True, required=False)

    class Meta:
        model = PlanAccion
        fields = (
            "plan_id",
            "evento_id",
            "codigo_plan",
            "nombre_evento_snapshot",
            "descripcion_accion",
            "tipo_accion",
            "equipo_responsable",
            "fecha_inicio",
            "fecha_cierre",
            "estado_plan",
            "avance_plan",
            "control_id",
            "evidencia_texto",
            "observaciones_plan",
            "verificacion_control_interno",
            "dias_cierre_evento",
            "dias_plan",
            "fecha_descubrimiento_evento",
            "fecha_inicio_evento",
            "fecha_cierre_evento",
        )


class PlanCreateUpdateSerializer(serializers.ModelSerializer):
    evento_id = serializers.PrimaryKeyRelatedField(source="evento", queryset=EventoRiesgo.objects.all())
    control_id = serializers.PrimaryKeyRelatedField(
        source="control",
        queryset=Control.objects.all(),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = PlanAccion
        fields = PlanDetailSerializer.Meta.fields
        read_only_fields = ("plan_id",)

    def validate_avance_plan(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("El avance debe estar entre 0 y 100.")
        return value

    def validate(self, attrs):
        fecha_inicio = attrs.get("fecha_inicio", getattr(self.instance, "fecha_inicio", None))
        fecha_cierre = attrs.get("fecha_cierre", getattr(self.instance, "fecha_cierre", None))
        if fecha_inicio and fecha_cierre and fecha_cierre < fecha_inicio:
            raise serializers.ValidationError({"fecha_cierre": "La fecha de cierre no puede ser anterior a la fecha de inicio."})
        return attrs
