"""Read queries for audit records."""

from backend.apps.compartido.models import Auditoria


class AuditoriaSelector:
    @staticmethod
    def obtener_base():
        return (
            Auditoria.objects.select_related("usuario")
            .order_by("-fecha_cambio", "-auditoria_id")
        )

    @staticmethod
    def obtener_detalle(auditoria_id: int):
        return AuditoriaSelector.obtener_base().filter(auditoria_id=auditoria_id).first()
