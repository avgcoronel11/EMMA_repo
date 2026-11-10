"""Business operations for causes and their risk associations."""

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from backend.apps.compartido.models import Auditoria
from backend.apps.riesgos.models import Causa, Riesgo, RiesgoCausa
from backend.apps.riesgos.services.riesgo_service import _obtener_usuario_emma
from backend.apps.riesgos.services.historico_matriz_service import registrar_riesgo_causa
from backend.apps.riesgos.services.codigo_entidad_service import generar_siguiente_codigo_causa


def _auditar(*, entidad, entidad_id, codigo, accion, usuario, anteriores=None, nuevos=None):
    if usuario:
        Auditoria.objects.create(entidad=entidad, entidad_id=entidad_id, codigo_negocio_snapshot=codigo, accion=accion, usuario=usuario, fecha_cambio=timezone.now(), datos_anteriores=anteriores, datos_nuevos=nuevos)


class CausaService:
    @staticmethod
    @transaction.atomic
    def crear_causa(data, *, riesgo_id, request_user=None):
        riesgo = Riesgo.objects.select_for_update().filter(riesgo_id=riesgo_id).first()
        if riesgo is None:
            raise ValidationError({"riesgo_id": "El riesgo no existe."})
        # La causa hereda el contexto organizacional del riesgo seleccionado;
        # no se permite que el formulario lo contradiga.
        data = {
            **data,
            "linea": riesgo.linea,
            "macroproceso": riesgo.macroproceso,
            "dueno": riesgo.dueno_proceso,
        }
        usuario = _obtener_usuario_emma(request_user)
        causa = Causa.objects.create(codigo_causa=generar_siguiente_codigo_causa(), riesgo=riesgo, **data)
        RiesgoCausa.objects.create(riesgo=riesgo, causa=causa)
        registrar_riesgo_causa(riesgo, causa, "ASSOCIATE", usuario=usuario)
        _auditar(entidad="CAUSA", entidad_id=causa.causa_id, codigo=causa.codigo_causa, accion="INSERT", usuario=usuario, nuevos={**data, "riesgo_id": riesgo_id})
        return causa

    @staticmethod
    @transaction.atomic
    def actualizar_causa(causa, data, *, request_user=None):
        anteriores = {campo: getattr(causa, campo) for campo in data}
        for campo, valor in data.items():
            setattr(causa, campo, valor)
        causa.save(update_fields=list(data))
        _auditar(entidad="CAUSA", entidad_id=causa.causa_id, codigo=causa.codigo_causa, accion="UPDATE", usuario=_obtener_usuario_emma(request_user), anteriores=anteriores, nuevos=data)
        return causa

    @staticmethod
    @transaction.atomic
    def asociar(causa, riesgo_id, *, request_user=None):
        riesgo = Riesgo.objects.select_for_update().filter(riesgo_id=riesgo_id).first()
        if riesgo is None:
            raise ValidationError({"riesgo_id": "El riesgo no existe."})
        causa = Causa.objects.select_for_update().get(causa_id=causa.causa_id)
        asociacion, creada = RiesgoCausa.objects.get_or_create(riesgo=riesgo, causa=causa)
        if not creada:
            raise ValidationError({"causa_id": "La causa ya está asociada a este riesgo."})
        usuario = _obtener_usuario_emma(request_user)
        registrar_riesgo_causa(riesgo, causa, "ASSOCIATE", usuario=usuario)
        _auditar(entidad="RIESGO_CAUSA", entidad_id=asociacion.riesgo_causa_id, codigo=causa.codigo_causa, accion="ASSOCIATE", usuario=usuario, nuevos={"riesgo_id": riesgo_id, "causa_id": causa.causa_id})
        return asociacion

    @staticmethod
    @transaction.atomic
    def retirar(asociacion, *, request_user=None):
        # Resolve identifiers first, then always lock the functional context in
        # the same order used by ``asociar``: Riesgo, Causa, association.
        # This serializes version allocation for a riesgo/causa pair.
        asociacion = RiesgoCausa.objects.select_related("riesgo", "causa").get(
            riesgo_causa_id=asociacion.riesgo_causa_id
        )
        riesgo = Riesgo.objects.select_for_update().get(riesgo_id=asociacion.riesgo_id)
        causa = Causa.objects.select_for_update().get(causa_id=asociacion.causa_id)
        asociacion = RiesgoCausa.objects.select_for_update().get(
            riesgo_causa_id=asociacion.riesgo_causa_id
        )
        if not asociacion.causa.riesgo_asociaciones.exclude(riesgo_causa_id=asociacion.riesgo_causa_id).exists():
            raise ValidationError("No se puede retirar la última asociación válida de una causa.")
        datos = {"riesgo_id": asociacion.riesgo_id, "causa_id": asociacion.causa_id}
        usuario = _obtener_usuario_emma(request_user)
        registrar_riesgo_causa(riesgo, causa, "DISASSOCIATE", usuario=usuario)
        _auditar(entidad="RIESGO_CAUSA", entidad_id=asociacion.riesgo_causa_id, codigo=asociacion.causa.codigo_causa, accion="DISASSOCIATE", usuario=usuario, anteriores=datos)
        asociacion.delete()
