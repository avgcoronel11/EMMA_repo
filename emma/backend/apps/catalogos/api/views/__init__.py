"""Views for catalogos API endpoints."""

from backend.apps.catalogos.api.views.catalogo import (
    CatalogoDetailView,
    CatalogoListView,
    CatalogoValoresView,
    CuentaContableListView,
    RiesgoGenericoListView,
)

__all__ = [
    "CatalogoDetailView",
    "CatalogoListView",
    "CatalogoValoresView",
    "CuentaContableListView",
    "RiesgoGenericoListView",
]
