"""Serializers for Riesgo API payloads."""

from rest_framework import serializers

from backend.apps.catalogos.models import CatalogoValor, RiesgoGenerico
from backend.apps.compartido.models import EntidadCaracteristica
from backend.apps.procesos.models import CatProceso
from backend.apps.riesgos.api.serializers.causa import CausaDetailSerializer
from backend.apps.riesgos.api.serializers.control import ControlDetailSerializer
from backend.apps.riesgos.api.serializers.valoracion import ValoracionInputSerializer
from backend.apps.riesgos.models import Riesgo, ValoracionRiesgo, ValoracionRiesgoControl


class ValoracionRiesgoControlSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValoracionRiesgoControl
        fields = "__all__"


class ValoracionRiesgoSerializer(serializers.ModelSerializer):
    controles = ValoracionRiesgoControlSerializer(many=True, read_only=True)

    class Meta:
        model = ValoracionRiesgo
        fields = "__all__"


class RiesgoGenericoNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiesgoGenerico
        fields = ("riesgo_generico_id", "codigo", "nombre")


class ProcesoRelacionadoSerializer(serializers.Serializer):
    proceso_id = serializers.IntegerField()
    principal = serializers.BooleanField(allow_null=True)
    vicepresidencia = serializers.CharField(allow_null=True)
    proceso_nivel0 = serializers.CharField(allow_null=True)
    proceso_nivel1 = serializers.CharField(allow_null=True)
    proceso_nivel2 = serializers.CharField(allow_null=True)
    macroproceso = serializers.CharField(allow_null=True)
    linea = serializers.CharField(allow_null=True)


class EntidadCaracteristicaSerializer(serializers.ModelSerializer):
    valor_catalogo = serializers.SerializerMethodField()

    class Meta:
        model = EntidadCaracteristica
        fields = (
            "entidad_caracteristica_id",
            "valor_catalogo",
            "valor_libre",
            "valor_snapshot",
            "orden",
            "activo",
        )

    def get_valor_catalogo(self, obj):
        valor = obj.valor_catalogo
        if valor is None:
            return None
        return {
            "valor_id": valor.valor_id,
            "codigo": valor.codigo,
            "descripcion": valor.descripcion,
        }


class RiesgoListSerializer(serializers.ModelSerializer):
    riesgo_generico = RiesgoGenericoNestedSerializer(read_only=True)

    class Meta:
        model = Riesgo
        fields = (
            "riesgo_id",
            "codigo_riesgo",
            "nombre_riesgo",
            "riesgo_generico",
            "riesgo_homologado",
            "linea",
            "macroproceso",
            "dueno_proceso",
            "frente_riesgo_asociado",
            "checklist_riesgo",
            "factor_riesgo_tipo_evento",
            "control_cambios",
            "frecuencia",
            "detalle_frecuencia",
            "estado",
            "severidad_inherente",
            "severidad_residual",
        )


class RiesgoDetailSerializer(serializers.ModelSerializer):
    riesgo_generico = RiesgoGenericoNestedSerializer(read_only=True)
    procesos = serializers.SerializerMethodField()
    causas = serializers.SerializerMethodField()
    controles = serializers.SerializerMethodField()
    caracteristicas = EntidadCaracteristicaSerializer(many=True, read_only=True)

    class Meta:
        model = Riesgo
        fields = (
            "riesgo_id",
            "codigo_riesgo",
            "nombre_riesgo",
            "codigo_referencia_saro",
            "ciclo",
            "riesgo_generico",
            "riesgo_homologado",
            "frente_riesgo_asociado",
            "checklist_riesgo",
            "factor_riesgo_tipo_evento",
            "control_cambios",
            "frecuencia",
            "detalle_frecuencia",
            "subfactor_riesgo",
            "descripcion_proceso",
            "linea",
            "macroproceso",
            "dueno_proceso",
            "exposicion",
            "complejidad",
            "condiciones_entorno",
            "grado_ocurrencia",
            "eventos_riesgo",
            "poblacion_expuesta",
            "impacto_legal",
            "impacto_reputacional",
            "impacto_servicio_cliente",
            "impacto_informacion",
            "impacto_continuidad",
            "impacto_contagio",
            "impacto_financiero",
            "prob_inherente_etiqueta",
            "prob_inherente_nivel",
            "impacto_inherente_etiqueta",
            "impacto_inherente_nivel",
            "severidad_inherente",
            "prob_residual_etiqueta",
            "prob_residual_nivel",
            "impacto_residual_etiqueta",
            "impacto_residual_nivel",
            "severidad_residual",
            "estado",
            "justificacion_inactivacion",
            "fecha_inactivacion",
            "fecha_ultima_edicion",
            "comentario_ultima_edicion",
            "procesos",
            "causas",
            "controles",
            "caracteristicas",
        )

    def get_procesos(self, obj):
        result = []
        for relacion in obj.riesgo_procesos.all():
            proceso = relacion.proceso
            result.append(
                {
                    "proceso_id": proceso.proceso_id,
                    "principal": relacion.principal,
                    "vicepresidencia": proceso.vicepresidencia,
                    "proceso_nivel0": proceso.proceso_nivel0,
                    "proceso_nivel1": proceso.proceso_nivel1,
                    "proceso_nivel2": proceso.proceso_nivel2,
                    "macroproceso": proceso.macroproceso,
                    "linea": proceso.linea,
                }
            )
        return result

    def get_causas(self, obj):
        """Prioriza RiesgoCausa y conserva la FK histórica durante transición."""
        causas = {}
        for asociacion in obj.causa_asociaciones.all():
            causas[asociacion.causa_id] = asociacion.causa
        for causa in obj.causas.all():
            causas.setdefault(causa.causa_id, causa)
        return CausaDetailSerializer(
            sorted(causas.values(), key=lambda causa: (causa.codigo_causa or "", causa.causa_id)), many=True
        ).data

    def get_controles(self, obj):
        """Obtiene controles puente sin duplicarlos y conserva históricos directos."""
        controles = {}
        for asociacion_causa in obj.causa_asociaciones.all():
            for asociacion_control in asociacion_causa.control_asociaciones.all():
                controles[asociacion_control.control_id] = asociacion_control.control
        for control in obj.controles.all():
            controles.setdefault(control.control_id, control)
        return ControlDetailSerializer(
            sorted(controles.values(), key=lambda control: (control.codigo_control or "", control.control_id)), many=True
        ).data


class CaracteristicaCreateSerializer(serializers.Serializer):
    valor_catalogo_id = serializers.IntegerField(required=False, allow_null=True)
    valor_libre = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    valor_snapshot = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    orden = serializers.IntegerField(required=False, allow_null=True)

    def validate_valor_catalogo_id(self, value):
        if value is None:
            return value
        if not CatalogoValor.objects.filter(valor_id=value, activo=True).exists():
            raise serializers.ValidationError("No existe un valor de catalogo activo con este id.")
        return value


class RiesgoCreateSerializer(serializers.ModelSerializer):
    riesgo_generico_id = serializers.IntegerField(required=False, allow_null=True)
    proceso_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
    )
    proceso_principal_id = serializers.IntegerField(required=False, allow_null=True)
    caracteristicas = CaracteristicaCreateSerializer(many=True, required=False)
    valoracion = ValoracionInputSerializer(required=False)

    class Meta:
        model = Riesgo
        fields = (
            "nombre_riesgo",
            "codigo_referencia_saro",
            "ciclo",
            "riesgo_generico_id",
            "riesgo_homologado",
            "frente_riesgo_asociado",
            "checklist_riesgo",
            "factor_riesgo_tipo_evento",
            "control_cambios",
            "frecuencia",
            "detalle_frecuencia",
            "subfactor_riesgo",
            "descripcion_proceso",
            "linea",
            "macroproceso",
            "dueno_proceso",
            "impacto_legal",
            "impacto_reputacional",
            "impacto_servicio_cliente",
            "impacto_informacion",
            "impacto_continuidad",
            "impacto_contagio",
            "impacto_financiero",
            "estado",
            "comentario_ultima_edicion",
            "proceso_ids",
            "proceso_principal_id",
            "caracteristicas",
            "valoracion",
        )
        extra_kwargs = {
            "estado": {"required": False, "allow_blank": True},
        }

    def validate_riesgo_generico_id(self, value):
        if value is None:
            return value
        if not RiesgoGenerico.objects.filter(riesgo_generico_id=value, activo=True).exists():
            raise serializers.ValidationError("No existe un riesgo generico activo con este id.")
        return value

    def validate(self, attrs):
        if "codigo_riesgo" in self.initial_data:
            raise serializers.ValidationError(
                {"codigo_riesgo": "El codigo GR es generado por el sistema y no se recibe manualmente."}
            )

        proceso_ids = attrs.get("proceso_ids") or []
        if len(proceso_ids) > 1:
            raise serializers.ValidationError({"proceso_ids": "Solo se puede asociar un proceso a cada riesgo."})
        if len(proceso_ids) != len(set(proceso_ids)):
            raise serializers.ValidationError({"proceso_ids": "No se deben repetir procesos."})

        if proceso_ids:
            existentes = set(
                CatProceso.objects.filter(proceso_id__in=proceso_ids, activo=True).values_list(
                    "proceso_id",
                    flat=True,
                )
            )
            faltantes = sorted(set(proceso_ids) - existentes)
            if faltantes:
                raise serializers.ValidationError({"proceso_ids": f"Procesos inexistentes o inactivos: {faltantes}"})

        principal_id = attrs.get("proceso_principal_id")
        if principal_id is not None and principal_id not in proceso_ids:
            raise serializers.ValidationError(
                {"proceso_principal_id": "El proceso principal debe estar en proceso_ids."}
            )
        if proceso_ids and principal_id is not None and principal_id != proceso_ids[0]:
            raise serializers.ValidationError(
                {"proceso_principal_id": "Debe coincidir con el único proceso seleccionado."}
            )

        return attrs


class RiesgoInactivarSerializer(serializers.Serializer):
    justificacion = serializers.CharField(allow_blank=True, trim_whitespace=True)


class RiesgoUpdateSerializer(serializers.ModelSerializer):
    """Actualiza únicamente los campos que también se diligencian al crear."""
    valoracion = ValoracionInputSerializer(required=False)
    proceso_ids = serializers.ListField(child=serializers.IntegerField(), required=False, allow_empty=False)
    proceso_principal_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Riesgo
        fields = (
            "nombre_riesgo", "codigo_referencia_saro", "ciclo", "riesgo_generico", "riesgo_homologado",
            "frente_riesgo_asociado", "checklist_riesgo", "factor_riesgo_tipo_evento",
            "control_cambios", "frecuencia", "detalle_frecuencia",
            "subfactor_riesgo", "descripcion_proceso", "linea", "macroproceso", "dueno_proceso",
            "impacto_legal", "impacto_reputacional", "impacto_servicio_cliente", "impacto_informacion",
            "impacto_continuidad", "impacto_contagio", "impacto_financiero", "comentario_ultima_edicion", "valoracion",
            "proceso_ids", "proceso_principal_id",
        )

    def validate(self, attrs):
        proceso_ids = attrs.get("proceso_ids")
        if proceso_ids is None:
            return attrs
        if len(proceso_ids) > 1:
            raise serializers.ValidationError({"proceso_ids": "Solo se puede asociar un proceso a cada riesgo."})
        if len(proceso_ids) != len(set(proceso_ids)):
            raise serializers.ValidationError({"proceso_ids": "No se deben repetir procesos."})
        existentes = set(CatProceso.objects.filter(proceso_id__in=proceso_ids, activo=True).values_list("proceso_id", flat=True))
        faltantes = sorted(set(proceso_ids) - existentes)
        if faltantes:
            raise serializers.ValidationError({"proceso_ids": f"Procesos inexistentes o inactivos: {faltantes}"})
        principal = attrs.get("proceso_principal_id")
        if principal is not None and principal not in proceso_ids:
            raise serializers.ValidationError({"proceso_principal_id": "El proceso principal debe estar en proceso_ids."})
        if principal is not None and principal != proceso_ids[0]:
            raise serializers.ValidationError({"proceso_principal_id": "Debe coincidir con el único proceso seleccionado."})
        return attrs
