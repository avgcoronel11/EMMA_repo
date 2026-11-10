"""Views for process read endpoints."""

from rest_framework.views import APIView

from backend.apps.compartido.api.filters import apply_ordering, apply_search
from backend.apps.compartido.api.pagination import ContractPaginationMixin
from backend.apps.procesos.api.serializers.proceso import CatProcesoSerializer
from backend.apps.procesos.selectors.proceso_selector import ProcesoSelector


class ProcesoListView(ContractPaginationMixin, APIView):
    serializer_class = CatProcesoSerializer

    def get(self, request):
        procesos = ProcesoSelector.obtener_activos(
            vicepresidencia=request.query_params.get("vicepresidencia"),
            proceso=request.query_params.get("proceso"),
            subproceso=request.query_params.get("subproceso"),
            linea=request.query_params.get("linea"),
            macroproceso=request.query_params.get("macroproceso"),
        )
        procesos = apply_search(
            procesos,
            request.query_params.get("search"),
            ["vicepresidencia", "proceso_nivel0", "proceso_nivel1", "proceso_nivel2", "macroproceso", "linea"],
        )
        procesos = apply_ordering(
            procesos,
            request.query_params.get("ordering"),
            {
                "vicepresidencia",
                "proceso_nivel0",
                "proceso_nivel1",
                "proceso_nivel2",
                "macroproceso",
                "linea",
                "proceso_id",
            },
        )
        return self.paginated_response(procesos, CatProcesoSerializer)
