"""Serializers for attachment metadata endpoints."""

from rest_framework import serializers

from backend.apps.compartido.models import Adjunto
from backend.apps.eventos.models import EventoRiesgo
from backend.apps.planes.models import PlanAccion
from backend.apps.usuarios.models import Usuario


class AdjuntoSerializer(serializers.ModelSerializer):
    evento_id = serializers.IntegerField(allow_null=True, required=False)
    plan_id = serializers.IntegerField(allow_null=True, required=False)
    usuario_carga_id = serializers.IntegerField()

    class Meta:
        model = Adjunto
        fields = (
            "adjunto_id",
            "evento_id",
            "plan_id",
            "nombre_archivo",
            "ruta_storage",
            "content_type",
            "tamano_bytes",
            "usuario_carga_id",
            "fecha_carga",
        )


class AdjuntoCreateUpdateSerializer(serializers.ModelSerializer):
    evento_id = serializers.PrimaryKeyRelatedField(
        source="evento",
        queryset=EventoRiesgo.objects.all(),
        allow_null=True,
        required=False,
    )
    plan_id = serializers.PrimaryKeyRelatedField(
        source="plan",
        queryset=PlanAccion.objects.all(),
        allow_null=True,
        required=False,
    )
    usuario_carga_id = serializers.PrimaryKeyRelatedField(source="usuario_carga", queryset=Usuario.objects.all())

    class Meta:
        model = Adjunto
        fields = AdjuntoSerializer.Meta.fields
        read_only_fields = ("adjunto_id",)

    def validate(self, attrs):
        evento = attrs.get("evento", getattr(self.instance, "evento", None))
        plan = attrs.get("plan", getattr(self.instance, "plan", None))
        if bool(evento) == bool(plan):
            raise serializers.ValidationError("El adjunto debe pertenecer a un evento o a un plan, pero no a ambos.")
        return attrs
