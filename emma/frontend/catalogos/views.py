from autenticacion.decoradores import login_requerido
from core.api_client import get_json
from core.views import render_api_list

from .forms import CatalogoFiltroForm


@login_requerido
def lista(request):
    form = CatalogoFiltroForm(request.GET)
    params = form.cleaned_data if form.is_valid() else {}
    return render_api_list(
        request,
        "catalogos/list.html",
        lambda: get_json("catalogos", params=params, token=request.session.get("access_token")),
        "catalogos",
        form=form,
    )
