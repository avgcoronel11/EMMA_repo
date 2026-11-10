"""Views for shared API endpoints."""

from backend.apps.compartido.api.views.adjunto import AdjuntoDetailView, AdjuntoListCreateView
from backend.apps.compartido.api.views.auditoria import AuditoriaDetailView, AuditoriaListView

__all__ = [
    "AdjuntoDetailView",
    "AdjuntoListCreateView",
    "AuditoriaDetailView",
    "AuditoriaListView",
]
