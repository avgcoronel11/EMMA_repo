"""Serializers for risk valuation API payloads."""

from rest_framework import serializers


class ProbabilidadInputSerializer(serializers.Serializer):
    exposicion = serializers.CharField(max_length=255)
    complejidad = serializers.CharField(max_length=255)
    condiciones_entorno = serializers.CharField(max_length=255)
    grado_ocurrencia = serializers.CharField(max_length=255)
    eventos_riesgo = serializers.IntegerField(min_value=0)
    poblacion_expuesta = serializers.IntegerField(min_value=1)


class ImpactoInputSerializer(serializers.Serializer):
    impactos = serializers.DictField(child=serializers.CharField(max_length=100, allow_blank=False))


class ValoracionInputSerializer(serializers.Serializer):
    probabilidad = ProbabilidadInputSerializer()
    impacto = ImpactoInputSerializer()
    version = serializers.CharField(max_length=30, required=False)
