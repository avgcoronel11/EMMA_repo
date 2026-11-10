"""Views for audit API endpoints."""

from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from backend.apps.compartido.api.filters import apply_ordering, apply_search
from backend.apps.compartido.api.pagination import ContractPaginationMixin
from backend.apps.compartido.api.serializers.auditoria import AuditoriaSerializer
from backend.apps.compartido.selectors.auditoria_selector import AuditoriaSelector


class AuditoriaListView(ContractPaginationMixin, APIView):
    serializer_class = AuditoriaSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        auditorias = AuditoriaSelector.obtener_base()
        entidad = request.query_params.get("entidad")
        entidad_id = request.query_params.get("entidad_id")
        accion = request.query_params.get("accion")
        usuario_id = request.query_params.get("usuario_id")
        fecha_desde = request.query_params.get("fecha_desde")
        fecha_hasta = request.query_params.get("fecha_hasta")

        if entidad:
            auditorias = auditorias.filter(entidad__iexact=entidad)
        if entidad_id:
            auditorias = auditorias.filter(entidad_id=entidad_id)
        if accion:
            auditorias = auditorias.filter(accion__iexact=accion)
        if usuario_id:
            auditorias = auditorias.filter(usuario_id=usuario_id)
        if fecha_desde:
            auditorias = auditorias.filter(fecha_cambio__date__gte=fecha_desde)
        if fecha_hasta:
            auditorias = auditorias.filter(fecha_cambio__date__lte=fecha_hasta)

        search = request.query_params.get("search") or request.query_params.get("q")
        auditorias = apply_search(auditorias, search, ["entidad", "codigo_negocio_snapshot", "accion", "motivo_modificacion"])
        auditorias = apply_ordering(
            auditorias,
            request.query_params.get("ordering"),
            {"auditoria_id", "entidad", "entidad_id", "accion", "fecha_cambio", "usuario_id"},
        )
        return self.paginated_response(auditorias, AuditoriaSerializer)


class AuditoriaDetailView(APIView):
    serializer_class = AuditoriaSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, auditoria_id: int):
        auditoria = AuditoriaSelector.obtener_detalle(auditoria_id)
        if auditoria is None:
            raise NotFound("Auditoria no encontrada.")
        return Response(AuditoriaSerializer(auditoria).data)
