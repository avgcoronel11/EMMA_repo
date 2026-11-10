from django.db import models
from django.db.models import Q, CheckConstraint


class CargaFuente(models.Model):
    """Bitacora tecnica de cargas de maestros, catalogos y configuracion."""

    carga_id = models.BigAutoField(primary_key=True)
    fuente = models.ForeignKey(
        "catalogos.FuenteDato",
        on_delete=models.PROTECT,
        related_name="cargas",
        db_column="fuente_id",
    )
    fecha_carga = models.DateTimeField()
    hash_archivo = models.CharField(max_length=128, null=True, blank=True)
    estado = models.CharField(max_length=30)
    registros_leidos = models.IntegerField(null=True, blank=True)
    registros_validos = models.IntegerField(null=True, blank=True)
    registros_rechazados = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "carga_fuente"

    def __str__(self):
        return f"{self.fuente.codigo_fuente} - {self.fecha_carga}"


class EntidadCaracteristica(models.Model):
    """Puente generico para multiselecciones de varias entidades."""

    entidad_caracteristica_id = models.BigAutoField(primary_key=True)
    riesgo = models.ForeignKey(
        "riesgos.Riesgo",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="caracteristicas",
        db_column="riesgo_id",
    )
    control = models.ForeignKey(
        "riesgos.Control",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="caracteristicas",
        db_column="control_id",
    )
    evento = models.ForeignKey(
        "eventos.EventoRiesgo",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="caracteristicas",
        db_column="evento_id",
    )
    plan = models.ForeignKey(
        "planes.PlanAccion",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="caracteristicas",
        db_column="plan_id",
    )
    valor_catalogo = models.ForeignKey(
        "catalogos.CatalogoValor",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="entidades_caracteristicas",
        db_column="valor_catalogo_id",
    )
    valor_libre = models.TextField(null=True, blank=True)
    valor_snapshot = models.TextField(null=True, blank=True)
    orden = models.SmallIntegerField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "entidad_caracteristica"
        constraints = [
            CheckConstraint(
                condition=(
                    Q(riesgo__isnull=False, control__isnull=True, evento__isnull=True, plan__isnull=True)
                    | Q(riesgo__isnull=True, control__isnull=False, evento__isnull=True, plan__isnull=True)
                    | Q(riesgo__isnull=True, control__isnull=True, evento__isnull=False, plan__isnull=True)
                    | Q(riesgo__isnull=True, control__isnull=True, evento__isnull=True, plan__isnull=False)
                ),
                name="ck_entidad_caracteristica_un_propietario",
            )
        ]

    def __str__(self):
        return self.valor_snapshot or self.valor_libre or f"Caracteristica {self.pk}"


class Adjunto(models.Model):
    """Metadata de archivos/evidencias almacenados fuera de la base de datos."""

    adjunto_id = models.BigAutoField(primary_key=True)
    evento = models.ForeignKey(
        "eventos.EventoRiesgo",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="adjuntos",
        db_column="evento_id",
    )
    plan = models.ForeignKey(
        "planes.PlanAccion",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="adjuntos",
        db_column="plan_id",
    )
    nombre_archivo = models.CharField(max_length=500)
    ruta_storage = models.TextField()  # URI/ruta logica en Azure Storage
    content_type = models.CharField(max_length=150, null=True, blank=True)
    tamano_bytes = models.BigIntegerField(null=True, blank=True)
    usuario_carga = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="adjuntos_cargados",
        db_column="usuario_carga_id",
    )
    fecha_carga = models.DateTimeField()

    class Meta:
        db_table = "adjunto"
        constraints = [
            CheckConstraint(
                condition=(
                    Q(evento__isnull=False, plan__isnull=True)
                    | Q(evento__isnull=True, plan__isnull=False)
                ),
                name="ck_adjunto_un_solo_dueno",
            )
        ]

    def __str__(self):
        return self.nombre_archivo


class Auditoria(models.Model):
    """Historico inmutable de cambios relevantes."""

    auditoria_id = models.BigAutoField(primary_key=True)
    entidad = models.CharField(max_length=80)  # ej. 'RIESGO', 'EVENTO_RIESGO', 'PLAN_ACCION'
    entidad_id = models.BigIntegerField()
    codigo_negocio_snapshot = models.CharField(max_length=100, null=True, blank=True)
    version = models.IntegerField(null=True, blank=True)
    accion = models.CharField(max_length=80)  # INSERT/UPDATE/INACTIVATE/CLOSE/etc.
    usuario = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="auditorias",
        db_column="usuario_id",
    )
    fecha_cambio = models.DateTimeField()
    motivo_modificacion = models.TextField(null=True, blank=True)
    datos_anteriores = models.JSONField(null=True, blank=True)
    datos_nuevos = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "auditoria"
        verbose_name_plural = "Auditorias"
