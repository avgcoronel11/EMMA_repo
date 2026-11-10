"""Views for catalog read endpoints."""

from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.apps.compartido.api.filters import apply_ordering, apply_search
from backend.apps.compartido.api.pagination import ContractPaginationMixin
from backend.apps.catalogos.api.serializers.catalogo import (
    CatalogoSerializer,
    CatalogoValorSerializer,
    CuentaContableSerializer,
    RiesgoGenericoSerializer,
)
from backend.apps.catalogos.selectors.catalogo_selector import CatalogoSelector
from backend.apps.catalogos.models import CuentaContable


class CatalogoListView(ContractPaginationMixin, APIView):
    serializer_class = CatalogoSerializer

    def get(self, request):
        solo_activos = request.query_params.get("solo_activos", "true").lower() != "false"
        catalogos = CatalogoSelector.obtener_base(solo_activos=solo_activos)
        activo = request.query_params.get("activo")
        if activo is not None:
            catalogos = catalogos.filter(activo=activo.lower() == "true")

        search = request.query_params.get("search") or request.query_params.get("q")
        catalogos = apply_search(catalogos, search, ["codigo_catalogo", "nombre", "descripcion"])
        catalogos = apply_ordering(
            catalogos,
            request.query_params.get("ordering"),
            {"catalogo_id", "codigo_catalogo", "nombre", "activo"},
        )
        return self.paginated_response(catalogos, CatalogoSerializer)


class CatalogoDetailView(APIView):
    serializer_class = CatalogoSerializer

    def get(self, request, codigo: str):
        solo_activos = request.query_params.get("solo_activos", "true").lower() != "false"
        catalogo = CatalogoSelector.obtener_catalogo(codigo, solo_activos=solo_activos)
        if catalogo is None:
            raise NotFound("Catalogo no encontrado.")
        return Response(CatalogoSerializer(catalogo).data)


class CatalogoValoresView(ContractPaginationMixin, APIView):
    serializer_class = CatalogoValorSerializer

    def get(self, request, codigo: str):
        solo_activos = request.query_params.get("solo_activos", "true").lower() != "false"
        catalogo = CatalogoSelector.obtener_catalogo(codigo, solo_activos=solo_activos)
        if catalogo is None:
            raise NotFound("Catalogo no encontrado.")

        valores = CatalogoSelector.obtener_valores(codigo, solo_activos=solo_activos)
        valores = apply_search(valores, request.query_params.get("search"), ["codigo", "descripcion"])
        valores = apply_ordering(
            valores,
            request.query_params.get("ordering"),
            {"codigo", "descripcion", "nivel", "orden", "valor_id"},
        )
        return self.paginated_response(valores, CatalogoValorSerializer)


class RiesgoGenericoListView(ContractPaginationMixin, APIView):
    serializer_class = RiesgoGenericoSerializer

    def get(self, request):
        riesgos_genericos = CatalogoSelector.obtener_riesgos_genericos_activos()
        riesgos_genericos = apply_search(riesgos_genericos, request.query_params.get("search"), ["codigo", "nombre"])
        riesgos_genericos = apply_ordering(
            riesgos_genericos,
            request.query_params.get("ordering"),
            {"codigo", "nombre", "riesgo_generico_id"},
        )
        return self.paginated_response(riesgos_genericos, RiesgoGenericoSerializer)


class CuentaContableListView(ContractPaginationMixin, APIView):
    """Cuentas activas disponibles para relaciones N:M con controles."""

    def get(self, request):
        cuentas = CuentaContable.objects.filter(activo=True).order_by("cuenta_10", "cuenta_6", "cuenta_id")
        cuentas = apply_search(cuentas, request.query_params.get("search"), ["cuenta_10", "cuenta_6", "descripcion"])
        return self.paginated_response(cuentas, CuentaContableSerializer)


