"""Serializers for catalog APIs."""

from rest_framework import serializers

from backend.apps.catalogos.models import Catalogo, CatalogoValor, CuentaContable, RiesgoGenerico


class CatalogoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Catalogo
        fields = ("catalogo_id", "codigo_catalogo", "nombre", "descripcion", "activo")


class CatalogoValorSerializer(serializers.ModelSerializer):
    parent_valor_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = CatalogoValor
        fields = (
            "valor_id",
            "codigo",
            "descripcion",
            "parent_valor_id",
            "nivel",
            "orden",
            "metadata_jsonb",
            "direccion",
            "ciudad",
            "departamento",
        )


class RiesgoGenericoSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiesgoGenerico
        fields = ("riesgo_generico_id", "codigo", "nombre")


class CuentaContableSerializer(serializers.ModelSerializer):
    """Contrato de lectura para el selector N:M de cuentas de un control."""

    codigo = serializers.SerializerMethodField()

    class Meta:
        model = CuentaContable
        fields = ("cuenta_id", "codigo", "descripcion")

    def get_codigo(self, obj):
        return obj.cuenta_10 or obj.cuenta_6
