from django.urls import path

from . import views


app_name = "autenticacion"

urlpatterns = [
    path("login/", views.iniciar_sesion, name="login"),
    path("iniciar-sesion/", views.iniciar_sesion, name="iniciar_sesion"),
    path("callback", views.callback, name="callback-no-slash"),
    path("callback/", views.callback, name="callback"),
    path("logout/", views.cerrar_sesion, name="logout"),
    path("cerrar-sesion/", views.cerrar_sesion, name="cerrar_sesion"),
]
