from django.urls import path

from . import views


app_name = "eventos"

urlpatterns = [
    path("api/riesgos/", views.riesgo_lista_proxy, name="riesgo-options"),
    path("api/riesgos/<int:riesgo_id>/", views.riesgo_detalle_proxy, name="riesgo-detail-options"),
    path("crear/", views.formulario, name="create"),
    path("<int:evento_id>/", views.detalle, name="detail"),
    path("<int:evento_id>/editar/", views.editar, name="edit"),
    path("", views.lista, name="list"),
]

