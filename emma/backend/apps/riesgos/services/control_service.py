"""Business operations and Tarea 3 evaluations for controls."""

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from backend.apps.riesgos.services.valoracion.utils import normalizar_texto
from backend.apps.compartido.models import Auditoria, EntidadCaracteristica
from backend.apps.riesgos.models import Causa, Control, ControlChecklist, ControlCuentaContable, Riesgo, RiesgoCausa, RiesgoCausaControl
from backend.apps.riesgos.services.riesgo_service import _obtener_usuario_emma
from backend.apps.riesgos.services.historico_matriz_service import registrar_evaluacion, registrar_riesgo_causa_control
from backend.apps.riesgos.services.codigo_entidad_service import generar_siguiente_codigo_control


RESPUESTA_SI = "Sí"
RESPUESTA_NO = "No"
RESPUESTA_NA = "NA"
RESPUESTAS_DISENO = ("d1", "d2", "d3", "d4")
RESPUESTAS_OPERATIVIDAD = ("o1", "o2", "o3", "o4", "o5")


def _extraer_relaciones(data):
    return {
        "sistemas": data.pop("sistema_valor_ids", None),
        "coso": data.pop("principio_coso_valor_ids", None),
        "cuentas": data.pop("cuenta_ids", None),
        "aserciones": data.pop("aserciones", None),
        "atributos": data.pop("atributos", None),
        "riesgos": data.pop("riesgos_control", None),
    }


def _guardar_relaciones(control, relaciones):
    for valores, codigo_catalogo in ((relaciones["sistemas"], "SISTEMA"), (relaciones["coso"], "PRINCIPIO_COSO")):
        if valores is not None:
            EntidadCaracteristica.objects.filter(control=control, valor_catalogo__catalogo__codigo_catalogo=codigo_catalogo).delete()
            EntidadCaracteristica.objects.bulk_create([
                EntidadCaracteristica(control=control, valor_catalogo_id=valor_id, orden=indice, activo=True)
                for indice, valor_id in enumerate(valores, start=1)
            ])
    if relaciones["cuentas"] is not None:
        ControlCuentaContable.objects.filter(control=control).delete()
        ControlCuentaContable.objects.bulk_create([ControlCuentaContable(control=control, cuenta_id=cuenta_id) for cuenta_id in relaciones["cuentas"]])
    for valores, tipo in ((relaciones["aserciones"], "ASERCION"), (relaciones["atributos"], "ATRIBUTO"), (relaciones["riesgos"], "RIESGO")):
        if valores is not None:
            ControlChecklist.objects.filter(control=control, tipo=tipo).delete()
            ControlChecklist.objects.bulk_create([ControlChecklist(control=control, tipo=tipo, valor=valor) for valor in dict.fromkeys(valores)])


def _normalizar_clave(value):
    return "".join(char for char in (normalizar_texto(value) or "").casefold() if char.isalnum())


def _efectividad(tipo_control, naturaleza, falla_vpr):
    """Tabla de efectividad de Tarea 3, Datos complementarios Q:T."""
    if _normalizar_clave(falla_vpr) != "no":
        return "Débil"

    tipo = _normalizar_clave(tipo_control)
    naturaleza_normalizada = _normalizar_clave(naturaleza)
    matriz = {
        ("correctivo", "manual"): "Débil",
        ("correctivo", "dependientedeti"): "Moderado",
        ("correctivo", "automatizado"): "Moderado",
        ("correctivo", "automatico"): "Moderado",
        ("preventivo", "manual"): "Moderado",
        ("preventivo", "dependientedeti"): "Moderado",
        ("preventivo", "automatizado"): "Fuerte",
        ("preventivo", "automatico"): "Fuerte",
        ("detectivo", "manual"): "Moderado",
        ("detectivo", "dependientedeti"): "Moderado",
        ("detectivo", "automatizado"): "Fuerte",
        ("detectivo", "automatico"): "Fuerte",
    }
    return matriz.get((tipo, naturaleza_normalizada), "Débil")


def recalcular_evaluacion(control):
    """Recalcula solo cuando las nueve respuestas primarias están completas."""
    respuestas = {campo: getattr(control, campo) for campo in (*RESPUESTAS_DISENO, *RESPUESTAS_OPERATIVIDAD)}
    if any(valor is None for valor in respuestas.values()):
        return False

    control.cumple_diseno = (
        RESPUESTA_SI if all(respuestas[campo] == RESPUESTA_SI for campo in RESPUESTAS_DISENO) else RESPUESTA_NO
    )
    control.cumple_oper = (
        RESPUESTA_SI
        if (
            respuestas["o1"] == RESPUESTA_NO
            and respuestas["o2"] == RESPUESTA_SI
            and respuestas["o3"] == RESPUESTA_SI
            and respuestas["o4"] == RESPUESTA_SI
            and respuestas["o5"] in (RESPUESTA_NO, RESPUESTA_NA)
        )
        else RESPUESTA_NO
    )
    control.falla_vpr = (
        RESPUESTA_NO
        if control.cumple_diseno == RESPUESTA_SI and control.cumple_oper == RESPUESTA_SI
        else RESPUESTA_SI
    )
    control.efectividad = _efectividad(control.tipo_control, control.naturaleza, control.falla_vpr)
    return True


class ControlService:
    @staticmethod
    @transaction.atomic
    def crear_control(data, *, riesgo_causa, request_user=None):
        relaciones = _extraer_relaciones(data)
        riesgo_causa = RiesgoCausa.objects.select_related("riesgo", "causa").get(
            riesgo_causa_id=riesgo_causa.riesgo_causa_id
        )
        # Lock the shared context in deterministic order before allocating the
        # first history version for the new triplet.
        Riesgo.objects.select_for_update().get(riesgo_id=riesgo_causa.riesgo_id)
        Causa.objects.select_for_update().get(causa_id=riesgo_causa.causa_id)
        riesgo_causa = RiesgoCausa.objects.select_for_update().select_related("riesgo", "causa").get(
            riesgo_causa_id=riesgo_causa.riesgo_causa_id
        )
        control = Control.objects.create(codigo_control=generar_siguiente_codigo_control(), riesgo=riesgo_causa.riesgo, **data)
        _guardar_relaciones(control, relaciones)
        asociacion = RiesgoCausaControl.objects.create(riesgo_causa=riesgo_causa, control=control)
        usuario = _obtener_usuario_emma(request_user)
        registrar_riesgo_causa_control(riesgo_causa.riesgo, riesgo_causa.causa, control, "ASSOCIATE", usuario=usuario)
        if usuario:
            Auditoria.objects.create(entidad="CONTROL", entidad_id=control.control_id, codigo_negocio_snapshot=control.codigo_control, accion="INSERT", usuario=usuario, fecha_cambio=timezone.now(), datos_nuevos={**data, "riesgo_id": riesgo_causa.riesgo_id, "causa_id": riesgo_causa.causa_id})
        return control, asociacion

    @staticmethod
    @transaction.atomic
    def asociar(control, riesgo_causa, *, request_user=None):
        riesgo_causa = RiesgoCausa.objects.select_related("riesgo", "causa").get(
            riesgo_causa_id=riesgo_causa.riesgo_causa_id
        )
        Riesgo.objects.select_for_update().get(riesgo_id=riesgo_causa.riesgo_id)
        Causa.objects.select_for_update().get(causa_id=riesgo_causa.causa_id)
        control = Control.objects.select_for_update().get(control_id=control.control_id)
        riesgo_causa = RiesgoCausa.objects.select_for_update().select_related("riesgo", "causa").get(
            riesgo_causa_id=riesgo_causa.riesgo_causa_id
        )
        asociacion, creada = RiesgoCausaControl.objects.get_or_create(riesgo_causa=riesgo_causa, control=control)
        if not creada:
            raise ValidationError({"control_id": "El control ya está asociado a esta causa dentro del riesgo."})
        usuario = _obtener_usuario_emma(request_user)
        registrar_riesgo_causa_control(riesgo_causa.riesgo, riesgo_causa.causa, control, "ASSOCIATE", usuario=usuario)
        if usuario:
            Auditoria.objects.create(entidad="RIESGO_CAUSA_CONTROL", entidad_id=asociacion.riesgo_causa_control_id, codigo_negocio_snapshot=control.codigo_control, accion="ASSOCIATE", usuario=usuario, fecha_cambio=timezone.now(), datos_nuevos={"riesgo_id": riesgo_causa.riesgo_id, "causa_id": riesgo_causa.causa_id, "control_id": control.control_id})
        return asociacion

    @staticmethod
    @transaction.atomic
    def retirar(asociacion, *, request_user=None):
        asociacion = RiesgoCausaControl.objects.select_related(
            "riesgo_causa__riesgo", "riesgo_causa__causa", "control"
        ).get(riesgo_causa_control_id=asociacion.riesgo_causa_control_id)
        Riesgo.objects.select_for_update().get(riesgo_id=asociacion.riesgo_causa.riesgo_id)
        Causa.objects.select_for_update().get(causa_id=asociacion.riesgo_causa.causa_id)
        Control.objects.select_for_update().get(control_id=asociacion.control_id)
        RiesgoCausa.objects.select_for_update().get(riesgo_causa_id=asociacion.riesgo_causa_id)
        asociacion = RiesgoCausaControl.objects.select_for_update().select_related(
            "riesgo_causa__riesgo", "riesgo_causa__causa", "control"
        ).get(riesgo_causa_control_id=asociacion.riesgo_causa_control_id)
        usuario = _obtener_usuario_emma(request_user)
        datos = {
            "riesgo_id": asociacion.riesgo_causa.riesgo_id,
            "causa_id": asociacion.riesgo_causa.causa_id,
            "control_id": asociacion.control_id,
        }
        registrar_riesgo_causa_control(
            asociacion.riesgo_causa.riesgo,
            asociacion.riesgo_causa.causa,
            asociacion.control,
            "DISASSOCIATE",
            usuario=usuario,
        )
        if usuario:
            Auditoria.objects.create(
                entidad="RIESGO_CAUSA_CONTROL",
                entidad_id=asociacion.riesgo_causa_control_id,
                codigo_negocio_snapshot=asociacion.control.codigo_control,
                accion="DISASSOCIATE",
                usuario=usuario,
                fecha_cambio=timezone.now(),
                datos_anteriores=datos,
            )
        asociacion.delete()

    @staticmethod
    @transaction.atomic
    def actualizar_control(control, data, *, request_user=None):
        relaciones = _extraer_relaciones(data)
        anteriores = {campo: getattr(control, campo) for campo in data}
        for campo, valor in data.items():
            setattr(control, campo, valor)
        if data:
            control.save(update_fields=list(data))
        _guardar_relaciones(control, relaciones)
        usuario = _obtener_usuario_emma(request_user)
        if usuario:
            Auditoria.objects.create(entidad="CONTROL", entidad_id=control.control_id, codigo_negocio_snapshot=control.codigo_control, accion="UPDATE", usuario=usuario, fecha_cambio=timezone.now(), datos_anteriores=anteriores, datos_nuevos=data)
        return control

    @staticmethod
    @transaction.atomic
    def registrar_evaluacion(control, respuestas, *, request_user=None):
        if not respuestas:
            raise ValidationError("Debe enviar al menos una respuesta de evaluación.")
        control = Control.objects.select_for_update().get(control_id=control.control_id)
        anteriores = {campo: getattr(control, campo) for campo in respuestas}
        for campo, valor in respuestas.items():
            setattr(control, campo, valor)

        completa = recalcular_evaluacion(control)
        campos = list(respuestas)
        if completa:
            campos.extend(["cumple_diseno", "cumple_oper", "falla_vpr", "efectividad"])
        control.save(update_fields=campos)
        usuario = _obtener_usuario_emma(request_user)
        registrar_evaluacion(control, usuario=usuario)
        if usuario:
            Auditoria.objects.create(entidad="CONTROL", entidad_id=control.control_id, codigo_negocio_snapshot=control.codigo_control, accion="EVALUATE", usuario=usuario, fecha_cambio=timezone.now(), datos_anteriores=anteriores, datos_nuevos={campo: getattr(control, campo) for campo in campos})
        return control, completa
