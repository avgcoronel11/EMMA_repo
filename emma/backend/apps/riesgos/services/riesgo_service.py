"""Business operations for risks."""

from django.db import transaction
from django.utils import timezone

from backend.apps.compartido.api.exceptions import ReglaNegocioError
from backend.apps.catalogos.models import CatalogoValor
from backend.apps.procesos.models import CatProceso
from backend.apps.compartido.models import Auditoria, EntidadCaracteristica
from backend.apps.riesgos.models import Riesgo, RiesgoProceso, RiesgoCausaControl, ValoracionRiesgo, ValoracionRiesgoControl
from backend.apps.riesgos.services.codigo_gr_service import generar_siguiente_codigo_gr
from backend.apps.riesgos.services.valoracion.impacto import calcular_impacto_mayor
from backend.apps.riesgos.services.valoracion.probabilidad import calcular_probabilidad
from backend.apps.riesgos.services.valoracion.residual import calcular_residual
from backend.apps.riesgos.services.valoracion.severidad import calcular_severidad
from backend.apps.usuarios.models import Usuario


def _obtener_usuario_emma(request_user):
    if not request_user or not getattr(request_user, "is_authenticated", False):
        return None

    email = getattr(request_user, "email", None)
    username = getattr(request_user, "username", None)
    queryset = Usuario.objects.filter(estado__iexact="Activo")
    if email:
        usuario = queryset.filter(correo__iexact=email).first()
        if usuario:
            return usuario
    if username:
        return queryset.filter(username__iexact=username).first()
    return None


class RiesgoService:
    @staticmethod
    def controles_para_residual(riesgo):
        """Une relaciones nuevas con la FK histórica sin duplicar controles.

        La FK directa se conserva durante la migración para que los controles
        históricos sin causa identificada continúen participando hasta remediar
        sus asociaciones. El filtro de estado continúa en el algoritmo residual
        existente y no se modifica aquí.
        """
        controles = {control.control_id: control for control in riesgo.controles.all()}
        for relacion in RiesgoCausaControl.objects.filter(riesgo_causa__riesgo=riesgo).select_related("control"):
            controles[relacion.control_id] = relacion.control
        return list(controles.values())

    @staticmethod
    @transaction.atomic
    def actualizar_riesgo(riesgo, validated_data, *, request_user=None):
        valoracion = validated_data.pop("valoracion", None)
        proceso_ids = validated_data.pop("proceso_ids", None)
        proceso_principal_id = validated_data.pop("proceso_principal_id", None)
        if proceso_ids:
            proceso_principal_id = proceso_ids[0]
        usuario = _obtener_usuario_emma(request_user)
        if proceso_ids is not None and proceso_principal_id:
            proceso_principal = CatProceso.objects.get(proceso_id=proceso_principal_id, activo=True)
            validated_data["linea"] = proceso_principal.linea
            validated_data["macroproceso"] = proceso_principal.macroproceso
        anteriores = {campo: getattr(riesgo, campo) for campo in validated_data}
        for campo, valor in validated_data.items():
            setattr(riesgo, campo, valor)
        if valoracion:
            resultado = RiesgoService.calcular_valoracion(valoracion)
            riesgo.prob_inherente_nivel = resultado["probabilidad"]["nivel"]
            riesgo.prob_inherente_etiqueta = resultado["probabilidad"]["etiqueta"]
            riesgo.impacto_inherente_nivel = resultado["impacto"]["nivel"]
            riesgo.impacto_inherente_etiqueta = resultado["impacto"]["etiqueta"]
            riesgo.severidad_inherente = resultado["severidad"]
        riesgo.usuario_ultima_edicion = usuario
        riesgo.fecha_ultima_edicion = timezone.now()
        riesgo.save()
        if proceso_ids is not None:
            RiesgoProceso.objects.filter(riesgo=riesgo).delete()
            for proceso_id in proceso_ids:
                RiesgoProceso.objects.create(riesgo=riesgo, proceso_id=proceso_id, principal=(proceso_id == proceso_principal_id))
        if valoracion:
            RiesgoService.recalcular_residual(riesgo, version=valoracion.get("version"), datos_entrada=valoracion, usuario=usuario)
        if usuario:
            Auditoria.objects.create(entidad="RIESGO", entidad_id=riesgo.riesgo_id, codigo_negocio_snapshot=riesgo.codigo_riesgo,
                accion="UPDATE", usuario=usuario, fecha_cambio=timezone.now(), datos_anteriores=anteriores,
                datos_nuevos=validated_data)
        return riesgo
    @staticmethod
    def _registrar_valoracion(riesgo, *, datos_entrada=None, usuario=None):
        """Persiste una fotografía inmutable de la valoración y sus controles activos."""
        ultima = ValoracionRiesgo.objects.filter(riesgo=riesgo).order_by("-version").values_list("version", flat=True).first()
        valoracion = ValoracionRiesgo.objects.create(
            riesgo=riesgo, version=(ultima or 0) + 1, fecha_valoracion=timezone.now(), usuario=usuario,
            datos_entrada=datos_entrada,
            prob_inherente_nivel=riesgo.prob_inherente_nivel, prob_inherente_etiqueta=riesgo.prob_inherente_etiqueta,
            impacto_inherente_nivel=riesgo.impacto_inherente_nivel, impacto_inherente_etiqueta=riesgo.impacto_inherente_etiqueta,
            severidad_inherente=riesgo.severidad_inherente, prob_residual_nivel=riesgo.prob_residual_nivel,
            prob_residual_etiqueta=riesgo.prob_residual_etiqueta, impacto_residual_nivel=riesgo.impacto_residual_nivel,
            impacto_residual_etiqueta=riesgo.impacto_residual_etiqueta, severidad_residual=riesgo.severidad_residual,
        )
        for control in (control for control in RiesgoService.controles_para_residual(riesgo) if (control.estado or "").casefold() == "activo"):
            efectiva = (control.efectividad or "").casefold() in {"fuerte", "moderado"}
            tipo = (control.tipo_control or "").casefold()
            ValoracionRiesgoControl.objects.create(
                valoracion=valoracion, control=control, control_id_snapshot=control.control_id,
                codigo_control_snapshot=control.codigo_control, nombre_control_snapshot=control.nombre_control,
                estado_snapshot=control.estado, tipo_control_snapshot=control.tipo_control, naturaleza_snapshot=control.naturaleza,
                cumple_diseno_snapshot=control.cumple_diseno, cumple_oper_snapshot=control.cumple_oper,
                falla_vpr_snapshot=control.falla_vpr, efectividad_snapshot=control.efectividad,
                aporte_preventivo=int(efectiva and tipo == "preventivo"),
                aporte_detectivo=int(efectiva and tipo == "detectivo"),
                aporte_correctivo=int(efectiva and tipo == "correctivo"),
            )
        return valoracion
    @staticmethod
    @transaction.atomic
    def recalcular_residual(riesgo: Riesgo, *, version=None, registrar_historico=True, datos_entrada=None, usuario=None):
        """Calcula y persiste residual usando únicamente controles activos."""
        if riesgo.prob_inherente_nivel is None or riesgo.impacto_inherente_nivel is None:
            return None

        resultado = calcular_residual(
            probabilidad_inherente=riesgo.prob_inherente_nivel,
            impacto_inherente=riesgo.impacto_inherente_nivel,
            controles=RiesgoService.controles_para_residual(riesgo),
            version=version,
        )
        riesgo.prob_residual_nivel = resultado["probabilidad"]["nivel"]
        riesgo.prob_residual_etiqueta = resultado["probabilidad"]["etiqueta"]
        riesgo.impacto_residual_nivel = resultado["impacto"]["nivel"]
        riesgo.impacto_residual_etiqueta = resultado["impacto"]["etiqueta"]
        riesgo.severidad_residual = resultado["severidad"]
        riesgo.save(
            update_fields=[
                "prob_residual_nivel",
                "prob_residual_etiqueta",
                "impacto_residual_nivel",
                "impacto_residual_etiqueta",
                "severidad_residual",
            ]
        )
        if registrar_historico:
            RiesgoService._registrar_valoracion(riesgo, datos_entrada=datos_entrada, usuario=usuario)
        return resultado

    @staticmethod
    def calcular_valoracion(data: dict):
        version = data.get("version")
        probabilidad_resultado = calcular_probabilidad(version=version, **data["probabilidad"])

        impacto_data = data["impacto"]
        impacto_resultado = calcular_impacto_mayor(
            impactos=impacto_data["impactos"],
            version=version,
        )

        severidad_resultado = calcular_severidad(
            probabilidad_etiqueta=probabilidad_resultado["etiqueta"],
            impacto_etiqueta=impacto_resultado["etiqueta"],
            version=version,
        )

        resultado = {
            "probabilidad": probabilidad_resultado,
            "impacto": impacto_resultado,
            "severidad": severidad_resultado["severidad"],
        }

        return resultado

    @staticmethod
    @transaction.atomic
    def crear_riesgo(validated_data: dict, *, request_user=None):
        proceso_ids = validated_data.pop("proceso_ids", [])
        proceso_principal_id = validated_data.pop("proceso_principal_id", None)
        if proceso_ids:
            proceso_principal_id = proceso_ids[0]
        caracteristicas = validated_data.pop("caracteristicas", [])
        valoracion = validated_data.pop("valoracion", None)

        if proceso_principal_id:
            proceso_principal = CatProceso.objects.get(proceso_id=proceso_principal_id, activo=True)
            validated_data["linea"] = proceso_principal.linea
            validated_data["macroproceso"] = proceso_principal.macroproceso

        if not validated_data.get("estado"):
            validated_data["estado"] = "Activo"

        usuario_emma = _obtener_usuario_emma(request_user)
        if usuario_emma:
            validated_data["usuario_ultima_edicion"] = usuario_emma
        validated_data["fecha_ultima_edicion"] = timezone.now()

        if valoracion:
            resultado = RiesgoService.calcular_valoracion(valoracion)
            probabilidad = valoracion["probabilidad"]
            impactos = valoracion["impacto"]["impactos"]
            validated_data.update(
                {
                    "exposicion": probabilidad["exposicion"],
                    "complejidad": probabilidad["complejidad"],
                    "condiciones_entorno": probabilidad["condiciones_entorno"],
                    "grado_ocurrencia": probabilidad["grado_ocurrencia"],
                    "eventos_riesgo": probabilidad["eventos_riesgo"],
                    "poblacion_expuesta": probabilidad["poblacion_expuesta"],
                    "impacto_legal": impactos["Impacto Legal"],
                    "impacto_reputacional": impactos["Impacto Reputacional"],
                    "impacto_servicio_cliente": impactos["Impacto servicio al cliente"],
                    "impacto_informacion": impactos["Información"],
                    "impacto_continuidad": impactos["Continuidad"],
                    "impacto_contagio": impactos["Contagio"],
                    "impacto_financiero": impactos["Financiero"],
                    "prob_inherente_nivel": resultado["probabilidad"]["nivel"],
                    "prob_inherente_etiqueta": resultado["probabilidad"]["etiqueta"],
                    "impacto_inherente_nivel": resultado["impacto"]["nivel"],
                    "impacto_inherente_etiqueta": resultado["impacto"]["etiqueta"],
                    "severidad_inherente": resultado["severidad"],
                }
            )
        consecutivo_gr, codigo_riesgo = generar_siguiente_codigo_gr()
        validated_data["consecutivo_gr"] = consecutivo_gr
        validated_data["codigo_riesgo"] = codigo_riesgo
        riesgo = Riesgo.objects.create(**validated_data)

        for proceso_id in proceso_ids:
            RiesgoProceso.objects.create(
                riesgo=riesgo,
                proceso_id=proceso_id,
                principal=(proceso_id == proceso_principal_id),
            )

        for index, item in enumerate(caracteristicas, start=1):
            valor_catalogo_id = item.get("valor_catalogo_id")
            valor_catalogo = None
            if valor_catalogo_id is not None:
                valor_catalogo = CatalogoValor.objects.get(valor_id=valor_catalogo_id)
            EntidadCaracteristica.objects.create(
                riesgo=riesgo,
                valor_catalogo=valor_catalogo,
                valor_libre=item.get("valor_libre"),
                valor_snapshot=item.get("valor_snapshot") or (valor_catalogo.descripcion if valor_catalogo else None),
                orden=item.get("orden") or index,
                activo=True,
            )

        if valoracion:
            RiesgoService.recalcular_residual(riesgo, version=valoracion.get("version"), datos_entrada=valoracion, usuario=usuario_emma)

        if usuario_emma:
            Auditoria.objects.create(
                entidad="RIESGO",
                entidad_id=riesgo.riesgo_id,
                codigo_negocio_snapshot=riesgo.codigo_riesgo,
                accion="INSERT",
                usuario=usuario_emma,
                fecha_cambio=timezone.now(),
                motivo_modificacion=riesgo.comentario_ultima_edicion,
                datos_nuevos={"codigo_riesgo": riesgo.codigo_riesgo, "estado": riesgo.estado},
            )

        return riesgo

    @staticmethod
    @transaction.atomic
    def inactivar_riesgo(riesgo: Riesgo, *, justificacion: str, request_user=None):
        justificacion = (justificacion or "").strip()
        if not justificacion:
            raise ReglaNegocioError("La justificacion es requerida.")

        usuario_emma = _obtener_usuario_emma(request_user)
        datos_anteriores = {"estado": riesgo.estado}

        riesgo.estado = "Inactivo"
        riesgo.justificacion_inactivacion = justificacion
        riesgo.fecha_inactivacion = timezone.localdate()
        riesgo.usuario_inactivacion = usuario_emma
        riesgo.usuario_ultima_edicion = usuario_emma
        riesgo.fecha_ultima_edicion = timezone.now()
        riesgo.comentario_ultima_edicion = justificacion
        riesgo.save(
            update_fields=[
                "estado",
                "justificacion_inactivacion",
                "fecha_inactivacion",
                "usuario_inactivacion",
                "usuario_ultima_edicion",
                "fecha_ultima_edicion",
                "comentario_ultima_edicion",
            ]
        )

        if usuario_emma:
            Auditoria.objects.create(
                entidad="RIESGO",
                entidad_id=riesgo.riesgo_id,
                codigo_negocio_snapshot=riesgo.codigo_riesgo,
                accion="INACTIVATE",
                usuario=usuario_emma,
                fecha_cambio=timezone.now(),
                motivo_modificacion=justificacion,
                datos_anteriores=datos_anteriores,
                datos_nuevos={"estado": riesgo.estado},
            )

        return riesgo
