"""Write services for attachment metadata."""

from django.db import transaction

from backend.apps.compartido.models import Adjunto


class AdjuntoService:
    @staticmethod
    @transaction.atomic
    def crear_adjunto(validated_data):
        return Adjunto.objects.create(**validated_data)

    @staticmethod
    @transaction.atomic
    def actualizar_adjunto(adjunto, validated_data):
        for field, value in validated_data.items():
            setattr(adjunto, field, value)
        adjunto.save()
        return adjunto

    @staticmethod
    @transaction.atomic
    def eliminar_adjunto(adjunto):
        adjunto.delete()
