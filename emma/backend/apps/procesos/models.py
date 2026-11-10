from django.db import models


class CatProceso(models.Model):
    """Jerarquia de procesos y estructura organizacional."""

    proceso_id = models.BigAutoField(primary_key=True)
    parent_proceso = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="hijos",
        db_column="parent_proceso_id",
    )
    vicepresidencia = models.CharField(max_length=250, null=True, blank=True)
    proceso_nivel0 = models.CharField(max_length=250, null=True, blank=True)
    proceso_nivel1 = models.CharField(max_length=250, null=True, blank=True)
    proceso_nivel2 = models.CharField(max_length=250, null=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    macroproceso = models.CharField(max_length=255, null=True, blank=True)
    linea = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "cat_proceso"

    def __str__(self):
        return self.proceso_nivel1 or self.proceso_nivel0 or f"Proceso {self.proceso_id}"
