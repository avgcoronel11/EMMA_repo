"""Views for riesgos API endpoints."""

from backend.apps.riesgos.api.views.riesgo import (
    RiesgoDetailView,
    RiesgoInactivarView,
    RiesgoListCreateView,
    RiesgoRecalcularResidualView,
    RiesgoValoracionesView,
)
from backend.apps.riesgos.api.views.control import (
    CausaRiesgosView,
    ControlCausasView,
    ControlDetailView,
    ControlEvaluacionView,
    ControlListCreateView,
    ControlRiesgosView,
    RiesgoCausaControlDetailView,
    RiesgoCausaControlListAssociateView,
)
from backend.apps.riesgos.api.views.causa import CausaDetailView, CausaListCreateView, RiesgoCausaDetailView, RiesgoCausaListAssociateView
from backend.apps.riesgos.api.views.valoracion import RiesgoCalcularValoracionView
from backend.apps.riesgos.api.views.configuracion_valoracion import RiesgoConfiguracionValoracionView
from backend.apps.riesgos.api.views.historico_matriz import (
    ControlEvaluacionesHistoricasView,
    RiesgoCausaControlHistorialAsociacionView,
    RiesgoCausaHistorialAsociacionView,
)

__all__ = [
    "RiesgoCalcularValoracionView",
    "RiesgoConfiguracionValoracionView",
    "ControlEvaluacionView",
    "ControlDetailView",
    "ControlListCreateView",
    "RiesgoCausaControlListAssociateView",
    "RiesgoCausaControlDetailView",
    "CausaRiesgosView",
    "ControlCausasView",
    "ControlRiesgosView",
    "CausaDetailView",
    "CausaListCreateView",
    "RiesgoCausaDetailView",
    "RiesgoCausaListAssociateView",
    "RiesgoDetailView",
    "RiesgoInactivarView",
    "RiesgoListCreateView",
    "RiesgoRecalcularResidualView",
    "RiesgoValoracionesView",
    "ControlEvaluacionesHistoricasView",
    "RiesgoCausaHistorialAsociacionView",
    "RiesgoCausaControlHistorialAsociacionView",
]
