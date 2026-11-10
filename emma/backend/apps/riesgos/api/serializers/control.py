"""Serializers for Control API payloads."""

from rest_framework import serializers

from backend.apps.catalogos.models import CatalogoValor, CuentaContable
from backend.apps.riesgos.models import Control, ControlChecklist, ControlCuentaContable
from backend.apps.compartido.models import EntidadCaracteristica


class ControlDetailSerializer(serializers.ModelSerializer):
    control_generico = serializers.SerializerMethodField()
    sistemas = serializers.SerializerMethodField()
    principios_coso = serializers.SerializerMethodField()
    cuentas_contables = serializers.SerializerMethodField()
    checklists = serializers.SerializerMethodField()

    class Meta:
        model = Control
        fields = (
            "control_id",
            "codigo_control",
            "codigo_actual_control",
            "nombre_control",
            "objetivo",
            "descripcion_control",
            "importancia",
            "evidencia",
            "ejecutor_texto",
            "tipo_control",
            "naturaleza",
            "hyperion_a",
            "hyperion_e",
            "aplicaciones_adu_ipe",
            "cumple_diseno",
            "cumple_oper",
            "falla_vpr",
            "efectividad",
            "d1",
            "d2",
            "d3",
            "d4",
            "o1",
            "o2",
            "o3",
            "o4",
            "o5",
            "estado",
            "control_generico",
            "sistemas",
            "principios_coso",
            "cuentas_contables",
            "checklists",
        )

    def get_control_generico(self, obj):
        valor = obj.control_generico_valor
        if valor is None:
            return None
        return {
            "valor_id": valor.valor_id,
            "codigo": valor.codigo,
            "descripcion": valor.descripcion,
        }

    def _caracteristicas(self, obj, codigo_catalogo):
        return [
            {"valor_id": item.valor_catalogo_id, "codigo": item.valor_catalogo.codigo, "descripcion": item.valor_catalogo.descripcion}
            for item in obj.caracteristicas.select_related("valor_catalogo__catalogo").filter(
                valor_catalogo__catalogo__codigo_catalogo=codigo_catalogo, activo=True
            )
        ]

    def get_sistemas(self, obj):
        return self._caracteristicas(obj, "SISTEMA")

    def get_principios_coso(self, obj):
        return self._caracteristicas(obj, "PRINCIPIO_COSO")

    def get_cuentas_contables(self, obj):
        return [
            {"cuenta_id": item.cuenta_id, "codigo": item.cuenta.cuenta_10 or item.cuenta.cuenta_6, "descripcion": item.cuenta.descripcion}
            for item in obj.cuentas_contables.select_related("cuenta").all()
        ]

    def get_checklists(self, obj):
        return {tipo: list(obj.checklists.filter(tipo=tipo).values_list("valor", flat=True)) for tipo in ControlChecklist.Tipo.values}


class ControlEvaluacionSerializer(serializers.Serializer):
    d1 = serializers.ChoiceField(choices=("Sí", "No"), required=False)
    d2 = serializers.ChoiceField(choices=("Sí", "No"), required=False)
    d3 = serializers.ChoiceField(choices=("Sí", "No"), required=False)
    d4 = serializers.ChoiceField(choices=("Sí", "No"), required=False)
    o1 = serializers.ChoiceField(choices=("Sí", "No"), required=False)
    o2 = serializers.ChoiceField(choices=("Sí", "No"), required=False)
    o3 = serializers.ChoiceField(choices=("Sí", "No"), required=False)
    o4 = serializers.ChoiceField(choices=("Sí", "No"), required=False)
    o5 = serializers.ChoiceField(choices=("Sí", "No", "NA"), required=False)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("Debe enviar al menos una respuesta de evaluación.")
        return attrs


class ControlWriteSerializer(serializers.ModelSerializer):
    riesgo_id = serializers.IntegerField(write_only=True, required=False)
    causa_id = serializers.IntegerField(write_only=True, required=False)
    control_generico_valor_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    sistema_valor_ids = serializers.ListField(child=serializers.IntegerField(), required=False, write_only=True)
    principio_coso_valor_ids = serializers.ListField(child=serializers.IntegerField(), required=False, write_only=True)
    cuenta_ids = serializers.ListField(child=serializers.IntegerField(), required=False, write_only=True)
    aserciones = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)
    atributos = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)
    riesgos_control = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)

    class Meta:
        model = Control
        fields = ("codigo_actual_control", "nombre_control", "objetivo", "descripcion_control", "importancia", "evidencia", "ejecutor_texto", "tipo_control", "naturaleza", "hyperion_a", "hyperion_e", "aplicaciones_adu_ipe", "estado", "control_generico_valor_id", "riesgo_id", "causa_id", "sistema_valor_ids", "principio_coso_valor_ids", "cuenta_ids", "aserciones", "atributos", "riesgos_control")
        extra_kwargs = {"estado": {"required": False}}

    def validate(self, attrs):
        if self.instance is None:
            for field in ("nombre_control", "descripcion_control", "riesgo_id", "causa_id"):
                if not attrs.get(field):
                    raise serializers.ValidationError({field: "Este campo es obligatorio."})
        if "codigo_control" in self.initial_data:
            raise serializers.ValidationError({"codigo_control": "El código de control es generado por el sistema."})
        if "tipo_control" in attrs and attrs["tipo_control"] not in ("Preventivo", "Detectivo", "Correctivo"):
            raise serializers.ValidationError({"tipo_control": "Debe ser Preventivo, Detectivo o Correctivo."})
        if "naturaleza" in attrs and attrs["naturaleza"] not in ("Manual", "Dependiente de TI", "Automatizado"):
            raise serializers.ValidationError({"naturaleza": "Debe ser Manual, Dependiente de TI o Automatizado."})
        if "control_generico_valor_id" in attrs and attrs["control_generico_valor_id"] is not None:
            valido = CatalogoValor.objects.filter(
                valor_id=attrs["control_generico_valor_id"],
                activo=True,
                catalogo__codigo_catalogo="CONTROL_GENERICO",
            ).exists()
            if not valido:
                raise serializers.ValidationError(
                    {"control_generico_valor_id": "Debe referenciar un valor activo del catálogo CONTROL_GENERICO."}
                )
        for campo, catalogo in (("sistema_valor_ids", "SISTEMA"), ("principio_coso_valor_ids", "PRINCIPIO_COSO")):
            ids = attrs.get(campo)
            if ids is not None:
                if len(ids) != len(set(ids)):
                    raise serializers.ValidationError({campo: "No se deben repetir valores."})
                encontrados = CatalogoValor.objects.filter(valor_id__in=ids, activo=True, catalogo__codigo_catalogo=catalogo).count()
                if encontrados != len(ids):
                    raise serializers.ValidationError({campo: f"Debe contener valores activos de {catalogo}."})
        if "cuenta_ids" in attrs:
            ids = attrs["cuenta_ids"]
            if len(ids) != len(set(ids)) or CuentaContable.objects.filter(cuenta_id__in=ids, activo=True).count() != len(ids):
                raise serializers.ValidationError({"cuenta_ids": "Debe contener cuentas activas sin duplicados."})
        return attrs
