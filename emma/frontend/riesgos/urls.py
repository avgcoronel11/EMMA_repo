from django.urls import path

from . import views


app_name = "riesgos"

urlpatterns = [
    path("causas/", views.causas_lista, name="causas-list"),
    path("causas/crear/", views.causas_crear, name="causas-create"),
    path("causas/<int:causa_id>/", views.causas_detalle, name="causas-detail"),
    path("causas/<int:causa_id>/editar/", views.causas_editar, name="causas-edit"),
    path("causas/<int:causa_id>/asociar/", views.causas_asociar, name="causas-associate"),
    path("causas/<int:causa_id>/riesgos/<int:riesgo_id>/retirar/", views.causas_retirar, name="causas-remove"),
    path("controles/", views.controles_lista, name="controles-list"),
    path("controles/crear/", views.controles_crear, name="controles-create"),
    path("controles/<int:control_id>/", views.controles_detalle, name="controles-detail"),
    path("controles/<int:control_id>/editar/", views.controles_editar, name="controles-edit"),
    path("controles/<int:control_id>/asociar/", views.controles_asociar, name="controles-associate"),
    path("controles/<int:control_id>/relaciones/<int:riesgo_id>/<int:causa_id>/retirar/", views.controles_retirar, name="controles-remove"),
    path("<int:riesgo_id>/causas/<int:causa_id>/controles/asociar/", views.relacion_control_asociar, name="relacion-control-associate"),
    path("<int:riesgo_id>/causas/<int:causa_id>/controles/<int:control_id>/retirar/", views.relacion_control_retirar, name="relacion-control-remove"),
    path("controles/<int:control_id>/evaluar/<int:riesgo_id>/", views.controles_evaluar, name="controles-evaluate"),
    path("", views.lista, name="list"),
    path("tabla/", views.tabla, name="table"),
    path("matriz-severidad/", views.matriz_severidad, name="matriz-severidad"),
    path("crear/", views.crear, name="create"),
    path("<int:riesgo_id>/", views.detalle, name="detail"),
    path("<int:riesgo_id>/editar/", views.editar, name="edit"),
    path("<int:riesgo_id>/inactivar/", views.inactivar, name="inactivate"),
]
