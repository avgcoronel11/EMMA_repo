"""Views for Riesgo API endpoints."""

from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from backend.apps.compartido.api.filters import apply_ordering, apply_search
from backend.apps.compartido.api.pagination import ContractPaginationMixin
from backend.apps.riesgos.api.serializers import (
    RiesgoCreateSerializer,
    RiesgoDetailSerializer,
    RiesgoInactivarSerializer,
    RiesgoListSerializer,
    RiesgoUpdateSerializer,
    ValoracionRiesgoSerializer,
)
from backend.apps.riesgos.selectors.riesgo_selector import RiesgoSelector
from backend.apps.riesgos.services.riesgo_service import RiesgoService
from backend.apps.riesgos.models import ValoracionRiesgo


class RiesgoListCreateView(ContractPaginationMixin, APIView):
    serializer_class = RiesgoListSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        estado = request.query_params.get("estado")
        riesgos = RiesgoSelector.obtener_base()
        if estado:
            riesgos = riesgos.filter(estado__iexact=estado)

        codigo_riesgo = request.query_params.get("codigo_riesgo")
        if codigo_riesgo:
            riesgos = riesgos.filter(codigo_riesgo__iexact=codigo_riesgo)

        riesgo_homologado = request.query_params.get("riesgo_homologado")
        if riesgo_homologado:
            riesgos = riesgos.filter(riesgo_homologado__iexact=riesgo_homologado)

        filtros_estructura = {}
        vicepresidencia = request.query_params.get("vicepresidencia")
        if vicepresidencia:
            filtros_estructura["riesgo_procesos__proceso__vicepresidencia__iexact"] = vicepresidencia

        proceso = request.query_params.get("proceso")
        if proceso:
            filtros_estructura["riesgo_procesos__proceso__proceso_nivel0__iexact"] = proceso

        subproceso = request.query_params.get("subproceso")
        if subproceso:
            filtros_estructura["riesgo_procesos__proceso__proceso_nivel1__iexact"] = subproceso

        linea = request.query_params.get("linea")
        if linea:
            filtros_estructura["riesgo_procesos__proceso__linea__iexact"] = linea

        macroproceso = request.query_params.get("macroproceso")
        if macroproceso:
            filtros_estructura["riesgo_procesos__proceso__macroproceso__iexact"] = macroproceso

        if filtros_estructura:
            riesgos = riesgos.filter(**filtros_estructura).distinct()

        dueno_proceso = request.query_params.get("dueno_proceso")
        if dueno_proceso:
            riesgos = riesgos.filter(dueno_proceso__iexact=dueno_proceso)

        riesgos = apply_search(
            riesgos,
            request.query_params.get("search"),
            [
                "nombre_riesgo",
                "codigo_referencia_saro",
                "ciclo",
                "subfactor_riesgo",
                "descripcion_proceso",
                "linea",
                "macroproceso",
                "dueno_proceso",
            ],
        )
        riesgos = apply_ordering(
            riesgos,
            request.query_params.get("ordering"),
            {
                "riesgo_id",
                "codigo_riesgo",
                "nombre_riesgo",
                "estado",
                "severidad_inherente",
                "severidad_residual",
                "fecha_ultima_edicion",
            },
        )
        return self.paginated_response(riesgos, RiesgoListSerializer)

    def post(self, request):
        serializer = RiesgoCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        riesgo = RiesgoService.crear_riesgo(
            serializer.validated_data,
            request_user=request.user,
        )
        detalle = RiesgoSelector.obtener_detalle(riesgo.riesgo_id)
        return Response(RiesgoDetailSerializer(detalle).data, status=status.HTTP_201_CREATED)


class RiesgoDetailView(APIView):
    serializer_class = RiesgoDetailSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, riesgo_id: int):
        riesgo = RiesgoSelector.obtener_detalle(riesgo_id)
        if riesgo is None:
            raise NotFound("Riesgo no encontrado.")
        return Response(RiesgoDetailSerializer(riesgo).data)

    def patch(self, request, riesgo_id: int):
        riesgo = RiesgoSelector.obtener_detalle(riesgo_id)
        if riesgo is None:
            raise NotFound("Riesgo no encontrado.")
        serializer = RiesgoUpdateSerializer(riesgo, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        riesgo = RiesgoService.actualizar_riesgo(riesgo, serializer.validated_data, request_user=request.user)
        return Response(RiesgoDetailSerializer(RiesgoSelector.obtener_detalle(riesgo.riesgo_id)).data)


class RiesgoInactivarView(APIView):
    serializer_class = RiesgoInactivarSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, riesgo_id: int):
        riesgo = RiesgoSelector.obtener_detalle(riesgo_id)
        if riesgo is None:
            raise NotFound("Riesgo no encontrado.")

        serializer = RiesgoInactivarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        riesgo = RiesgoService.inactivar_riesgo(
            riesgo,
            justificacion=serializer.validated_data["justificacion"],
            request_user=request.user,
        )
        detalle = RiesgoSelector.obtener_detalle(riesgo.riesgo_id)
        return Response(RiesgoDetailSerializer(detalle).data)


class RiesgoValoracionesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, riesgo_id: int, valoracion_id: int | None = None):
        if not RiesgoSelector.obtener_detalle(riesgo_id):
            raise NotFound("Riesgo no encontrado.")
        valoraciones = ValoracionRiesgo.objects.filter(riesgo_id=riesgo_id).prefetch_related("controles")
        if valoracion_id is not None:
            valoracion = valoraciones.filter(valoracion_riesgo_id=valoracion_id).first()
            if valoracion is None:
                raise NotFound("Valoración no encontrada.")
            return Response(ValoracionRiesgoSerializer(valoracion).data)
        return Response(ValoracionRiesgoSerializer(valoraciones, many=True).data)


class RiesgoRecalcularResidualView(APIView):
    """Recalcula y persiste el riesgo residual desde los controles activos."""

    permission_classes = [IsAuthenticated]

    def post(self, request, riesgo_id: int):
        riesgo = RiesgoSelector.obtener_detalle(riesgo_id)
        if riesgo is None:
            raise NotFound("Riesgo no encontrado.")
        resultado = RiesgoService.recalcular_residual(riesgo, version=request.data.get("version"))
        if resultado is None:
            from rest_framework.exceptions import ValidationError

            raise ValidationError("El riesgo no tiene valoración inherente completa.")
        detalle = RiesgoSelector.obtener_detalle(riesgo.riesgo_id)
        return Response({"residual": resultado, "riesgo": RiesgoDetailSerializer(detalle).data})
