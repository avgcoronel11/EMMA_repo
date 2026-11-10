"""Versioned API routes for EMMA."""

from django.urls import include, path

from backend.apps.catalogos.api.views import RiesgoGenericoListView
from backend.apps.compartido.api.views import (
    AdjuntoDetailView,
    AdjuntoListCreateView,
    AuditoriaDetailView,
    AuditoriaListView,
)


app_name = "api"

urlpatterns = [
    path("catalogos/", include("backend.apps.catalogos.api.urls")),
    path("riesgos-genericos/", RiesgoGenericoListView.as_view(), name="riesgo-generico-list"),
    path("procesos/", include("backend.apps.procesos.api.urls")),
    path("riesgos/", include("backend.apps.riesgos.api.urls")),
    path("eventos/", include("backend.apps.eventos.api.urls")),
    path("planes/", include("backend.apps.planes.api.urls")),
    path("adjuntos/", AdjuntoListCreateView.as_view(), name="adjunto-list-create"),
    path("adjuntos/<int:adjunto_id>/", AdjuntoDetailView.as_view(), name="adjunto-detail"),
    path("auditoria/", AuditoriaListView.as_view(), name="auditoria-list"),
    path("auditoria/<int:auditoria_id>/", AuditoriaDetailView.as_view(), name="auditoria-detail"),
    path("usuarios/", include("backend.apps.usuarios.api.urls")),
    path("compartido/", include("backend.apps.compartido.api.urls")),
]
