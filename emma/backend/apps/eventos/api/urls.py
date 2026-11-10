"""URL routes for eventos API endpoints."""

from django.urls import path

from backend.apps.eventos.api.views import EventoDetailView, EventoListCreateView


app_name = "eventos"

urlpatterns = [
    path("", EventoListCreateView.as_view(), name="evento-list-create"),
    path("<int:evento_id>/", EventoDetailView.as_view(), name="evento-detail"),
]
