"""Read-only endpoints for append-only functional matrix history."""

from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.apps.riesgos.api.serializers.historico_matriz import (
    ControlEvaluacionHistoricoSerializer,
    HistorialRiesgoCausaControlSerializer,
    HistorialRiesgoCausaSerializer,
)
from backend.apps.riesgos.models import (
    Causa,
    Control,
    ControlEvaluacionHistorico,
    HistorialRiesgoCausa,
    HistorialRiesgoCausaControl,
    Riesgo,
)


class ControlEvaluacionesHistoricasView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, control_id):
        if not Control.objects.filter(control_id=control_id).exists():
            raise NotFound("Control no encontrado.")
        historial = ControlEvaluacionHistorico.objects.filter(control_id=control_id).order_by("-version")
        return Response(ControlEvaluacionHistoricoSerializer(historial, many=True).data)


class RiesgoCausaHistorialAsociacionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, riesgo_id, causa_id):
        if not Riesgo.objects.filter(riesgo_id=riesgo_id).exists():
            raise NotFound("Riesgo no encontrado.")
        if not Causa.objects.filter(causa_id=causa_id).exists():
            raise NotFound("Causa no encontrada.")
        historial = HistorialRiesgoCausa.objects.filter(
            riesgo_id=riesgo_id, causa_id=causa_id
        ).order_by("-version")
        return Response(HistorialRiesgoCausaSerializer(historial, many=True).data)


class RiesgoCausaControlHistorialAsociacionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, riesgo_id, causa_id, control_id):
        if not Riesgo.objects.filter(riesgo_id=riesgo_id).exists():
            raise NotFound("Riesgo no encontrado.")
        if not Causa.objects.filter(causa_id=causa_id).exists():
            raise NotFound("Causa no encontrada.")
        if not Control.objects.filter(control_id=control_id).exists():
            raise NotFound("Control no encontrado.")
        historial = HistorialRiesgoCausaControl.objects.filter(
            riesgo_id=riesgo_id, causa_id=causa_id, control_id=control_id
        ).order_by("-version")
        return Response(HistorialRiesgoCausaControlSerializer(historial, many=True).data)
