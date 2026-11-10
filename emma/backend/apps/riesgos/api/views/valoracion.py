"""Views for risk valuation API endpoints."""

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from backend.apps.riesgos.api.serializers import ValoracionInputSerializer
from backend.apps.riesgos.services.riesgo_service import RiesgoService


class RiesgoCalcularValoracionView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ValoracionInputSerializer

    def post(self, request):
        serializer = ValoracionInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        resultado = RiesgoService.calcular_valoracion(serializer.validated_data)
        return Response(resultado)
