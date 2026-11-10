"""Read queries for process master data."""

from backend.apps.procesos.models import CatProceso


class ProcesoSelector:
    @staticmethod
    def obtener_activos(
        *,
        vicepresidencia: str | None = None,
        proceso: str | None = None,
        subproceso: str | None = None,
        linea: str | None = None,
        macroproceso: str | None = None,
    ):
        queryset = CatProceso.objects.filter(activo=True).select_related("parent_proceso")

        if vicepresidencia:
            queryset = queryset.filter(vicepresidencia__iexact=vicepresidencia)
        if proceso:
            queryset = queryset.filter(proceso_nivel0__iexact=proceso)
        if subproceso:
            queryset = queryset.filter(proceso_nivel1__iexact=subproceso)
        if linea:
            queryset = queryset.filter(linea__iexact=linea)
        if macroproceso:
            queryset = queryset.filter(macroproceso__iexact=macroproceso)

        return queryset.order_by("vicepresidencia", "proceso_nivel0", "proceso_nivel1", "proceso_id")
