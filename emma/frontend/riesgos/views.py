from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from urllib.parse import parse_qs, urlencode, urlparse

from autenticacion.decoradores import login_requerido
from core.api_client import delete_json, get_json, patch_json, post_json
from core.errors import ApiClientError, form_errors_from_api, to_user_message

from .forms import CausaForm, ControlForm, EvaluacionControlForm, RiesgoCreateForm, RiesgoEditForm, RiesgoFiltroForm, RiesgoInactivarForm
from .matriz_severidad import preparar_matriz_severidad


def _is_htmx(request):
    return request.headers.get("HX-Request") == "true"


def _filter_form_and_params(request, opciones_riesgo=None):
    form = RiesgoFiltroForm(request.GET, opciones_riesgo=opciones_riesgo)
    params = {}
    if form.is_valid():
        params = {
            key: value
            for key, value in form.cleaned_data.items()
            if value not in ("", None)
        }
    page = request.GET.get("page")
    if page and page.isdigit() and int(page) > 0:
        params["page"] = page
    return form, params


def _page_number(url):
    if not url:
        return None
    # DRF omite `page=1` en el enlace anterior de la segunda página.
    return parse_qs(urlparse(url).query).get("page", ["1"])[0]


def _fetch_riesgos(params, token=None):
    response = get_json("riesgos", params=params, token=token)
    if isinstance(response, dict):
        return response
    if isinstance(response, list):
        return {"count": len(response), "next": None, "previous": None, "results": response}
    return {"count": 0, "next": None, "previous": None, "results": []}


def _apply_api_errors(form, error):
    for field_name, messages in form_errors_from_api(error).items():
        target = field_name if field_name in form.fields else None
        form.add_error(target, messages)


def _obtener_configuracion_valoracion(token):
    return get_json("riesgos/configuracion-valoracion", token=token)


def _opciones_riesgo(token):
    """Opciones maestras para los selectores de información del riesgo."""
    subfactores = _api_lista("catalogos/SUBFACTOR_RIESGO/valores", token, page_size=100).get("results", [])
    homologados = _api_lista("riesgos-genericos", token, page_size=100).get("results", [])
    procesos = _api_todos("procesos", token)

    def unicos(valores):
        return sorted({valor.strip() for valor in valores if valor and valor.strip()}, key=str.casefold)

    return {
        "estructura_procesos": [
            {"proceso_id": item.get("proceso_id"), "vicepresidencia": item.get("vicepresidencia"), "proceso_nivel0": item.get("proceso_nivel0"), "proceso_nivel1": item.get("proceso_nivel1"), "linea": item.get("linea"), "macroproceso": item.get("macroproceso")}
            for item in procesos if item.get("proceso_id") and item.get("vicepresidencia")
        ],
        "subfactores": [(item.get("descripcion") or item.get("codigo"), item.get("descripcion") or item.get("codigo")) for item in subfactores if item.get("descripcion") or item.get("codigo")],
        "riesgos_homologados": [
            (item["nombre"], f'{item.get("codigo", "")} — {item["nombre"]}')
            for item in homologados
            if item.get("nombre")
        ],
        "lineas": [(valor, valor) for valor in unicos(item.get("linea") for item in procesos)],
        "macroprocesos": [(valor, valor) for valor in unicos(item.get("macroproceso") for item in procesos)],
        "vicepresidencias": [(valor, valor) for valor in unicos(item.get("vicepresidencia") for item in procesos)],
        "procesos": [(valor, valor) for valor in unicos(item.get("proceso_nivel0") for item in procesos)],
        "subprocesos": [(valor, valor) for valor in unicos(item.get("proceso_nivel1") for item in procesos)],
        # El dueño es un dato propio de los riesgos ya registrados, no un
        # catálogo de gerencias/direcciones.
        "duenos": [(valor, valor) for valor in unicos(item.get("dueno_proceso") for item in _api_todos("riesgos", token))],
    }


def _build_context(request, *, create_form=None, alert=None):
    pagina = {"count": 0, "next": None, "previous": None, "results": []}
    configuracion = {}
    opciones_riesgo = {}
    try:
        opciones_riesgo = _opciones_riesgo(request.session.get("access_token"))
    except ApiClientError as exc:
        alert = alert or {"level": "danger", "message": to_user_message(exc)}
    filter_form, params = _filter_form_and_params(request, opciones_riesgo)
    try:
        pagina = _fetch_riesgos(params, token=request.session.get("access_token"))
    except ApiClientError as exc:
        alert = alert or {"level": "danger", "message": to_user_message(exc)}
    try:
        configuracion = _obtener_configuracion_valoracion(request.session.get("access_token"))
    except ApiClientError as exc:
        alert = alert or {"level": "danger", "message": to_user_message(exc)}

    return {
        "riesgos": pagina.get("results", []),
        "count": pagina.get("count", 0),
        "next": pagina.get("next"),
        "previous": pagina.get("previous"),
        "query_string": urlencode({key: value for key, value in params.items() if key != "page"}),
        "next_page": _page_number(pagina.get("next")),
        "previous_page": _page_number(pagina.get("previous")),
        "filter_form": filter_form,
        "create_form": create_form or RiesgoCreateForm(configuracion=configuracion, opciones_riesgo=opciones_riesgo),
        "opciones_riesgo": opciones_riesgo,
        "alert": alert,
    }


def _contexto_matriz_unica(request):
    context = _build_context(request)
    token = request.session.get("access_token")
    for nombre, ruta in (("causas", "riesgos/causas"), ("controles", "riesgos/controles")):
        try:
            context[f"{nombre}_pagina"] = _api_lista(ruta, token, page_size=10)
            context[f"{nombre}_alert"] = None
        except ApiClientError as exc:
            context[f"{nombre}_pagina"] = {"results": [], "count": 0, "next": None, "previous": None}
            context[f"{nombre}_alert"] = {"level": "danger", "message": to_user_message(exc)}
    try:
        riesgos, causas, catalogo, sistemas, principios_coso, cuentas = _opciones_control(token)
        context["riesgos_opciones_matriz"] = riesgos
        subfactores = [{"descripcion": etiqueta} for _, etiqueta in context.get("opciones_riesgo", {}).get("subfactores", [])]
        context["causa_form"] = CausaForm(riesgos=riesgos, subfactores=subfactores, require_riesgo=True)
        context["control_form"] = ControlForm(
            riesgos=riesgos,
            causas=causas,
            catalogo=catalogo,
            sistemas=sistemas,
            principios_coso=principios_coso,
            cuentas=cuentas,
            require_context=True,
        )
    except ApiClientError as exc:
        context["causa_form"] = CausaForm(require_riesgo=True)
        context["control_form"] = ControlForm(require_context=True)
        context["formularios_alert"] = {"level": "danger", "message": to_user_message(exc)}
    return context


def _contexto_matriz_severidad(request):
    """Lee solamente la valoración vigente del riesgo seleccionado."""
    riesgo_id = request.GET.get("riesgo_id")
    context = {"matriz_riesgo": None, "matriz_severidad": None, "matriz_alert": None}
    if not riesgo_id:
        return context
    try:
        riesgo_id = int(riesgo_id)
        context["matriz_riesgo"] = _obtener_riesgo(request, riesgo_id)
        context["matriz_severidad"] = preparar_matriz_severidad(context["matriz_riesgo"])
    except (ValueError, ApiClientError) as exc:
        context["matriz_alert"] = {
            "level": "danger",
            "message": to_user_message(exc) if isinstance(exc, ApiClientError) else "Seleccione un riesgo válido.",
        }
    return context


@require_GET
@login_requerido
def lista(request):
    context = _contexto_matriz_unica(request)
    context.update(_contexto_matriz_severidad(request))
    codigo = request.GET.get("codigo_creado")
    entidad = request.GET.get("entidad_creada")
    if codigo and entidad:
        context["alert"] = {"level": "success", "message": f"{entidad} creada correctamente. Código asignado: {codigo}."}
    return render(request, "riesgos/matriz.html", context)


@require_GET
@login_requerido
def matriz_severidad(request):
    return render(request, "riesgos/partials/_matriz_severidad_panel.html", _contexto_matriz_severidad(request))


@require_GET
@login_requerido
def tabla(request):
    context = _build_context(request)
    template_name = "riesgos/partials/_table.html" if _is_htmx(request) else "riesgos/list.html"
    return render(request, template_name, context)


@require_POST
@login_requerido
def crear(request):
    alert = None
    opciones_riesgo = {}
    try:
        configuracion = _obtener_configuracion_valoracion(request.session.get("access_token"))
    except ApiClientError as exc:
        configuracion = {}
        alert = {"level": "danger", "message": to_user_message(exc)}
    try:
        opciones_riesgo = _opciones_riesgo(request.session.get("access_token"))
    except ApiClientError as exc:
        alert = alert or {"level": "danger", "message": to_user_message(exc)}
    form = RiesgoCreateForm(request.POST, configuracion=configuracion, opciones_riesgo=opciones_riesgo)

    if form.is_valid():
        try:
            creado = post_json("riesgos", form.to_api_payload(), token=request.session.get("access_token"))
            form = RiesgoCreateForm(configuracion=configuracion, opciones_riesgo=opciones_riesgo)
            codigo = creado.get("codigo_riesgo") if isinstance(creado, dict) else None
            mensaje = f"Riesgo creado correctamente. Código asignado: {codigo}." if codigo else "Riesgo creado correctamente."
            alert = {"level": "success", "message": mensaje}
        except ApiClientError as exc:
            _apply_api_errors(form, exc)
            alert = {"level": "danger", "message": to_user_message(exc)}

    context = _build_context(request, create_form=form, alert=alert)
    template_name = "riesgos/partials/_workspace.html" if _is_htmx(request) else "riesgos/list.html"
    return render(request, template_name, context)


def _obtener_riesgo(request, riesgo_id):
    return get_json(f"riesgos/{riesgo_id}", token=request.session.get("access_token"))


def _inicial_edicion(riesgo, valoraciones=None):
    campos = RiesgoEditForm().fields
    inicial = {campo: riesgo.get(campo) for campo in campos if campo in riesgo}
    procesos = riesgo.get("procesos") or []
    if procesos:
        principal = next((proceso for proceso in procesos if proceso.get("principal")), procesos[0])
        inicial["vicepresidencia"] = principal.get("vicepresidencia")
        inicial["proceso_nivel0"] = principal.get("proceso_nivel0")
        inicial["proceso_ids"] = str(principal.get("proceso_id"))

    # Las entradas de valoración no se duplican en Riesgo: se conservan en la
    # última fotografía de valoración. Se usan solo para precargar el formulario;
    # los resultados siguen siendo calculados exclusivamente por el backend.
    if not valoraciones:
        return inicial
    ultima = max(valoraciones, key=lambda item: item.get("version", 0))
    datos = ultima.get("datos_entrada") or {}
    probabilidad = datos.get("probabilidad") or {}
    impactos = (datos.get("impacto") or {}).get("impactos") or {}
    for campo in (
        "exposicion", "complejidad", "condiciones_entorno", "grado_ocurrencia",
        "eventos_riesgo", "poblacion_expuesta",
    ):
        if campo in probabilidad:
            inicial[campo] = probabilidad[campo]
    for campo, nombre in RiesgoCreateForm.CAMPOS_IMPACTO.items():
        if nombre in impactos:
            inicial[campo] = impactos[nombre]
    if datos.get("version"):
        inicial["valoracion_version"] = datos["version"]
    return inicial


@require_GET
@login_requerido
def detalle(request, riesgo_id):
    try:
        riesgo = _obtener_riesgo(request, riesgo_id)
        valoraciones = get_json(f"riesgos/{riesgo_id}/valoraciones", token=request.session.get("access_token"))
        controles_por_causa = {}
        for causa in riesgo.get("causas", []):
            if not causa.get("causa_id"):
                continue
            controles = get_json(
                f"riesgos/{riesgo_id}/causas/{causa['causa_id']}/controles",
                token=request.session.get("access_token"),
            )
            causa["controles"] = controles
            controles_por_causa[causa["causa_id"]] = controles
        controles_disponibles = (
            _api_lista("riesgos/controles", request.session.get("access_token"), page_size=100).get("results", [])
            if controles_por_causa else []
        )
    except ApiClientError as exc:
        return render(request, "riesgos/detail.html", {"alert": {"level": "danger", "message": to_user_message(exc)}} , status=exc.status_code or 503)
    try:
        configuracion = _obtener_configuracion_valoracion(request.session.get("access_token"))
    except ApiClientError:
        configuracion = {}
    try:
        opciones_riesgo = _opciones_riesgo(request.session.get("access_token"))
    except (ApiClientError, StopIteration):
        opciones_riesgo = {}
    inicial = _inicial_edicion(riesgo, valoraciones)
    return render(request, "riesgos/detail.html", {
        "riesgo": riesgo,
        "valoraciones": valoraciones,
        "causas": riesgo.get("causas", []),
        "controles": riesgo.get("controles", []),
        "controles_por_causa": controles_por_causa,
        "controles_disponibles": controles_disponibles,
        "edit_form": RiesgoEditForm(initial=inicial, configuracion=configuracion, opciones_riesgo=opciones_riesgo),
        "inactivar_form": RiesgoInactivarForm(),
    })


@require_POST
@login_requerido
def relacion_control_asociar(request, riesgo_id, causa_id):
    try:
        post_json(f"riesgos/{riesgo_id}/causas/{causa_id}/controles", {"control_id": int(request.POST["control_id"])}, token=request.session.get("access_token"))
    except (ApiClientError, ValueError, KeyError):
        pass
    return redirect("riesgos:detail", riesgo_id=riesgo_id)


@require_POST
@login_requerido
def relacion_control_retirar(request, riesgo_id, causa_id, control_id):
    try:
        delete_json(f"riesgos/{riesgo_id}/causas/{causa_id}/controles/{control_id}", token=request.session.get("access_token"))
    except ApiClientError:
        pass
    return redirect("riesgos:detail", riesgo_id=riesgo_id)


@require_POST
@login_requerido
def editar(request, riesgo_id):
    alert = None
    try:
        configuracion = _obtener_configuracion_valoracion(request.session.get("access_token"))
    except ApiClientError as exc:
        configuracion = {}
        alert = {"level": "danger", "message": to_user_message(exc)}
    try:
        opciones_riesgo = _opciones_riesgo(request.session.get("access_token"))
    except ApiClientError as exc:
        opciones_riesgo = {}
        alert = alert or {"level": "danger", "message": to_user_message(exc)}
    form = RiesgoEditForm(request.POST, configuracion=configuracion, opciones_riesgo=opciones_riesgo)
    if form.is_valid():
        try:
            patch_json(f"riesgos/{riesgo_id}", form.to_api_payload(), token=request.session.get("access_token"))
            return redirect("riesgos:detail", riesgo_id=riesgo_id)
        except ApiClientError as exc:
            _apply_api_errors(form, exc)
            alert = {"level": "danger", "message": to_user_message(exc)}
    try:
        riesgo = _obtener_riesgo(request, riesgo_id)
    except ApiClientError as exc:
        return render(request, "riesgos/detail.html", {"alert": {"level": "danger", "message": to_user_message(exc)}}, status=exc.status_code or 503)
    return render(request, "riesgos/detail.html", {
        "riesgo": riesgo,
        "causas": riesgo.get("causas", []),
        "controles": riesgo.get("controles", []),
        "valoraciones": [],
        "edit_form": form,
        "inactivar_form": RiesgoInactivarForm(),
        "alert": alert,
        "edit_mode": True,
    })


@require_POST
@login_requerido
def inactivar(request, riesgo_id):
    form = RiesgoInactivarForm(request.POST)
    alert = None
    if form.is_valid():
        try:
            post_json(
                f"riesgos/{riesgo_id}/inactivar",
                {"justificacion": form.cleaned_data["justificacion"]},
                token=request.session.get("access_token"),
            )
            return redirect("riesgos:detail", riesgo_id=riesgo_id)
        except ApiClientError as exc:
            _apply_api_errors(form, exc)
            alert = {"level": "danger", "message": to_user_message(exc)}
    try:
        riesgo = _obtener_riesgo(request, riesgo_id)
    except ApiClientError as exc:
        return render(request, "riesgos/detail.html", {"alert": {"level": "danger", "message": to_user_message(exc)}}, status=exc.status_code or 503)
    return render(request, "riesgos/detail.html", {
        "riesgo": riesgo,
        "causas": riesgo.get("causas", []),
        "controles": riesgo.get("controles", []),
        "valoraciones": [],
        "edit_form": RiesgoEditForm(initial=_inicial_edicion(riesgo), opciones_riesgo=opciones_riesgo),
        "inactivar_form": form,
        "alert": alert,
    })


def _api_lista(path, token, **params):
    data = get_json(path, params={k: v for k, v in params.items() if v not in (None, "")}, token=token)
    return data if isinstance(data, dict) else {"results": data or [], "count": len(data or []), "next": None, "previous": None}


def _api_todos(path, token, page_size=100):
    """Recorre la paginación contractual para catálogos que alimentan selects."""
    resultados = []
    pagina = 1
    while True:
        respuesta = _api_lista(path, token, page=pagina, page_size=page_size)
        resultados.extend(respuesta.get("results", []))
        if not respuesta.get("next"):
            return resultados
        pagina += 1


def _opciones(token):
    riesgos = _api_lista("riesgos", token, page_size=100).get("results", [])
    causas = _api_lista("riesgos/causas", token, page_size=100).get("results", [])
    catalogo = _api_lista("catalogos/CONTROL_GENERICO/valores", token, page_size=100).get("results", [])
    return riesgos, causas, catalogo


def _opciones_control(token):
    riesgos, causas, catalogo = _opciones(token)
    sistemas = _api_lista("catalogos/SISTEMA/valores", token, page_size=100).get("results", [])
    principios_coso = _api_lista("catalogos/PRINCIPIO_COSO/valores", token, page_size=100).get("results", [])
    cuentas = _api_lista("catalogos/cuentas", token, page_size=100).get("results", [])
    return riesgos, causas, catalogo, sistemas, principios_coso, cuentas


def _inicial_control(control):
    """Adapta la respuesta de lectura de la API a los nombres de los campos editables."""
    inicial = dict(control or {})
    inicial["sistema_valor_ids"] = [str(item["valor_id"]) for item in control.get("sistemas", [])]
    inicial["principio_coso_valor_ids"] = [str(item["valor_id"]) for item in control.get("principios_coso", [])]
    inicial["cuenta_ids"] = [str(item["cuenta_id"]) for item in control.get("cuentas_contables", [])]
    checklists = control.get("checklists", {})
    inicial["aserciones"] = checklists.get("ASERCION", [])
    inicial["atributos"] = checklists.get("ATRIBUTO", [])
    inicial["riesgos_control"] = checklists.get("RIESGO", [])
    return inicial


def _causa_context(request, causa_id=None, alert=None, form=None):
    token = request.session.get("access_token")
    try:
        causa = get_json(f"riesgos/causas/{causa_id}", token=token) if causa_id else None
        riesgos_asociados = get_json(f"riesgos/causas/{causa_id}/riesgos", token=token) if causa_id else []
        riesgos, _, _ = _opciones(token)
    except ApiClientError as exc:
        return {"alert": {"level": "danger", "message": to_user_message(exc)}}
    return {"causa": causa, "riesgos_asociados": riesgos_asociados, "riesgos_opciones": riesgos, "form": form or CausaForm(initial=causa, riesgos=riesgos), "alert": alert}


@login_requerido
def causas_lista(request):
    token = request.session.get("access_token")
    try:
        pagina = _api_lista("riesgos/causas", token, search=request.GET.get("search"), page=request.GET.get("page"))
    except ApiClientError as exc:
        pagina = {"results": [], "count": 0}; alert = {"level": "danger", "message": to_user_message(exc)}
    else:
        alert = None
    return render(request, "riesgos/causas_list.html", {"pagina": pagina, "search": request.GET.get("search", ""), "alert": alert, "next_page": _page_number(pagina.get("next")), "previous_page": _page_number(pagina.get("previous"))})


@login_requerido
def causas_detalle(request, causa_id):
    return render(request, "riesgos/causa_detail.html", _causa_context(request, causa_id))


@login_requerido
def causas_crear(request):
    token = request.session.get("access_token")
    try: riesgos, _, _ = _opciones(token)
    except ApiClientError as exc: return render(request, "riesgos/causa_form.html", {"alert": {"level": "danger", "message": to_user_message(exc)}})
    if request.method == "GET":
        return render(request, "riesgos/causa_form.html", {"form": CausaForm(riesgos=riesgos, require_riesgo=True), "crear": True})
    form = CausaForm(request.POST, riesgos=riesgos, require_riesgo=True)
    if form.is_valid():
        try:
            creada = post_json("riesgos/causas", form.payload(include_riesgo=True), token=token)
            if request.POST.get("from_matrix"):
                return redirect(f"{reverse('riesgos:list')}?entidad_creada=Causa&codigo_creado={creada['codigo_causa']}")
            return redirect("riesgos:causas-detail", causa_id=creada["causa_id"])
        except ApiClientError as exc: _apply_api_errors(form, exc); alert = {"level": "danger", "message": to_user_message(exc)}
    else: alert = {"level": "danger", "message": "Revise los datos de la Causa."}
    return render(request, "riesgos/causa_form.html", {"form": form, "alert": alert, "crear": True})


@require_POST
@login_requerido
def causas_editar(request, causa_id):
    ctx = _causa_context(request, causa_id); token = request.session.get("access_token")
    if not ctx.get("causa"): return render(request, "riesgos/causa_detail.html", ctx, status=404)
    form = CausaForm(request.POST, riesgos=ctx["riesgos_opciones"])
    if form.is_valid():
        try: patch_json(f"riesgos/causas/{causa_id}", form.payload(), token=token); return redirect("riesgos:causas-detail", causa_id=causa_id)
        except ApiClientError as exc: _apply_api_errors(form, exc); ctx["alert"] = {"level": "danger", "message": to_user_message(exc)}
    ctx["form"] = form; return render(request, "riesgos/causa_detail.html", ctx)


@require_POST
@login_requerido
def causas_asociar(request, causa_id):
    token = request.session.get("access_token"); ctx = _causa_context(request, causa_id)
    try: post_json(f"riesgos/{request.POST.get('riesgo_id')}/causas", {"causa_id": causa_id}, token=token); return redirect("riesgos:causas-detail", causa_id=causa_id)
    except ApiClientError as exc: ctx["alert"] = {"level": "danger", "message": to_user_message(exc)}; return render(request, "riesgos/causa_detail.html", ctx)


@require_POST
@login_requerido
def causas_retirar(request, causa_id, riesgo_id):
    token = request.session.get("access_token"); ctx = _causa_context(request, causa_id)
    try: delete_json(f"riesgos/{riesgo_id}/causas/{causa_id}", token=token); return redirect("riesgos:causas-detail", causa_id=causa_id)
    except ApiClientError as exc: ctx["alert"] = {"level": "danger", "message": to_user_message(exc)}; return render(request, "riesgos/causa_detail.html", ctx)


def _control_context(request, control_id, alert=None, form=None):
    token = request.session.get("access_token")
    try:
        control = get_json(f"riesgos/controles/{control_id}", token=token)
        causas = get_json(f"riesgos/controles/{control_id}/causas", token=token)
        riesgos_asociados = get_json(f"riesgos/controles/{control_id}/riesgos", token=token)
        riesgos, causas_opciones, catalogo, sistemas, principios_coso, cuentas = _opciones_control(token)
    except ApiClientError as exc: return {"alert": {"level": "danger", "message": to_user_message(exc)}}
    return {"control": control, "causas_asociadas": causas, "riesgos_asociados": riesgos_asociados, "riesgos_opciones": riesgos, "causas_opciones": causas_opciones, "catalogo": catalogo, "sistemas": sistemas, "principios_coso": principios_coso, "cuentas": cuentas, "form": form or ControlForm(initial=_inicial_control(control), riesgos=riesgos, causas=causas_opciones, catalogo=catalogo, sistemas=sistemas, principios_coso=principios_coso, cuentas=cuentas), "evaluacion_form": EvaluacionControlForm(initial=control), "alert": alert}


@login_requerido
def controles_lista(request):
    token = request.session.get("access_token")
    try: pagina = _api_lista("riesgos/controles", token, search=request.GET.get("search"), page=request.GET.get("page")); alert = None
    except ApiClientError as exc: pagina = {"results": [], "count": 0}; alert = {"level": "danger", "message": to_user_message(exc)}
    return render(request, "riesgos/controles_list.html", {"pagina": pagina, "search": request.GET.get("search", ""), "alert": alert, "next_page": _page_number(pagina.get("next")), "previous_page": _page_number(pagina.get("previous"))})


@login_requerido
def controles_detalle(request, control_id):
    return render(request, "riesgos/control_detail.html", _control_context(request, control_id))


@login_requerido
def controles_crear(request):
    token = request.session.get("access_token")
    try: riesgos, causas, catalogo, sistemas, principios_coso, cuentas = _opciones_control(token)
    except ApiClientError as exc: return render(request, "riesgos/control_form.html", {"alert": {"level": "danger", "message": to_user_message(exc)}})
    if request.method == "GET":
        return render(request, "riesgos/control_form.html", {"form": ControlForm(riesgos=riesgos, causas=causas, catalogo=catalogo, sistemas=sistemas, principios_coso=principios_coso, cuentas=cuentas, require_context=True), "crear": True})
    form = ControlForm(request.POST, riesgos=riesgos, causas=causas, catalogo=catalogo, sistemas=sistemas, principios_coso=principios_coso, cuentas=cuentas, require_context=True)
    if form.is_valid():
        try:
            creado = post_json("riesgos/controles", form.payload(include_context=True), token=token)
            if request.POST.get("from_matrix"):
                return redirect(f"{reverse('riesgos:list')}?entidad_creada=Control&codigo_creado={creado['codigo_control']}")
            return redirect("riesgos:controles-detail", control_id=creado["control_id"])
        except ApiClientError as exc: _apply_api_errors(form, exc); alert = {"level": "danger", "message": to_user_message(exc)}
    else: alert = {"level": "danger", "message": "Revise los datos del Control."}
    return render(request, "riesgos/control_form.html", {"form": form, "alert": alert, "crear": True})


@require_POST
@login_requerido
def controles_editar(request, control_id):
    ctx = _control_context(request, control_id); token = request.session.get("access_token")
    if not ctx.get("control"): return render(request, "riesgos/control_detail.html", ctx, status=404)
    form = ControlForm(request.POST, riesgos=ctx["riesgos_opciones"], causas=ctx["causas_opciones"], catalogo=ctx["catalogo"], sistemas=ctx["sistemas"], principios_coso=ctx["principios_coso"], cuentas=ctx["cuentas"])
    if form.is_valid():
        try: patch_json(f"riesgos/controles/{control_id}", form.payload(), token=token); return redirect("riesgos:controles-detail", control_id=control_id)
        except ApiClientError as exc: _apply_api_errors(form, exc); ctx["alert"] = {"level": "danger", "message": to_user_message(exc)}
    ctx["form"] = form; return render(request, "riesgos/control_detail.html", ctx)


@require_POST
@login_requerido
def controles_asociar(request, control_id):
    token = request.session.get("access_token"); ctx = _control_context(request, control_id); riesgo_id = request.POST.get("riesgo_id"); causa_id = request.POST.get("causa_id")
    try: post_json(f"riesgos/{riesgo_id}/causas/{causa_id}/controles", {"control_id": control_id}, token=token); return redirect("riesgos:controles-detail", control_id=control_id)
    except ApiClientError as exc: ctx["alert"] = {"level": "danger", "message": to_user_message(exc)}; return render(request, "riesgos/control_detail.html", ctx)


@require_POST
@login_requerido
def controles_retirar(request, control_id, riesgo_id, causa_id):
    token = request.session.get("access_token"); ctx = _control_context(request, control_id)
    try: delete_json(f"riesgos/{riesgo_id}/causas/{causa_id}/controles/{control_id}", token=token); return redirect("riesgos:controles-detail", control_id=control_id)
    except ApiClientError as exc: ctx["alert"] = {"level": "danger", "message": to_user_message(exc)}; return render(request, "riesgos/control_detail.html", ctx)


@require_POST
@login_requerido
def controles_evaluar(request, control_id, riesgo_id):
    ctx = _control_context(request, control_id); token = request.session.get("access_token"); form = EvaluacionControlForm(request.POST)
    if form.is_valid() and form.payload():
        try:
            resultado = patch_json(f"riesgos/{riesgo_id}/controles/{control_id}/evaluacion", form.payload(), token=token)
            ctx["alert"] = {"level": "success", "message": "Evaluación registrada." + (" La valoración residual fue actualizada." if resultado.get("residual") else "")}
        except ApiClientError as exc: _apply_api_errors(form, exc); ctx["alert"] = {"level": "danger", "message": to_user_message(exc)}
    else: ctx["alert"] = {"level": "danger", "message": "Debe registrar al menos una respuesta válida."}
    ctx["evaluacion_form"] = form; return render(request, "riesgos/control_detail.html", ctx)
