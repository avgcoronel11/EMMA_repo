from autenticacion.decoradores import login_requerido
from core.api_client import get_json
from core.views import render_api_list

from .forms import PlanFiltroForm


@login_requerido
def lista(request):
    form = PlanFiltroForm(request.GET)
    params = form.cleaned_data if form.is_valid() else {}
    return render_api_list(
        request,
        "planes/list.html",
        lambda: get_json("planes", params=params, token=request.session.get("access_token")),
        "planes",
        form=form,
    )
