"""Read queries for catalog and master data."""

from backend.apps.catalogos.models import Catalogo, CatalogoValor, RiesgoGenerico


class CatalogoSelector:
    @staticmethod
    def obtener_base(*, solo_activos: bool = True):
        queryset = Catalogo.objects.all()
        if solo_activos:
            queryset = queryset.filter(activo=True)
        return queryset.order_by("codigo_catalogo", "catalogo_id")

    @staticmethod
    def obtener_catalogo(codigo: str, *, solo_activos: bool = True):
        queryset = Catalogo.objects.filter(codigo_catalogo__iexact=codigo)
        if solo_activos:
            queryset = queryset.filter(activo=True)
        return queryset.first()

    @staticmethod
    def obtener_valores(codigo: str, *, solo_activos: bool = True):
        queryset = CatalogoValor.objects.select_related("catalogo", "parent_valor").filter(
            catalogo__codigo_catalogo__iexact=codigo,
        )
        if solo_activos:
            queryset = queryset.filter(activo=True, catalogo__activo=True)
        return queryset.order_by("orden", "nivel", "descripcion", "valor_id")

    @staticmethod
    def obtener_riesgos_genericos_activos():
        return RiesgoGenerico.objects.filter(activo=True).order_by("codigo", "nombre")
