"""Endpoint de opciones válidas para la valoración de Riesgos."""

from rest_framework.response import Response
from rest_framework.views import APIView

from backend.apps.riesgos.services.valoracion_configuracion_service import obtener_configuracion


class RiesgoConfiguracionValoracionView(APIView):
    def get(self, request):
        return Response(obtener_configuracion(version=request.query_params.get("version")))
