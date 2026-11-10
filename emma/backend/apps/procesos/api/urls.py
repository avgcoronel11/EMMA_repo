"""URL routes for procesos API endpoints."""

from django.urls import path

from backend.apps.procesos.api.views import ProcesoListView


app_name = "procesos"

urlpatterns = [
    path("", ProcesoListView.as_view(), name="proceso-list"),
]
