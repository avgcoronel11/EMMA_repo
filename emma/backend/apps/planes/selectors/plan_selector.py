"""Read queries for action plans."""

from backend.apps.planes.models import PlanAccion


class PlanSelector:
    @staticmethod
    def obtener_base():
        return (
            PlanAccion.objects.select_related("evento", "control")
            .order_by("-fecha_inicio", "-plan_id")
        )

    @staticmethod
    def obtener_detalle(plan_id: int):
        return PlanSelector.obtener_base().filter(plan_id=plan_id).first()
