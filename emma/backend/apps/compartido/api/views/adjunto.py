"""Views for attachment metadata API endpoints."""

from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.apps.compartido.api.filters import apply_ordering, apply_search
from backend.apps.compartido.api.pagination import ContractPaginationMixin
from backend.apps.compartido.api.serializers.adjunto import (
    AdjuntoCreateUpdateSerializer,
    AdjuntoSerializer,
)
from backend.apps.compartido.selectors.adjunto_selector import AdjuntoSelector
from backend.apps.compartido.services.adjunto_service import AdjuntoService


class AdjuntoListCreateView(ContractPaginationMixin, APIView):
    serializer_class = AdjuntoSerializer

    def get(self, request):
        adjuntos = AdjuntoSelector.obtener_base()
        evento_id = request.query_params.get("evento_id")
        plan_id = request.query_params.get("plan_id")
        content_type = request.query_params.get("content_type")

        if evento_id:
            adjuntos = adjuntos.filter(evento_id=evento_id)
        if plan_id:
            adjuntos = adjuntos.filter(plan_id=plan_id)
        if content_type:
            adjuntos = adjuntos.filter(content_type__iexact=content_type)

        search = request.query_params.get("search") or request.query_params.get("q")
        adjuntos = apply_search(adjuntos, search, ["nombre_archivo", "ruta_storage", "content_type"])
        adjuntos = apply_ordering(
            adjuntos,
            request.query_params.get("ordering"),
            {"adjunto_id", "nombre_archivo", "content_type", "tamano_bytes", "fecha_carga"},
        )
        return self.paginated_response(adjuntos, AdjuntoSerializer)

    def post(self, request):
        serializer = AdjuntoCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        adjunto = AdjuntoService.crear_adjunto(serializer.validated_data)
        detalle = AdjuntoSelector.obtener_detalle(adjunto.adjunto_id)
        return Response(AdjuntoSerializer(detalle).data, status=status.HTTP_201_CREATED)


class AdjuntoDetailView(APIView):
    serializer_class = AdjuntoSerializer

    def get(self, request, adjunto_id: int):
        adjunto = AdjuntoSelector.obtener_detalle(adjunto_id)
        if adjunto is None:
            raise NotFound("Adjunto no encontrado.")
        return Response(AdjuntoSerializer(adjunto).data)

    def patch(self, request, adjunto_id: int):
        adjunto = AdjuntoSelector.obtener_detalle(adjunto_id)
        if adjunto is None:
            raise NotFound("Adjunto no encontrado.")

        serializer = AdjuntoCreateUpdateSerializer(adjunto, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        adjunto = AdjuntoService.actualizar_adjunto(adjunto, serializer.validated_data)
        detalle = AdjuntoSelector.obtener_detalle(adjunto.adjunto_id)
        return Response(AdjuntoSerializer(detalle).data)

    def delete(self, request, adjunto_id: int):
        adjunto = AdjuntoSelector.obtener_detalle(adjunto_id)
        if adjunto is None:
            raise NotFound("Adjunto no encontrado.")
        AdjuntoService.eliminar_adjunto(adjunto)
        return Response(status=status.HTTP_204_NO_CONTENT)
