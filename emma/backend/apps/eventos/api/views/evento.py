"""Views for event risk API endpoints."""

from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.apps.compartido.api.filters import apply_ordering, apply_search
from backend.apps.compartido.api.pagination import ContractPaginationMixin
from backend.apps.eventos.api.serializers.evento import (
    EventoCreateUpdateSerializer,
    EventoDetailSerializer,
    EventoListSerializer,
)
from backend.apps.eventos.selectors.evento_selector import EventoSelector
from backend.apps.eventos.services.evento_service import EventoService
from backend.apps.riesgos.services.riesgo_service import _obtener_usuario_emma
from rest_framework.permissions import IsAuthenticated


class EventoListCreateView(ContractPaginationMixin, APIView):
    serializer_class = EventoListSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        eventos = EventoSelector.obtener_base()
        estado = request.query_params.get("estado") or request.query_params.get("estado_evento")
        if estado:
            eventos = eventos.filter(estado_evento__iexact=estado)

        search = request.query_params.get("search") or request.query_params.get("q")
        eventos = apply_search(
            eventos,
            search,
            [
                "id_ocurrencia",
                "descripcion_evento",
                "codigo_riesgo_snapshot",
                "descripcion_riesgo_snapshot",
                "estado_evento",
            ],
        )
        eventos = apply_ordering(
            eventos,
            request.query_params.get("ordering"),
            {
                "evento_id",
                "id_ocurrencia",
                "fecha_registro",
                "fecha_inicio_evento",
                "fecha_descubrimiento_evento",
                "estado_evento",
                "cuantia_perdida_neta",
            },
        )
        return self.paginated_response(eventos, EventoListSerializer)

    def post(self, request):
        serializer = EventoCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        evento = EventoService.crear_evento(serializer.validated_data, usuario=_obtener_usuario_emma(request.user))
        detalle = EventoSelector.obtener_detalle(evento.evento_id)
        response = Response(EventoDetailSerializer(detalle).data, status=status.HTTP_201_CREATED)
        if EventoService.excede_plazo_registro(evento):
            response["X-EMMA-Advertencia"] = "El registro supera 15 días hábiles desde el descubrimiento; valide la fecha."
        return response


class EventoDetailView(APIView):
    serializer_class = EventoDetailSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, evento_id: int):
        evento = EventoSelector.obtener_detalle(evento_id)
        if evento is None:
            raise NotFound("Evento no encontrado.")
        return Response(EventoDetailSerializer(evento).data)

    def patch(self, request, evento_id: int):
        evento = EventoSelector.obtener_detalle(evento_id)
        if evento is None:
            raise NotFound("Evento no encontrado.")

        serializer = EventoCreateUpdateSerializer(evento, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        evento = EventoService.actualizar_evento(evento, serializer.validated_data, usuario=_obtener_usuario_emma(request.user))
        detalle = EventoSelector.obtener_detalle(evento.evento_id)
        return Response(EventoDetailSerializer(detalle).data)
