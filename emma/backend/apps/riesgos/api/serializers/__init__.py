"""Serializers for riesgos API endpoints."""

from backend.apps.riesgos.api.serializers.causa import CausaDetailSerializer, CausaWriteSerializer
from backend.apps.riesgos.api.serializers.control import ControlDetailSerializer, ControlEvaluacionSerializer, ControlWriteSerializer
from backend.apps.riesgos.api.serializers.riesgo import (
    RiesgoCreateSerializer,
    RiesgoDetailSerializer,
    RiesgoInactivarSerializer,
    RiesgoUpdateSerializer,
    ValoracionRiesgoSerializer,
    RiesgoListSerializer,
)
from backend.apps.riesgos.api.serializers.valoracion import ValoracionInputSerializer
from backend.apps.riesgos.api.serializers.historico_matriz import (
    ControlEvaluacionHistoricoSerializer,
    HistorialRiesgoCausaControlSerializer,
    HistorialRiesgoCausaSerializer,
)

__all__ = [
    "CausaDetailSerializer",
    "CausaWriteSerializer",
    "ControlDetailSerializer",
    "ControlWriteSerializer",
    "ControlEvaluacionSerializer",
    "RiesgoCreateSerializer",
    "RiesgoDetailSerializer",
    "RiesgoInactivarSerializer",
    "RiesgoUpdateSerializer",
    "ValoracionRiesgoSerializer",
    "RiesgoListSerializer",
    "ValoracionInputSerializer",
    "ControlEvaluacionHistoricoSerializer",
    "HistorialRiesgoCausaSerializer",
    "HistorialRiesgoCausaControlSerializer",
]
