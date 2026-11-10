"""Serializers for event risk API endpoints."""

from datetime import datetime

from django.utils import timezone
from rest_framework import serializers

from backend.apps.catalogos.models import CatalogoValor, CuentaContable
from backend.apps.compartido.models import EntidadCaracteristica
from backend.apps.eventos.models import (
    EventoCausa,
    EventoControl,
    EventoCuentaContable,
    EventoDistribucionLinea,
    EventoRiesgo,
)
from backend.apps.riesgos.models import Causa, Control, Riesgo
from backend.apps.usuarios.models import Usuario


CATALOGOS_EVENTO = {
    "PRODUCTO", "CANAL", "SEGMENTO", "PAIS", "DEPARTAMENTO", "CIUDAD",
    "LINEA_NEGOCIO", "TIPO_EVENTO", "CLASE_EVENTO",
}
TIPOS_SITIO = {
    "OFICINA": "OFICINA",
    "DIRECCION_GENERAL": "GERENCIA_EVENTO",
}


def _es_otro(valor):
    texto = "".join(caracter for caracter in (valor.codigo or valor.descripcion).casefold() if caracter.isalnum())
    return texto == "otro"


class EventoCausaSerializer(serializers.ModelSerializer):
    causa_id = serializers.IntegerField(allow_null=True, required=False)
    codigo_causa_snapshot = serializers.CharField(read_only=True)
    descripcion_causa_snapshot = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = EventoCausa
        fields = (
            "evento_causa_id",
            "causa_id",
            "codigo_causa_snapshot",
            "descripcion_causa_snapshot",
            "es_causa_libre",
            "orden",
        )


class EventoControlSerializer(serializers.ModelSerializer):
    control_id = serializers.IntegerField()
    codigo_control_snapshot = serializers.CharField(read_only=True)
    descripcion_control_snapshot = serializers.CharField(read_only=True)

    class Meta:
        model = EventoControl
        fields = (
            "evento_control_id",
            "control_id",
            "codigo_control_snapshot",
            "descripcion_control_snapshot",
            "orden",
        )


class EventoCuentaContableSerializer(serializers.ModelSerializer):
    cuenta_valor_id = serializers.IntegerField(allow_null=True, required=False)
    cuenta_id = serializers.IntegerField()
    codigo_cuenta_snapshot = serializers.CharField(read_only=True)
    descripcion_cuenta_snapshot = serializers.CharField(read_only=True)

    class Meta:
        model = EventoCuentaContable
        fields = (
            "evento_cuenta_id",
            "tipo_cuenta",
            "cuenta_valor_id",
            "cuenta_id",
            "codigo_cuenta_snapshot",
            "descripcion_cuenta_snapshot",
            "orden",
        )


class EventoDistribucionLineaSerializer(serializers.ModelSerializer):
    linea_valor_id = serializers.IntegerField()

    class Meta:
        model = EventoDistribucionLinea
        fields = (
            "evento_distribucion_id",
            "linea",
            "linea_valor_id",
            "linea_snapshot",
            "porcentaje",
        )


class EventoCaracteristicaSerializer(serializers.ModelSerializer):
    valor_catalogo_id = serializers.IntegerField(allow_null=True, required=False)

    class Meta:
        model = EntidadCaracteristica
        fields = (
            "entidad_caracteristica_id",
            "valor_catalogo_id",
            "valor_libre",
            "valor_snapshot",
            "orden",
            "activo",
        )


class EventoListSerializer(serializers.ModelSerializer):
    riesgo_id = serializers.IntegerField()

    class Meta:
        model = EventoRiesgo
        fields = (
            "evento_id",
            "id_ocurrencia",
            "riesgo_id",
            "codigo_riesgo_snapshot",
            "descripcion_evento",
            "fecha_inicio_evento",
            "fecha_descubrimiento_evento",
            "estado_evento",
            "cuantia_perdida_neta",
            "evento_ciberseguridad",
            "evento_alto_impacto",
        )


class EventoDetailSerializer(serializers.ModelSerializer):
    usuario_registro_id = serializers.IntegerField()
    riesgo_id = serializers.IntegerField()
    tipo_evento_valor_id = serializers.IntegerField(allow_null=True, required=False)
    causas = EventoCausaSerializer(source="evento_causas", many=True, read_only=True)
    controles = EventoControlSerializer(source="evento_controles", many=True, read_only=True)
    cuentas_contables = EventoCuentaContableSerializer(many=True, read_only=True)
    distribuciones_linea = EventoDistribucionLineaSerializer(many=True, read_only=True)
    caracteristicas = EventoCaracteristicaSerializer(many=True, read_only=True)
    sitio_ocurrencia_tipo = serializers.SerializerMethodField()
    sitio_ocurrencia_valor_id = serializers.IntegerField(read_only=True, allow_null=True)
    sitio_deteccion_tipo = serializers.SerializerMethodField()
    sitio_deteccion_valor_id = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = EventoRiesgo
        fields = (
            "evento_id",
            "id_ocurrencia",
            "usuario_registro_id",
            "riesgo_id",
            "tipo_evento_valor_id",
            "orden_cargue",
            "fecha_registro",
            "hora_registro",
            "id_usuario_informador",
            "fecha_inicio_evento",
            "hora_inicio_evento",
            "fecha_finalizacion_evento",
            "hora_finalizacion_evento",
            "fecha_descubrimiento_evento",
            "hora_descubrimiento_evento",
            "nombre_evento",
            "descripcion_evento",
            "codigo_riesgo_snapshot",
            "descripcion_riesgo_snapshot",
            "riesgo_generico_snapshot",
            "riesgo_asociado_display",
            "vicepresidencia_snapshot",
            "proceso_snapshot",
            "subproceso_snapshot",
            "gerencia_duena_snapshot",
            "cuantia_estimada",
            "cantidad_casos",
            "tipo_perdida",
            "estado_evento",
            "divisa",
            "cuantia_perdida_bruta",
            "cuantia_recuperaciones_total",
            "cuantia_recuperada_seguros",
            "cuantia_otras_recuperaciones",
            "tipo_recuperacion",
            "cuantia_perdida_neta",
            "fecha_contabilizacion_evento",
            "fecha_recuperacion_evento",
            "fecha_cierre_evento",
            "evento_ciberseguridad",
            "evento_alto_impacto",
            "sitio_ocurrencia",
            "sitio_deteccion",
            "sitio_ocurrencia_tipo",
            "sitio_ocurrencia_valor_id",
            "sitio_deteccion_tipo",
            "sitio_deteccion_valor_id",
            "pais_evento",
            "departamento_evento",
            "ciudad_evento",
            "linea_negocio_1",
            "linea_negocio_2",
            "dependencia_contabiliza",
            "numero_comprobante_sub_eventos",
            "dependencia_contabiliza_recuperacion",
            "numero_comprobante_recuperacion",
            "causas",
            "controles",
            "cuentas_contables",
            "distribuciones_linea",
            "caracteristicas",
        )

    def _tipo_sitio(self, obj, campo):
        valor = getattr(obj, campo)
        if not valor or not valor.catalogo_id:
            return None
        return "OFICINA" if valor.catalogo.codigo_catalogo == "OFICINA" else "DIRECCION_GENERAL"

    def get_sitio_ocurrencia_tipo(self, obj):
        return self._tipo_sitio(obj, "sitio_ocurrencia_valor")

    def get_sitio_deteccion_tipo(self, obj):
        return self._tipo_sitio(obj, "sitio_deteccion_valor")


class EventoCreateUpdateSerializer(serializers.ModelSerializer):
    id_ocurrencia = serializers.CharField(read_only=True)
    usuario_registro_id = serializers.IntegerField(read_only=True)
    riesgo_id = serializers.PrimaryKeyRelatedField(source="riesgo", queryset=Riesgo.objects.all())
    tipo_evento_valor_id = serializers.PrimaryKeyRelatedField(
        source="tipo_evento_valor",
        queryset=CatalogoValor.objects.all(),
        allow_null=True,
        required=False,
    )
    causas = EventoCausaSerializer(many=True, required=False)
    controles = EventoControlSerializer(many=True, required=False)
    cuentas_contables = EventoCuentaContableSerializer(many=True, required=False)
    distribuciones_linea = EventoDistribucionLineaSerializer(many=True, required=False)
    caracteristicas = EventoCaracteristicaSerializer(many=True, required=False)
    tipo_recuperacion = serializers.ListField(
        child=serializers.ChoiceField(choices=("SEGUROS", "DIFERENTE_DE_SEGUROS")),
        required=False,
        allow_empty=True,
    )
    sitio_ocurrencia_tipo = serializers.ChoiceField(choices=tuple(TIPOS_SITIO), write_only=True, required=False, allow_null=True)
    sitio_ocurrencia_valor_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    sitio_ocurrencia_padre_valor_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    sitio_deteccion_tipo = serializers.ChoiceField(choices=tuple(TIPOS_SITIO), write_only=True, required=False, allow_null=True)
    sitio_deteccion_valor_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    sitio_deteccion_padre_valor_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = EventoRiesgo
        fields = EventoDetailSerializer.Meta.fields + (
            "sitio_ocurrencia_tipo", "sitio_ocurrencia_valor_id", "sitio_ocurrencia_padre_valor_id",
            "sitio_deteccion_tipo", "sitio_deteccion_valor_id", "sitio_deteccion_padre_valor_id",
        )
        read_only_fields = (
            "evento_id", "id_ocurrencia", "usuario_registro_id", "fecha_registro", "hora_registro",
            "codigo_riesgo_snapshot", "descripcion_riesgo_snapshot", "riesgo_generico_snapshot",
            "riesgo_asociado_display", "vicepresidencia_snapshot", "proceso_snapshot",
            "subproceso_snapshot", "gerencia_duena_snapshot", "cuantia_perdida_neta",
        )

    def validate_causas(self, value):
        vistos = set()
        for item in value:
            causa_id = item.get("causa_id")
            es_libre = item.get("es_causa_libre", False)
            descripcion = (item.get("descripcion_causa_snapshot") or "").strip()
            if causa_id is None and (not es_libre or not descripcion):
                raise serializers.ValidationError("Una causa libre debe marcarse como tal e incluir su descripción.")
            if causa_id is not None and es_libre:
                raise serializers.ValidationError("Una causa existente no puede registrarse como causa libre.")
            if causa_id is not None and not Causa.objects.filter(causa_id=causa_id).exists():
                raise serializers.ValidationError(f"No existe la causa {causa_id}.")
            clave = ("libre", descripcion.casefold()) if causa_id is None else ("causa", causa_id)
            if clave in vistos:
                raise serializers.ValidationError("No se pueden repetir causas en un evento.")
            vistos.add(clave)
        return value

    def validate_controles(self, value):
        vistos = set()
        for item in value:
            control_id = item.get("control_id")
            if not Control.objects.filter(control_id=control_id).exists():
                raise serializers.ValidationError(f"No existe el control {control_id}.")
            if control_id in vistos:
                raise serializers.ValidationError("No se pueden repetir controles en un evento.")
            vistos.add(control_id)
        return value

    def validate_cuentas_contables(self, value):
        for item in value:
            cuenta_id = item.get("cuenta_id")
            if not CuentaContable.objects.filter(cuenta_id=cuenta_id).exists():
                raise serializers.ValidationError(f"No existe la cuenta contable {cuenta_id}.")
        return value

    def validate_distribuciones_linea(self, value):
        total = sum(item["porcentaje"] for item in value)
        if value and total > 100:
            raise serializers.ValidationError("La distribucion por linea no puede superar 100%.")
        return value

    def validate_caracteristicas(self, value):
        ids = [item.get("valor_catalogo_id") for item in value]
        if any(valor_id is None for valor_id in ids):
            raise serializers.ValidationError("Cada característica de catálogo requiere valor_catalogo_id.")
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("No se puede repetir un valor de catálogo en el mismo evento.")
        valores = {
            valor.valor_id: valor
            for valor in CatalogoValor.objects.select_related("catalogo", "parent_valor").filter(
                valor_id__in=ids, activo=True, catalogo__activo=True
            )
        }
        faltantes = sorted(set(ids) - set(valores))
        if faltantes:
            raise serializers.ValidationError(f"Valores de catálogo inexistentes o inactivos: {faltantes}")
        for item in value:
            valor = valores[item["valor_catalogo_id"]]
            if valor.catalogo.codigo_catalogo not in CATALOGOS_EVENTO:
                raise serializers.ValidationError(f"El valor {valor.valor_id} no pertenece a un catálogo permitido para Eventos.")
            texto_libre = (item.get("valor_libre") or "").strip()
            if texto_libre and (valor.catalogo.codigo_catalogo not in {"PRODUCTO", "CANAL"} or not _es_otro(valor)):
                raise serializers.ValidationError("El texto libre solo se permite para el valor OTRO de Producto o Canal.")
        return value

    @staticmethod
    def _validar_sitio(attrs, prefijo, actual):
        tipo = attrs.get(f"{prefijo}_tipo")
        valor_id = attrs.get(f"{prefijo}_valor_id")
        if actual is not None and f"{prefijo}_tipo" in attrs and f"{prefijo}_valor_id" in attrs and tipo is None and valor_id is None:
            return
        if tipo is None and valor_id is None and actual is not None:
            return
        if not tipo or not valor_id:
            raise serializers.ValidationError({prefijo: "Debe indicar tipo e identificador del sitio."})
        codigo_catalogo = TIPOS_SITIO[tipo]
        valor = CatalogoValor.objects.select_related("catalogo", "parent_valor").filter(
            valor_id=valor_id, activo=True, catalogo__codigo_catalogo=codigo_catalogo, catalogo__activo=True
        ).first()
        if valor is None:
            raise serializers.ValidationError({f"{prefijo}_valor_id": "El sitio no corresponde al tipo seleccionado o está inactivo."})
        padre_id = attrs.get(f"{prefijo}_padre_valor_id")
        if tipo == "OFICINA":
            if padre_id is not None or valor.parent_valor_id is not None:
                raise serializers.ValidationError({prefijo: "Una oficina no puede incluir gerencia ni detalle."})
            return
        if padre_id is not None:
            if valor.parent_valor_id != padre_id:
                raise serializers.ValidationError({f"{prefijo}_valor_id": "El detalle no pertenece a la Gerencia/Dirección seleccionada."})
            if not CatalogoValor.objects.filter(valor_id=padre_id, activo=True, catalogo__codigo_catalogo=codigo_catalogo).exists():
                raise serializers.ValidationError({f"{prefijo}_padre_valor_id": "La Gerencia/Dirección seleccionada no es válida."})
        elif valor.parent_valor_id is not None:
            raise serializers.ValidationError({f"{prefijo}_padre_valor_id": "Debe enviar la Gerencia/Dirección del detalle seleccionado."})
        elif valor.hijos.filter(activo=True).exists():
            raise serializers.ValidationError({f"{prefijo}_valor_id": "Seleccione uno de los detalles asociados a esta Gerencia/Dirección."})

    @staticmethod
    def _fecha_hora(fecha, hora, nombre):
        if fecha is None or hora is None:
            raise serializers.ValidationError({nombre: "La fecha y la hora son obligatorias."})
        return datetime.combine(fecha, hora)

    def validate(self, attrs):
        """Reglas que deben ejecutarse también si el cliente omite la interfaz."""
        actual = self.instance

        self._validar_sitio(attrs, "sitio_ocurrencia", actual)
        self._validar_sitio(attrs, "sitio_deteccion", actual)

        def valor(nombre):
            return attrs.get(nombre, getattr(actual, nombre, None))

        inicio = self._fecha_hora(valor("fecha_inicio_evento"), valor("hora_inicio_evento"), "fecha_inicio_evento")
        descubrimiento = self._fecha_hora(
            valor("fecha_descubrimiento_evento"), valor("hora_descubrimiento_evento"), "fecha_descubrimiento_evento"
        )
        fin = self._fecha_hora(
            valor("fecha_finalizacion_evento"), valor("hora_finalizacion_evento"), "fecha_finalizacion_evento"
        )
        registro = datetime.combine(
            getattr(actual, "fecha_registro", None) or timezone.localdate(),
            getattr(actual, "hora_registro", None) or timezone.localtime().time().replace(microsecond=0),
        )
        if inicio > descubrimiento:
            raise serializers.ValidationError({"fecha_inicio_evento": "La fecha y hora de inicio no pueden ser posteriores al descubrimiento."})
        if inicio > registro:
            raise serializers.ValidationError({"fecha_inicio_evento": "La fecha y hora de inicio no pueden ser posteriores al registro."})
        if descubrimiento > registro:
            raise serializers.ValidationError({"fecha_descubrimiento_evento": "La fecha y hora de descubrimiento no pueden ser posteriores al registro."})
        if fin < inicio:
            raise serializers.ValidationError({"fecha_finalizacion_evento": "La fecha y hora de finalización no pueden ser anteriores al inicio."})

        if valor("cuantia_estimada") is None or valor("cuantia_estimada") <= 0:
            raise serializers.ValidationError({"cuantia_estimada": "La cuantía estimada debe ser mayor que cero."})
        if valor("cantidad_casos") is None or valor("cantidad_casos") <= 0:
            raise serializers.ValidationError({"cantidad_casos": "La cantidad de casos debe ser un entero mayor que cero."})
        if not (valor("descripcion_evento") or "").strip():
            raise serializers.ValidationError({"descripcion_evento": "La descripción del evento es obligatoria."})
        if not (valor("nombre_evento") or "").strip():
            raise serializers.ValidationError({"nombre_evento": "El nombre del evento es obligatorio."})

        tipo_perdida = (valor("tipo_perdida") or "").strip().upper().replace("TIPO ", "")
        if tipo_perdida not in {"A", "B", "C"}:
            raise serializers.ValidationError({"tipo_perdida": "Debe seleccionar un tipo de pérdida válido (A, B o C)."})
        bruta = valor("cuantia_perdida_bruta") or 0
        recuperaciones = (valor("cuantia_recuperada_seguros") or 0) + (valor("cuantia_otras_recuperaciones") or 0)
        if any(monto < 0 for monto in (
            bruta, recuperaciones, valor("cuantia_recuperada_seguros") or 0,
            valor("cuantia_otras_recuperaciones") or 0,
        )):
            raise serializers.ValidationError("Las cuantías de pérdida y recuperación no pueden ser negativas.")
        cuentas = attrs.get("cuentas_contables")
        if cuentas is None and actual is not None:
            cuentas = list(actual.cuentas_contables.all())
        if tipo_perdida == "A":
            requeridos = {
                "divisa": valor("divisa"),
                "fecha_contabilizacion_evento": valor("fecha_contabilizacion_evento"),
                "dependencia_contabiliza": valor("dependencia_contabiliza"),
                "numero_comprobante_sub_eventos": valor("numero_comprobante_sub_eventos"),
            }
            faltantes = [campo for campo, dato in requeridos.items() if dato in (None, "")]
            if bruta <= 0:
                raise serializers.ValidationError({"cuantia_perdida_bruta": "Tipo A exige una pérdida bruta mayor que cero."})
            if faltantes or not cuentas:
                raise serializers.ValidationError({"cuentas_contables": "Tipo A exige fecha, comprobante, dependencia, divisa y una cuenta contable de pérdida."})
            if recuperaciones > 0:
                recuperacion_requerida = {
                    "fecha_recuperacion_evento": valor("fecha_recuperacion_evento"),
                    "dependencia_contabiliza_recuperacion": valor("dependencia_contabiliza_recuperacion"),
                    "numero_comprobante_recuperacion": valor("numero_comprobante_recuperacion"),
                }
                if any(dato in (None, "") for dato in recuperacion_requerida.values()):
                    raise serializers.ValidationError({"cuantia_recuperaciones_total": "Una recuperación exige fecha, dependencia y comprobante."})
        elif recuperaciones > 0:
            raise serializers.ValidationError({"cuantia_recuperaciones_total": "Solo los eventos Tipo A pueden registrar recuperaciones."})

        causas = attrs.get("causas")
        controles = attrs.get("controles")
        if causas is None and actual is not None:
            causas = list(actual.evento_causas.all())
        if controles is None and actual is not None:
            controles = list(actual.evento_controles.all())
        if not causas:
            raise serializers.ValidationError({"causas": "Debe asociar al menos una causa."})
        if not controles:
            raise serializers.ValidationError({"controles": "Debe asociar al menos un control."})

        caracteristicas = attrs.get("caracteristicas")
        if caracteristicas is None and actual is not None:
            caracteristicas = list(actual.caracteristicas.all())
        if not caracteristicas:
            raise serializers.ValidationError({"caracteristicas": "Debe informar las selecciones obligatorias del evento."})
        ids_caracteristicas = [
            item.get("valor_catalogo_id") if isinstance(item, dict) else item.valor_catalogo_id
            for item in caracteristicas
        ]
        valores_caracteristicas = {
            valor.valor_id: valor
            for valor in CatalogoValor.objects.select_related("catalogo", "parent_valor").filter(valor_id__in=ids_caracteristicas)
        }
        por_catalogo = {}
        for valor_catalogo in valores_caracteristicas.values():
            por_catalogo.setdefault(valor_catalogo.catalogo.codigo_catalogo, []).append(valor_catalogo)

        def exigir(codigo, cantidad=None, minimo=None):
            valores = por_catalogo.get(codigo, [])
            if cantidad is not None and len(valores) != cantidad:
                raise serializers.ValidationError({"caracteristicas": f"Debe seleccionar exactamente {cantidad} valor(es) de {codigo}."})
            if minimo is not None and len(valores) < minimo:
                raise serializers.ValidationError({"caracteristicas": f"Debe seleccionar al menos {minimo} valor de {codigo}."})
            return valores

        productos = exigir("PRODUCTO", minimo=1)
        canales = exigir("CANAL", minimo=1)
        exigir("SEGMENTO", minimo=1)
        pais = exigir("PAIS", cantidad=1)[0]
        departamento = exigir("DEPARTAMENTO", cantidad=1)[0]
        ciudad = exigir("CIUDAD", cantidad=1)[0]
        linea_n1 = [valor for valor in exigir("LINEA_NEGOCIO", minimo=2) if valor.nivel == 1]
        linea_n2 = [valor for valor in por_catalogo.get("LINEA_NEGOCIO", []) if valor.nivel == 2]
        tipo_n1 = [valor for valor in exigir("TIPO_EVENTO", minimo=3) if valor.nivel == 1]
        tipo_n2 = [valor for valor in por_catalogo.get("TIPO_EVENTO", []) if valor.nivel == 2]
        tipo_n3 = [valor for valor in por_catalogo.get("TIPO_EVENTO", []) if valor.nivel == 3]
        exigir("CLASE_EVENTO", minimo=1)
        if len(linea_n1) != 1 or len(linea_n2) != 1 or linea_n2[0].parent_valor_id != linea_n1[0].valor_id:
            raise serializers.ValidationError({"caracteristicas": "Línea de negocio N2 debe pertenecer a la Línea N1 seleccionada."})
        if (len(tipo_n1), len(tipo_n2), len(tipo_n3)) != (1, 1, 1) or tipo_n2[0].parent_valor_id != tipo_n1[0].valor_id or tipo_n3[0].parent_valor_id != tipo_n2[0].valor_id:
            raise serializers.ValidationError({"caracteristicas": "La clasificación operacional N1, N2 y N3 debe ser una ruta jerárquica válida."})
        if departamento.parent_valor_id != pais.valor_id or ciudad.parent_valor_id != departamento.valor_id:
            raise serializers.ValidationError({"caracteristicas": "País, Departamento y Ciudad no forman una ruta geográfica válida."})
        if len([valor for valor in productos if not _es_otro(valor)]) != 1 or len([valor for valor in productos if _es_otro(valor)]) > 1:
            raise serializers.ValidationError({"caracteristicas": "Debe seleccionar un producto principal y, opcionalmente, un único OTRO producto."})
        if len([valor for valor in canales if not _es_otro(valor)]) != 1 or len([valor for valor in canales if _es_otro(valor)]) > 1:
            raise serializers.ValidationError({"caracteristicas": "Debe seleccionar un canal principal y, opcionalmente, un único OTRO canal."})

        riesgo = valor("riesgo")
        if riesgo:
            causa_ids = [item.get("causa_id") if isinstance(item, dict) else item.causa_id for item in causas]
            causa_ids = [causa_id for causa_id in causa_ids if causa_id is not None]
            invalidas = [
                causa_id for causa_id in causa_ids
                if not (Causa.objects.filter(causa_id=causa_id, riesgo=riesgo).exists()
                        or riesgo.causa_asociaciones.filter(causa_id=causa_id).exists())
            ]
            if invalidas:
                raise serializers.ValidationError({"causas": f"Las causas no pertenecen al riesgo seleccionado: {invalidas}"})
            control_ids = [item.get("control_id") if isinstance(item, dict) else item.control_id for item in controles]
            controles_validos = set(riesgo.controles.values_list("control_id", flat=True)) | set(
                Control.objects.filter(causa_asociaciones__riesgo_causa__riesgo=riesgo).values_list("control_id", flat=True)
            )
            invalidos = sorted(set(control_ids) - controles_validos)
            if invalidos:
                raise serializers.ValidationError({"controles": f"Los controles no pertenecen al riesgo seleccionado: {invalidos}"})
        return attrs
