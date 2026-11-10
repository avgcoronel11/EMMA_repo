"""Serializers for audit read endpoints."""

from rest_framework import serializers

from backend.apps.compartido.models import Auditoria


class AuditoriaSerializer(serializers.ModelSerializer):
    usuario_id = serializers.IntegerField()

    class Meta:
        model = Auditoria
        fields = (
            "auditoria_id",
            "entidad",
            "entidad_id",
            "codigo_negocio_snapshot",
            "version",
            "accion",
            "usuario_id",
            "fecha_cambio",
            "motivo_modificacion",
            "datos_anteriores",
            "datos_nuevos",
        )
