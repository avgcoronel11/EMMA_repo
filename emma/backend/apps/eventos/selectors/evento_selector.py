"""Read queries for event risk data."""

from django.db.models import Prefetch

from backend.apps.compartido.models import EntidadCaracteristica
from backend.apps.eventos.models import (
    EventoCausa,
    EventoControl,
    EventoCuentaContable,
    EventoDistribucionLinea,
    EventoRiesgo,
)


class EventoSelector:
    @staticmethod
    def obtener_base():
        return (
            EventoRiesgo.objects.select_related(
                "usuario_registro",
                "riesgo",
                "tipo_evento_valor",
            )
            .prefetch_related(
                Prefetch("evento_causas", queryset=EventoCausa.objects.select_related("causa").order_by("orden", "evento_causa_id")),
                Prefetch("evento_controles", queryset=EventoControl.objects.select_related("control").order_by("orden", "evento_control_id")),
                Prefetch(
                    "cuentas_contables",
                    queryset=EventoCuentaContable.objects.select_related("cuenta", "cuenta_valor").order_by("orden", "evento_cuenta_id"),
                ),
                Prefetch(
                    "distribuciones_linea",
                    queryset=EventoDistribucionLinea.objects.select_related("linea_valor").order_by("evento_distribucion_id"),
                ),
                Prefetch(
                    "caracteristicas",
                    queryset=EntidadCaracteristica.objects.select_related("valor_catalogo").order_by("orden", "entidad_caracteristica_id"),
                ),
            )
            .order_by("-fecha_registro", "-evento_id")
        )

    @staticmethod
    def obtener_detalle(evento_id: int):
        return EventoSelector.obtener_base().filter(evento_id=evento_id).first()
