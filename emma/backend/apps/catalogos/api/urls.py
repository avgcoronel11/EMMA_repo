"""URL routes for catalogos API endpoints."""

from django.urls import path

from backend.apps.catalogos.api.views import CatalogoDetailView, CatalogoListView, CatalogoValoresView, CuentaContableListView


app_name = "catalogos"

urlpatterns = [
    path("", CatalogoListView.as_view(), name="catalogo-list"),
    path("cuentas/", CuentaContableListView.as_view(), name="cuenta-list"),
    path("<str:codigo>/valores/", CatalogoValoresView.as_view(), name="catalogo-valores"),
    path("<str:codigo>/", CatalogoDetailView.as_view(), name="catalogo-detail"),
]
