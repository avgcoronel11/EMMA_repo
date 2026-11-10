"""Serializers for user API endpoints."""

from rest_framework import serializers

from backend.apps.usuarios.models import Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = (
            "usuario_id",
            "entra_object_id",
            "username",
            "nombre",
            "correo",
            "estado",
            "fecha_creacion",
            "fecha_ultimo_acceso",
        )
