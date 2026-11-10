"""URL routes for riesgos API endpoints."""

from django.urls import path

from backend.apps.riesgos.api.views import (
    ControlEvaluacionView,
    ControlDetailView,
    ControlListCreateView,
    CausaDetailView,
    CausaListCreateView,
    RiesgoCalcularValoracionView,
    RiesgoConfiguracionValoracionView,
    RiesgoDetailView,
    RiesgoInactivarView,
    RiesgoListCreateView,
    RiesgoRecalcularResidualView,
    RiesgoValoracionesView,
    RiesgoCausaDetailView,
    RiesgoCausaListAssociateView,
    RiesgoCausaControlListAssociateView,
    RiesgoCausaControlDetailView,
    CausaRiesgosView,
    ControlCausasView,
    ControlRiesgosView,
    ControlEvaluacionesHistoricasView,
    RiesgoCausaHistorialAsociacionView,
    RiesgoCausaControlHistorialAsociacionView,
)


app_name = "riesgos"

urlpatterns = [
    path("causas/", CausaListCreateView.as_view(), name="causa-list-create"),
    path("causas/<int:causa_id>/", CausaDetailView.as_view(), name="causa-detail"),
    path("causas/<int:causa_id>/riesgos/", CausaRiesgosView.as_view(), name="causa-riesgos"),
    path("controles/", ControlListCreateView.as_view(), name="control-list-create"),
    path("controles/<int:control_id>/", ControlDetailView.as_view(), name="control-detail"),
    path("controles/<int:control_id>/causas/", ControlCausasView.as_view(), name="control-causas"),
    path("controles/<int:control_id>/riesgos/", ControlRiesgosView.as_view(), name="control-riesgos"),
    path("controles/<int:control_id>/evaluaciones-historicas/", ControlEvaluacionesHistoricasView.as_view(), name="control-evaluaciones-historicas"),
    path("", RiesgoListCreateView.as_view(), name="riesgo-list-create"),
    path("calcular-valoracion/", RiesgoCalcularValoracionView.as_view(), name="riesgo-calcular-valoracion"),
    path("configuracion-valoracion/", RiesgoConfiguracionValoracionView.as_view(), name="riesgo-configuracion-valoracion"),
    path(
        "<int:riesgo_id>/controles/<int:control_id>/evaluacion/",
        ControlEvaluacionView.as_view(),
        name="control-evaluacion",
    ),
    path("<int:riesgo_id>/causas/", RiesgoCausaListAssociateView.as_view(), name="riesgo-causa-list-associate"),
    path("<int:riesgo_id>/causas/<int:causa_id>/", RiesgoCausaDetailView.as_view(), name="riesgo-causa-detail"),
    path("<int:riesgo_id>/causas/<int:causa_id>/historial-asociacion/", RiesgoCausaHistorialAsociacionView.as_view(), name="riesgo-causa-historial-asociacion"),
    path("<int:riesgo_id>/causas/<int:causa_id>/controles/", RiesgoCausaControlListAssociateView.as_view(), name="riesgo-causa-control-list-associate"),
    path("<int:riesgo_id>/causas/<int:causa_id>/controles/<int:control_id>/", RiesgoCausaControlDetailView.as_view(), name="riesgo-causa-control-detail"),
    path("<int:riesgo_id>/causas/<int:causa_id>/controles/<int:control_id>/historial-asociacion/", RiesgoCausaControlHistorialAsociacionView.as_view(), name="riesgo-causa-control-historial-asociacion"),
    path("<int:riesgo_id>/", RiesgoDetailView.as_view(), name="riesgo-detail"),
    path("<int:riesgo_id>/valoraciones/", RiesgoValoracionesView.as_view(), name="riesgo-valoraciones"),
    path("<int:riesgo_id>/valoraciones/<int:valoracion_id>/", RiesgoValoracionesView.as_view(), name="riesgo-valoracion-detail"),
    path("<int:riesgo_id>/inactivar/", RiesgoInactivarView.as_view(), name="riesgo-inactivar"),
    path(
        "<int:riesgo_id>/recalcular-residual/",
        RiesgoRecalcularResidualView.as_view(),
        name="riesgo-recalcular-residual",
    ),
]
