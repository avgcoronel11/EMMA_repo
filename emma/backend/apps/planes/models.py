from django.db import models


class PlanAccion(models.Model):
    """Planes de accion asociados a eventos."""

    plan_id = models.BigAutoField(primary_key=True)
    evento = models.ForeignKey(
        "eventos.EventoRiesgo",
        on_delete=models.PROTECT,
        related_name="planes_accion",
        db_column="evento_id",
    )
    codigo_plan = models.CharField(max_length=80, unique=True)
    nombre_evento_snapshot = models.TextField()
    descripcion_accion = models.TextField()
    tipo_accion = models.CharField(max_length=50)
    equipo_responsable = models.CharField(max_length=250, null=True, blank=True)
    fecha_inicio = models.DateField()
    fecha_cierre = models.DateField()
    estado_plan = models.CharField(max_length=50)
    avance_plan = models.SmallIntegerField()
    control = models.ForeignKey(
        "riesgos.Control",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="planes_accion",
        db_column="control_id",
    )
    evidencia_texto = models.TextField(null=True, blank=True)
    observaciones_plan = models.TextField(null=True, blank=True)
    verificacion_control_interno = models.CharField(max_length=50, null=True, blank=True)
    dias_cierre_evento = models.IntegerField(null=True, blank=True)
    dias_plan = models.IntegerField(null=True, blank=True)
    fecha_descubrimiento_evento = models.DateField(null=True, blank=True)
    fecha_inicio_evento = models.DateField(null=True, blank=True)
    fecha_cierre_evento = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "plan_accion"

    def __str__(self):
        return self.codigo_plan
