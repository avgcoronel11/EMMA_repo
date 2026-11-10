"""Views for Causa API endpoints."""
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from backend.apps.compartido.api.filters import apply_search
from backend.apps.compartido.api.pagination import ContractPaginationMixin
from backend.apps.riesgos.api.serializers.causa import CausaDetailSerializer, CausaWriteSerializer
from backend.apps.riesgos.models import Causa, RiesgoCausa
from backend.apps.riesgos.services.causa_service import CausaService


class CausaListCreateView(ContractPaginationMixin, APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        causas = apply_search(Causa.objects.order_by("codigo_causa"), request.query_params.get("search"), ["codigo_causa", "codigo_actual_causa", "descripcion_causa", "subfactor"])
        return self.paginated_response(causas, CausaDetailSerializer)

    def post(self, request):
        serializer = CausaWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        riesgo_id = data.pop("riesgo_id", None)
        if riesgo_id is None:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"riesgo_id": "Este campo es obligatorio."})
        causa = CausaService.crear_causa(data, riesgo_id=riesgo_id, request_user=request.user)
        return Response(CausaDetailSerializer(causa).data, status=201)


class CausaDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def _get(self, causa_id):
        causa = Causa.objects.filter(causa_id=causa_id).first()
        if causa is None:
            raise NotFound("Causa no encontrada.")
        return causa

    def get(self, request, causa_id):
        return Response(CausaDetailSerializer(self._get(causa_id)).data)

    def patch(self, request, causa_id):
        causa = self._get(causa_id)
        serializer = CausaWriteSerializer(causa, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        data.pop("riesgo_id", None)
        return Response(CausaDetailSerializer(CausaService.actualizar_causa(causa, data, request_user=request.user)).data)


class RiesgoCausaListAssociateView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, riesgo_id):
        asociaciones = RiesgoCausa.objects.filter(riesgo_id=riesgo_id).select_related("causa")
        return Response(CausaDetailSerializer([x.causa for x in asociaciones], many=True).data)

    def post(self, request, riesgo_id):
        causa = Causa.objects.filter(causa_id=request.data.get("causa_id")).first()
        if causa is None:
            raise NotFound("Causa no encontrada.")
        CausaService.asociar(causa, riesgo_id, request_user=request.user)
        return Response(status=201)


class RiesgoCausaDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request, riesgo_id, causa_id):
        asociacion = RiesgoCausa.objects.filter(riesgo_id=riesgo_id, causa_id=causa_id).select_related("causa").first()
        if asociacion is None:
            raise NotFound("Asociación Riesgo-Causa no encontrada.")
        CausaService.retirar(asociacion, request_user=request.user)
        return Response(status=204)
