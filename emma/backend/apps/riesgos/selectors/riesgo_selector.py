"""Risk query helpers."""

from django.db.models import Prefetch

from backend.apps.riesgos.models import Causa, Control, Riesgo, RiesgoCausa, RiesgoCausaControl, RiesgoProceso


class RiesgoSelector:
    @staticmethod
    def obtener_activos():
        return RiesgoSelector.obtener_base().exclude(estado__iexact="Inactivo")

    @staticmethod
    def obtener_base(*, incluir_relaciones_puente=False):
        procesos = RiesgoProceso.objects.select_related("proceso").order_by("-principal", "proceso_id")
        causas = Causa.objects.order_by("codigo_causa", "causa_id")
        controles = Control.objects.select_related("control_generico_valor").order_by(
            "codigo_control",
            "control_id",
        )
        asociaciones_control = RiesgoCausaControl.objects.select_related(
            "control__control_generico_valor"
        ).order_by("control_id")
        asociaciones_causa = RiesgoCausa.objects.select_related("causa").prefetch_related(
            Prefetch("control_asociaciones", queryset=asociaciones_control)
        ).order_by("causa_id")
        prefetches = [
            Prefetch("riesgo_procesos", queryset=procesos),
            Prefetch("causas", queryset=causas),
            Prefetch("controles", queryset=controles),
            "caracteristicas__valor_catalogo",
        ]
        # Estas relaciones solo se serializan en el detalle. Evitar precargarlas
        # en el listado conserva el contrato de consultas y no introduce trabajo
        # adicional por cada página de riesgos.
        if incluir_relaciones_puente:
            prefetches.append(Prefetch("causa_asociaciones", queryset=asociaciones_causa))

        return (
            Riesgo.objects.select_related(
                "riesgo_generico",
                "usuario_inactivacion",
                "usuario_ultima_edicion",
            )
            .prefetch_related(*prefetches)
            .order_by("codigo_riesgo", "riesgo_id")
        )

    @staticmethod
    def obtener_detalle(riesgo_id: int):
        return RiesgoSelector.obtener_base(incluir_relaciones_puente=True).filter(riesgo_id=riesgo_id).first()
