"""Views for Control API endpoints."""

from django.db import transaction
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from backend.apps.compartido.api.pagination import ContractPaginationMixin
from backend.apps.riesgos.api.serializers.causa import CausaDetailSerializer
from backend.apps.riesgos.api.serializers.control import ControlDetailSerializer, ControlEvaluacionSerializer
from backend.apps.riesgos.api.serializers.control import ControlWriteSerializer
from backend.apps.riesgos.api.serializers.riesgo import RiesgoListSerializer
from backend.apps.riesgos.models import Causa, Control, Riesgo, RiesgoCausa, RiesgoCausaControl
from backend.apps.riesgos.services.control_service import ControlService
from backend.apps.riesgos.services.riesgo_service import RiesgoService


class ControlEvaluacionView(APIView):
    """Registra respuestas D1..D4 y O1..O5 de un control existente."""

    serializer_class = ControlEvaluacionSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def patch(self, request, riesgo_id: int, control_id: int):
        riesgo = Riesgo.objects.filter(riesgo_id=riesgo_id).first()
        if riesgo is None:
            raise NotFound("Riesgo no encontrado.")
        control = Control.objects.filter(control_id=control_id).first()
        if control is None:
            raise NotFound("Control no encontrado.")
        asociado_por_puente = RiesgoCausaControl.objects.filter(
            riesgo_causa__riesgo_id=riesgo_id, control_id=control_id
        ).exists()
        # La FK directa se conserva temporalmente para controles históricos
        # cuya causa mitigada no puede determinarse aún.
        if not asociado_por_puente and control.riesgo_id != riesgo_id:
            raise NotFound("Control no asociado al riesgo.")

        serializer = ControlEvaluacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        control, completa = ControlService.registrar_evaluacion(control, serializer.validated_data, request_user=request.user)
        residual = RiesgoService.recalcular_residual(riesgo) if completa else None
        return Response(
            {
                "evaluacion_completa": completa,
                "residual": residual,
                "control": ControlDetailSerializer(control).data,
            }
        )


class ControlListCreateView(ContractPaginationMixin, APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        controles = Control.objects.order_by("codigo_control")
        search = request.query_params.get("search")
        if search:
            from django.db.models import Q
            controles = controles.filter(Q(codigo_control__icontains=search) | Q(nombre_control__icontains=search))
        return self.paginated_response(controles, ControlDetailSerializer)

    def post(self, request):
        serializer = ControlWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        riesgo_id, causa_id = data.pop("riesgo_id"), data.pop("causa_id")
        riesgo_causa = RiesgoCausa.objects.filter(riesgo_id=riesgo_id, causa_id=causa_id).first()
        if riesgo_causa is None:
            raise NotFound("La causa no está asociada al riesgo indicado.")
        control, _ = ControlService.crear_control(data, riesgo_causa=riesgo_causa, request_user=request.user)
        return Response(ControlDetailSerializer(control).data, status=201)


class ControlDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def _get(self, control_id):
        control = Control.objects.filter(control_id=control_id).first()
        if control is None:
            raise NotFound("Control no encontrado.")
        return control

    def get(self, request, control_id):
        return Response(ControlDetailSerializer(self._get(control_id)).data)

    def patch(self, request, control_id):
        control = self._get(control_id)
        serializer = ControlWriteSerializer(control, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        data.pop("riesgo_id", None); data.pop("causa_id", None)
        return Response(ControlDetailSerializer(ControlService.actualizar_control(control, data, request_user=request.user)).data)


class RiesgoCausaControlListAssociateView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, riesgo_id, causa_id):
        relaciones = RiesgoCausaControl.objects.filter(riesgo_causa__riesgo_id=riesgo_id, riesgo_causa__causa_id=causa_id).select_related("control")
        return Response(ControlDetailSerializer([x.control for x in relaciones], many=True).data)

    def post(self, request, riesgo_id, causa_id):
        riesgo_causa = RiesgoCausa.objects.filter(riesgo_id=riesgo_id, causa_id=causa_id).first()
        if riesgo_causa is None:
            raise NotFound("La causa no está asociada al riesgo indicado.")
        control = Control.objects.filter(control_id=request.data.get("control_id")).first()
        if control is None:
            raise NotFound("Control no encontrado.")
        ControlService.asociar(control, riesgo_causa, request_user=request.user)
        return Response(status=201)


class RiesgoCausaControlDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, riesgo_id, causa_id, control_id):
        relacion = RiesgoCausaControl.objects.filter(
            riesgo_causa__riesgo_id=riesgo_id,
            riesgo_causa__causa_id=causa_id,
            control_id=control_id,
        ).first()
        if relacion is None:
            raise NotFound("Asociación Riesgo-Causa-Control no encontrada.")
        ControlService.retirar(relacion, request_user=request.user)
        return Response(status=204)


class CausaRiesgosView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, causa_id):
        if not Causa.objects.filter(causa_id=causa_id).exists():
            raise NotFound("Causa no encontrada.")
        riesgos = Riesgo.objects.filter(causa_asociaciones__causa_id=causa_id).distinct().order_by("riesgo_id")
        return Response(RiesgoListSerializer(riesgos, many=True).data)


class ControlCausasView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, control_id):
        if not Control.objects.filter(control_id=control_id).exists():
            raise NotFound("Control no encontrado.")
        causas = Causa.objects.filter(
            riesgo_asociaciones__control_asociaciones__control_id=control_id
        ).distinct().order_by("causa_id")
        return Response(CausaDetailSerializer(causas, many=True).data)


class ControlRiesgosView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, control_id):
        if not Control.objects.filter(control_id=control_id).exists():
            raise NotFound("Control no encontrado.")
        riesgos = Riesgo.objects.filter(
            causa_asociaciones__control_asociaciones__control_id=control_id
        ).distinct().order_by("riesgo_id")
        return Response(RiesgoListSerializer(riesgos, many=True).data)
