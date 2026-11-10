"""Read queries for attachment metadata."""

from backend.apps.compartido.models import Adjunto


class AdjuntoSelector:
    @staticmethod
    def obtener_base():
        return (
            Adjunto.objects.select_related("evento", "plan", "usuario_carga")
            .order_by("-fecha_carga", "-adjunto_id")
        )

    @staticmethod
    def obtener_detalle(adjunto_id: int):
        return AdjuntoSelector.obtener_base().filter(adjunto_id=adjunto_id).first()
