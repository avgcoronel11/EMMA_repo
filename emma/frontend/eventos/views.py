from autenticacion.decoradores import login_requerido
from core.api_client import get_json
from core.views import render_api_list
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from core.errors import ApiClientError, to_user_message

from .forms import EventoFiltroForm


@login_requerido
def lista(request):
    form = EventoFiltroForm(request.GET)
    params = form.cleaned_data if form.is_valid() else {}
    return render_api_list(
        request,
        "eventos/list.html",
        lambda: get_json("eventos", params=params, token=request.session.get("access_token")),
        "eventos",
        form=form,
    )


@login_requerido
def formulario(request):
    return _formulario(request, "crear")


@login_requerido
def editar(request, evento_id):
    return _formulario(request, "editar", evento_id)


def _api_todos(ruta, token):
    """Lee todas las páginas de una colección paginada del API industrializado."""
    respuesta = get_json(ruta, params={"page_size": 100}, token=token)
    if isinstance(respuesta, list):
        return respuesta
    resultados = list(respuesta.get("results", [])) if isinstance(respuesta, dict) else []
    while isinstance(respuesta, dict) and respuesta.get("next"):
        from urllib.parse import parse_qs, urlparse
        pagina = parse_qs(urlparse(respuesta["next"]).query).get("page", [None])[0]
        if not pagina:
            break
        respuesta = get_json(ruta, params={"page": pagina, "page_size": 100}, token=token)
        resultados.extend(respuesta.get("results", []))
    return resultados


def _formulario(request, modo, evento_id=None):
    codigos = {
        "paises": "PAIS", "departamentos": "DEPARTAMENTO", "ciudades": "CIUDAD",
        "oficinas": "OFICINA", "gerencias": "GERENCIA_EVENTO", "productos": "PRODUCTO",
        "canales": "CANAL", "segmentos": "SEGMENTO", "tipos_perdida": "TIPO_PERDIDA",
        "divisas": "DIVISA", "tipologias": "CLASE_EVENTO", "lineas_negocio": "LINEA_NEGOCIO",
        "tipos_evento": "TIPO_EVENTO",
    }
    token = request.session.get("access_token")
    datos, error = {}, None
    evento_actual = None
    try:
        for clave, codigo in codigos.items():
            datos[clave] = _api_todos(f"catalogos/{codigo}/valores", token)
        datos["procesos"] = _api_todos("procesos", token)
        datos["causas"] = _api_todos("riesgos/causas", token)
        datos["riesgos"] = _api_todos("riesgos", token)
    except ApiClientError as exc:
        error = to_user_message(exc)
    if modo == "editar":
        try:
            evento_actual = get_json(f"eventos/{evento_id}", token=token)
        except ApiClientError as exc:
            error = error or to_user_message(exc)
    return render(request, "eventos/formulario.html", {
        "modo": modo, "evento_id": evento_id, "catalogos_eventos": datos,
        "evento_actual": evento_actual, "catalogos_error": error,
    })


@login_requerido
@require_GET
def riesgo_detalle_proxy(request, riesgo_id):
    try:
        data = get_json(f"riesgos/{riesgo_id}", token=request.session.get("access_token"))
        return JsonResponse(data)
    except ApiClientError as exc:
        return JsonResponse({"error": to_user_message(exc)}, status=502)


@login_requerido
@require_GET
def riesgo_lista_proxy(request):
    params = {key: request.GET.get(key) for key in ("vicepresidencia", "proceso", "subproceso") if request.GET.get(key)}
    try:
        data = get_json("riesgos", params=params, token=request.session.get("access_token"))
        return JsonResponse(data, safe=not isinstance(data, list))
    except ApiClientError as exc:
        return JsonResponse({"error": to_user_message(exc)}, status=502)


@login_requerido
def detalle(request, evento_id):
    """Vista visual de detalle; pendiente enlazar la respuesta del API."""
    return render(request, "eventos/detalle.html", {"evento_id": evento_id})
