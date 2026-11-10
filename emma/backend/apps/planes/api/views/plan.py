"""Views for action plan API endpoints."""

from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.apps.compartido.api.filters import apply_ordering, apply_search
from backend.apps.compartido.api.pagination import ContractPaginationMixin
from backend.apps.planes.api.serializers.plan import (
    PlanCreateUpdateSerializer,
    PlanDetailSerializer,
    PlanListSerializer,
)
from backend.apps.planes.selectors.plan_selector import PlanSelector
from backend.apps.planes.services.plan_service import PlanService


class PlanListCreateView(ContractPaginationMixin, APIView):
    serializer_class = PlanListSerializer

    def get(self, request):
        planes = PlanSelector.obtener_base()
        estado = request.query_params.get("estado") or request.query_params.get("estado_plan")
        evento_id = request.query_params.get("evento_id")

        if estado:
            planes = planes.filter(estado_plan__iexact=estado)
        if evento_id:
            planes = planes.filter(evento_id=evento_id)

        search = request.query_params.get("search") or request.query_params.get("q")
        planes = apply_search(
            planes,
            search,
            ["codigo_plan", "nombre_evento_snapshot", "descripcion_accion", "tipo_accion", "estado_plan"],
        )
        planes = apply_ordering(
            planes,
            request.query_params.get("ordering"),
            {
                "plan_id",
                "codigo_plan",
                "fecha_inicio",
                "fecha_cierre",
                "estado_plan",
                "avance_plan",
            },
        )
        return self.paginated_response(planes, PlanListSerializer)

    def post(self, request):
        serializer = PlanCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plan = PlanService.crear_plan(serializer.validated_data)
        detalle = PlanSelector.obtener_detalle(plan.plan_id)
        return Response(PlanDetailSerializer(detalle).data, status=status.HTTP_201_CREATED)


class PlanDetailView(APIView):
    serializer_class = PlanDetailSerializer

    def get(self, request, plan_id: int):
        plan = PlanSelector.obtener_detalle(plan_id)
        if plan is None:
            raise NotFound("Plan no encontrado.")
        return Response(PlanDetailSerializer(plan).data)

    def patch(self, request, plan_id: int):
        plan = PlanSelector.obtener_detalle(plan_id)
        if plan is None:
            raise NotFound("Plan no encontrado.")

        serializer = PlanCreateUpdateSerializer(plan, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        plan = PlanService.actualizar_plan(plan, serializer.validated_data)
        detalle = PlanSelector.obtener_detalle(plan.plan_id)
        return Response(PlanDetailSerializer(detalle).data)
