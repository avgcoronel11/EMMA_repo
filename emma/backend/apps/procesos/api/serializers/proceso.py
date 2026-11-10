"""Serializers for process APIs."""

from rest_framework import serializers

from backend.apps.procesos.models import CatProceso


class CatProcesoSerializer(serializers.ModelSerializer):
    parent_proceso_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = CatProceso
        fields = (
            "proceso_id",
            "parent_proceso_id",
            "vicepresidencia",
            "proceso_nivel0",
            "proceso_nivel1",
            "proceso_nivel2",
            "descripcion",
            "macroproceso",
            "linea",
        )
