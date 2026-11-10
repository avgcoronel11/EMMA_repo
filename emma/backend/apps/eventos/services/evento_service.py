"""Write services for event risk workflows."""

from datetime import timedelta
from uuid import uuid4

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from backend.apps.compartido.models import Auditoria, EntidadCaracteristica
from backend.apps.eventos.models import (
    EventoCausa,
    EventoControl,
    EventoCuentaContable,
    EventoDistribucionLinea,
    EventoRiesgo,
)
from backend.apps.catalogos.models import CatalogoValor, CuentaContable
from backend.apps.riesgos.models import Causa, Control


class EventoService:
    NESTED_KEYS = {
        "causas",
        "controles",
        "cuentas_contables",
        "distribuciones_linea",
        "caracteristicas",
        "sitio_ocurrencia_tipo",
        "sitio_ocurrencia_valor_id",
        "sitio_ocurrencia_padre_valor_id",
        "sitio_deteccion_tipo",
        "sitio_deteccion_valor_id",
        "sitio_deteccion_padre_valor_id",
    }

    @staticmethod
    @transaction.atomic
    def crear_evento(validated_data, *, usuario):
        if usuario is None:
            raise ValidationError({"usuario_registro_id": "No se encontró un usuario EMMA activo para la identidad autenticada."})
        nested_data = EventoService._pop_nested(validated_data)
        EventoService._aplicar_sitios(validated_data, nested_data)
        EventoService._aplicar_snapshots_caracteristicas(validated_data, nested_data)
        EventoService._completar_datos_servidor(validated_data, usuario=usuario)
        evento = EventoRiesgo.objects.create(**validated_data)
        EventoService._crear_detalles(evento, nested_data)
        Auditoria.objects.create(
            entidad="EVENTO_RIESGO", entidad_id=evento.evento_id,
            codigo_negocio_snapshot=evento.id_ocurrencia, accion="INSERT", usuario=usuario,
            fecha_cambio=timezone.now(), datos_nuevos={"id_ocurrencia": evento.id_ocurrencia, "riesgo_id": evento.riesgo_id},
        )
        return evento

    @staticmethod
    @transaction.atomic
    def actualizar_evento(evento, validated_data, *, usuario):
        if usuario is None:
            raise ValidationError({"usuario_registro_id": "No se encontró un usuario EMMA activo para la identidad autenticada."})
        nested_data = EventoService._pop_nested(validated_data)
        EventoService._aplicar_sitios(validated_data, nested_data)
        EventoService._aplicar_snapshots_caracteristicas(validated_data, nested_data)
        anteriores = {campo: getattr(evento, campo) for campo in validated_data}

        for field, value in validated_data.items():
            setattr(evento, field, value)
        EventoService._completar_snapshots(evento)
        EventoService._calcular_perdida_neta(evento)
        evento.save()

        EventoService._reemplazar_detalles(evento, nested_data)
        Auditoria.objects.create(
            entidad="EVENTO_RIESGO", entidad_id=evento.evento_id,
            codigo_negocio_snapshot=evento.id_ocurrencia, accion="UPDATE", usuario=usuario,
            fecha_cambio=timezone.now(), datos_anteriores=anteriores,
            datos_nuevos={campo: getattr(evento, campo) for campo in validated_data},
        )
        return evento

    @staticmethod
    def _completar_datos_servidor(data, *, usuario):
        ahora = timezone.localtime()
        data["id_ocurrencia"] = uuid4().hex
        data["usuario_registro"] = usuario
        data["fecha_registro"] = ahora.date()
        data["hora_registro"] = ahora.time().replace(microsecond=0)
        EventoService._completar_snapshots_data(data)
        if (data.get("tipo_perdida") or "").strip().upper().replace("TIPO ", "") == "B":
            data["divisa"] = "N/A"
        data["cuantia_recuperaciones_total"] = (
            (data.get("cuantia_recuperada_seguros") or 0)
            + (data.get("cuantia_otras_recuperaciones") or 0)
        )
        EventoService._calcular_perdida_neta_data(data)

    @staticmethod
    def _completar_snapshots(evento):
        data = {"riesgo": evento.riesgo}
        EventoService._completar_snapshots_data(data)
        for campo, valor in data.items():
            if campo != "riesgo":
                setattr(evento, campo, valor)

    @staticmethod
    def _completar_snapshots_data(data):
        riesgo = data["riesgo"]
        proceso = riesgo.riesgo_procesos.select_related("proceso").order_by("-principal", "proceso_id").first()
        proceso = proceso.proceso if proceso else None
        data.update({
            "codigo_riesgo_snapshot": riesgo.codigo_riesgo,
            "descripcion_riesgo_snapshot": riesgo.nombre_riesgo,
            "riesgo_generico_snapshot": riesgo.riesgo_generico.codigo if riesgo.riesgo_generico else riesgo.riesgo_homologado,
            "riesgo_asociado_display": f"{riesgo.codigo_riesgo} - {riesgo.nombre_riesgo}",
            "vicepresidencia_snapshot": proceso.vicepresidencia if proceso else None,
            "proceso_snapshot": proceso.proceso_nivel0 if proceso else None,
            "subproceso_snapshot": proceso.proceso_nivel1 if proceso else None,
            "gerencia_duena_snapshot": riesgo.dueno_proceso,
        })

    @staticmethod
    def _calcular_perdida_neta(evento):
        evento.cuantia_recuperaciones_total = (
            (evento.cuantia_recuperada_seguros or 0) + (evento.cuantia_otras_recuperaciones or 0)
        )
        data = {
            "cuantia_perdida_bruta": evento.cuantia_perdida_bruta,
            "cuantia_recuperaciones_total": evento.cuantia_recuperaciones_total,
        }
        EventoService._calcular_perdida_neta_data(data)
        evento.cuantia_perdida_neta = data["cuantia_perdida_neta"]

    @staticmethod
    def _calcular_perdida_neta_data(data):
        bruta = data.get("cuantia_perdida_bruta") or 0
        recuperaciones = data.get("cuantia_recuperaciones_total") or 0
        data["cuantia_perdida_neta"] = bruta - recuperaciones

    @staticmethod
    def excede_plazo_registro(evento):
        """Cuenta lunes a viernes; el aviso no bloquea el registro (RC-08)."""
        fecha = evento.fecha_descubrimiento_evento + timedelta(days=1)
        habiles = 0
        while fecha <= evento.fecha_registro:
            if fecha.weekday() < 5:
                habiles += 1
            fecha += timedelta(days=1)
        return habiles > 15

    @staticmethod
    def _pop_nested(validated_data):
        return {key: validated_data.pop(key) for key in list(validated_data.keys()) if key in EventoService.NESTED_KEYS}

    @staticmethod
    def _crear_detalles(evento, nested_data):
        for item in nested_data.get("causas", []):
            EventoCausa.objects.create(evento=evento, **EventoService._normalizar_causa(item))
        for item in nested_data.get("controles", []):
            EventoControl.objects.create(evento=evento, **EventoService._normalizar_control(item))
        for item in nested_data.get("cuentas_contables", []):
            EventoCuentaContable.objects.create(evento=evento, **EventoService._normalizar_cuenta(item))
        for item in nested_data.get("distribuciones_linea", []):
            EventoDistribucionLinea.objects.create(evento=evento, **item)
        for item in nested_data.get("caracteristicas", []):
            EntidadCaracteristica.objects.create(evento=evento, **EventoService._normalizar_caracteristica(item))

    @staticmethod
    def _reemplazar_detalles(evento, nested_data):
        if "causas" in nested_data:
            evento.evento_causas.all().delete()
            for item in nested_data["causas"]:
                EventoCausa.objects.create(evento=evento, **EventoService._normalizar_causa(item))

        if "controles" in nested_data:
            evento.evento_controles.all().delete()
            for item in nested_data["controles"]:
                EventoControl.objects.create(evento=evento, **EventoService._normalizar_control(item))

        if "cuentas_contables" in nested_data:
            evento.cuentas_contables.all().delete()
            for item in nested_data["cuentas_contables"]:
                EventoCuentaContable.objects.create(evento=evento, **EventoService._normalizar_cuenta(item))

        if "distribuciones_linea" in nested_data:
            evento.distribuciones_linea.all().delete()
            for item in nested_data["distribuciones_linea"]:
                EventoDistribucionLinea.objects.create(evento=evento, **item)

        if "caracteristicas" in nested_data:
            evento.caracteristicas.all().delete()
            for item in nested_data["caracteristicas"]:
                EntidadCaracteristica.objects.create(evento=evento, **EventoService._normalizar_caracteristica(item))

    @staticmethod
    def _aplicar_sitios(data, nested_data):
        for prefijo, campo in (("sitio_ocurrencia", "sitio_ocurrencia"), ("sitio_deteccion", "sitio_deteccion")):
            id_key = f"{prefijo}_valor_id"
            if id_key not in nested_data:
                continue
            valor_id = nested_data[id_key]
            data[f"{prefijo}_valor"] = CatalogoValor.objects.get(valor_id=valor_id) if valor_id is not None else None
            data[campo] = CatalogoValor.objects.get(valor_id=valor_id).descripcion if valor_id is not None else None

    @staticmethod
    def _aplicar_snapshots_caracteristicas(data, nested_data):
        caracteristicas = nested_data.get("caracteristicas")
        if caracteristicas is None:
            return
        valores = CatalogoValor.objects.select_related("catalogo").filter(
            valor_id__in=[item["valor_catalogo_id"] for item in caracteristicas]
        )
        for valor in valores:
            codigo = valor.catalogo.codigo_catalogo
            if codigo == "PAIS":
                data["pais_evento"] = valor.descripcion
            elif codigo == "DEPARTAMENTO":
                data["departamento_evento"] = valor.descripcion
            elif codigo == "CIUDAD":
                data["ciudad_evento"] = valor.descripcion
            elif codigo == "LINEA_NEGOCIO" and valor.nivel == 1:
                data["linea_negocio_1"] = valor.descripcion
            elif codigo == "LINEA_NEGOCIO" and valor.nivel == 2:
                data["linea_negocio_2"] = valor.descripcion

    @staticmethod
    def _normalizar_caracteristica(item):
        item = dict(item)
        valor = CatalogoValor.objects.get(valor_id=item["valor_catalogo_id"])
        texto_libre = (item.get("valor_libre") or "").strip() or None
        item.update({
            "valor_snapshot": f"{valor.descripcion}: {texto_libre}" if texto_libre else valor.descripcion,
            "valor_libre": texto_libre,
            "activo": True,
        })
        return item

    @staticmethod
    def _normalizar_causa(item):
        item = dict(item)
        causa_id = item.get("causa_id")
        if causa_id is None:
            item.update({
                "codigo_causa_snapshot": "N/A",
                "descripcion_causa_snapshot": item["descripcion_causa_snapshot"].strip(),
                "es_causa_libre": True,
            })
            return item
        causa = Causa.objects.get(causa_id=causa_id)
        item.update({
            "codigo_causa_snapshot": causa.codigo_causa,
            "descripcion_causa_snapshot": causa.descripcion_causa,
            "es_causa_libre": False,
        })
        return item

    @staticmethod
    def _normalizar_control(item):
        item = dict(item)
        control = Control.objects.get(control_id=item["control_id"])
        item.update({
            "codigo_control_snapshot": control.codigo_control,
            "descripcion_control_snapshot": control.descripcion_control,
        })
        return item

    @staticmethod
    def _normalizar_cuenta(item):
        item = dict(item)
        cuenta = CuentaContable.objects.get(cuenta_id=item["cuenta_id"])
        item.update({
            "codigo_cuenta_snapshot": cuenta.cuenta_6 or cuenta.cuenta_10 or cuenta.clave_homologacion,
            "descripcion_cuenta_snapshot": cuenta.descripcion,
        })
        return item
