"""Serializers for Causa API payloads."""

from rest_framework import serializers

from backend.apps.riesgos.models import Causa


class CausaDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Causa
        fields = (
            "causa_id",
            "codigo_causa",
            "codigo_actual_causa",
            "descripcion_causa",
            "subfactor",
            "linea",
            "macroproceso",
            "dueno",
            "estado",
        )


class CausaWriteSerializer(serializers.ModelSerializer):
    riesgo_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Causa
        fields = ("riesgo_id", "codigo_actual_causa", "descripcion_causa", "subfactor", "linea", "macroproceso", "dueno", "estado")
        extra_kwargs = {"estado": {"required": False}}

    def validate(self, attrs):
        if "codigo_causa" in self.initial_data:
            raise serializers.ValidationError({"codigo_causa": "El código de causa es generado por el sistema."})
        return attrs
