from django.urls import include, path

from autenticacion import views as auth_views


urlpatterns = [
    path("", auth_views.login, name="login"),
    path("inicio/", auth_views.inicio, name="inicio"),
    path("auth/", include("autenticacion.urls")),
    path("catalogos/", include("catalogos.urls")),
    path("riesgos/", include("riesgos.urls")),
    path("eventos/", include("eventos.urls")),
    path("planes/", include("planes.urls")),
]

handler404 = "core.views.error_404"
handler500 = "core.views.error_500"
