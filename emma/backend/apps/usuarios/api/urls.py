"""URL routes for usuarios API endpoints."""

from django.urls import path

from backend.apps.usuarios.api.views import UsuarioDetailView, UsuarioListView


app_name = "usuarios"

urlpatterns = [
    path("", UsuarioListView.as_view(), name="usuario-list"),
    path("<int:usuario_id>/", UsuarioDetailView.as_view(), name="usuario-detail"),
]
