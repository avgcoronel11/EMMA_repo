from django.db import models


class EventoRiesgo(models.Model):
    """Registro vigente del evento de riesgo."""

    evento_id = models.BigAutoField(primary_key=True)
    id_ocurrencia = models.CharField(max_length=60, unique=True)
    usuario_registro = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="eventos_registrados",
        db_column="usuario_registro_id",
    )
    riesgo = models.ForeignKey(
        "riesgos.Riesgo",
        on_delete=models.PROTECT,
        related_name="eventos",
        db_column="riesgo_id",
    )
    tipo_evento_valor = models.ForeignKey(
        "catalogos.CatalogoValor",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="eventos_tipo",
        db_column="tipo_evento_valor_id",
    )
    orden_cargue = models.IntegerField(null=True, blank=True)

    fecha_registro = models.DateField()
    hora_registro = models.TimeField()
    id_usuario_informador = models.CharField(max_length=150, null=True, blank=True)

    fecha_inicio_evento = models.DateField()
    hora_inicio_evento = models.TimeField(null=True, blank=True)
    fecha_finalizacion_evento = models.DateField(null=True, blank=True)
    hora_finalizacion_evento = models.TimeField(null=True, blank=True)
    fecha_descubrimiento_evento = models.DateField()
    hora_descubrimiento_evento = models.TimeField(null=True, blank=True)

    descripcion_evento = models.TextField()
    nombre_evento = models.CharField(max_length=250, null=True, blank=True)

    # Snapshots: copia del contexto vigente al momento del evento.
    codigo_riesgo_snapshot = models.CharField(max_length=30)
    descripcion_riesgo_snapshot = models.TextField()
    riesgo_generico_snapshot = models.CharField(max_length=250, null=True, blank=True)
    riesgo_asociado_display = models.TextField(null=True, blank=True)
    vicepresidencia_snapshot = models.CharField(max_length=250, null=True, blank=True)
    proceso_snapshot = models.CharField(max_length=250, null=True, blank=True)
    subproceso_snapshot = models.CharField(max_length=250, null=True, blank=True)
    gerencia_duena_snapshot = models.CharField(max_length=250, null=True, blank=True)

    cuantia_estimada = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    cantidad_casos = models.IntegerField(null=True, blank=True)
    tipo_perdida = models.CharField(max_length=120, null=True, blank=True)
    estado_evento = models.CharField(max_length=80)
    divisa = models.CharField(max_length=20, null=True, blank=True)

    cuantia_perdida_bruta = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    cuantia_recuperaciones_total = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    cuantia_recuperada_seguros = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    cuantia_otras_recuperaciones = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    cuantia_perdida_neta = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    tipo_recuperacion = models.JSONField(default=list, blank=True)

    fecha_contabilizacion_evento = models.DateField(null=True, blank=True)
    fecha_recuperacion_evento = models.DateField(null=True, blank=True)
    fecha_cierre_evento = models.DateField(null=True, blank=True)

    evento_ciberseguridad = models.BooleanField(null=True, blank=True)
    evento_alto_impacto = models.BooleanField(null=True, blank=True)

    sitio_ocurrencia = models.CharField(max_length=250, null=True, blank=True)
    sitio_deteccion = models.CharField(max_length=250, null=True, blank=True)
    sitio_ocurrencia_valor = models.ForeignKey(
        "catalogos.CatalogoValor", on_delete=models.PROTECT, null=True, blank=True,
        related_name="eventos_ocurrencia", db_column="sitio_ocurrencia_valor_id",
    )
    sitio_deteccion_valor = models.ForeignKey(
        "catalogos.CatalogoValor", on_delete=models.PROTECT, null=True, blank=True,
        related_name="eventos_deteccion", db_column="sitio_deteccion_valor_id",
    )
    pais_evento = models.CharField(max_length=150, null=True, blank=True)
    departamento_evento = models.CharField(max_length=150, null=True, blank=True)
    ciudad_evento = models.CharField(max_length=150, null=True, blank=True)

    linea_negocio_1 = models.CharField(max_length=200, null=True, blank=True)
    linea_negocio_2 = models.CharField(max_length=200, null=True, blank=True)
    dependencia_contabiliza = models.CharField(max_length=250, null=True, blank=True)
    numero_comprobante_sub_eventos = models.CharField(max_length=150, null=True, blank=True)
    dependencia_contabiliza_recuperacion = models.CharField(max_length=250, null=True, blank=True)
    numero_comprobante_recuperacion = models.CharField(max_length=150, null=True, blank=True)

    class Meta:
        db_table = "evento_riesgo"

    def __str__(self):
        return self.id_ocurrencia


class EventoCausa(models.Model):
    """Causas asociadas al evento, con snapshot de codigo/descripcion."""

    evento_causa_id = models.BigAutoField(primary_key=True)
    evento = models.ForeignKey(
        "eventos.EventoRiesgo",
        on_delete=models.CASCADE,
        related_name="evento_causas",
        db_column="evento_id",
    )
    causa = models.ForeignKey(
        "riesgos.Causa",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evento_causas",
        db_column="causa_id",
    )
    codigo_causa_snapshot = models.CharField(max_length=60, null=True, blank=True)
    descripcion_causa_snapshot = models.TextField()
    es_causa_libre = models.BooleanField(default=False)
    orden = models.SmallIntegerField(null=True, blank=True)

    class Meta:
        db_table = "evento_causa"


class EventoControl(models.Model):
    """Controles asociados al evento, con snapshot de codigo/descripcion."""

    evento_control_id = models.BigAutoField(primary_key=True)
    evento = models.ForeignKey(
        "eventos.EventoRiesgo",
        on_delete=models.CASCADE,
        related_name="evento_controles",
        db_column="evento_id",
    )
    control = models.ForeignKey(
        "riesgos.Control",
        on_delete=models.PROTECT,
        related_name="evento_controles",
        db_column="control_id",
    )
    codigo_control_snapshot = models.CharField(max_length=60)
    descripcion_control_snapshot = models.TextField()
    orden = models.SmallIntegerField(null=True, blank=True)

    class Meta:
        db_table = "evento_control"


class EventoCuentaContable(models.Model):
    """Cuentas contables de perdida y recuperacion del evento."""

    evento_cuenta_id = models.BigAutoField(primary_key=True)
    evento = models.ForeignKey(
        "eventos.EventoRiesgo",
        on_delete=models.CASCADE,
        related_name="cuentas_contables",
        db_column="evento_id",
    )
    tipo_cuenta = models.CharField(max_length=20)
    cuenta_valor = models.ForeignKey(
        "catalogos.CatalogoValor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evento_cuentas_legado",
        db_column="cuenta_valor_id",
    )
    cuenta = models.ForeignKey(
        "catalogos.CuentaContable",
        on_delete=models.PROTECT,
        related_name="eventos_cuenta",
        db_column="cuenta_id",
    )
    codigo_cuenta_snapshot = models.CharField(max_length=60)
    descripcion_cuenta_snapshot = models.CharField(max_length=300)
    orden = models.SmallIntegerField(null=True, blank=True)

    class Meta:
        db_table = "evento_cuenta_contable"


class EventoDistribucionLinea(models.Model):
    """Distribucion porcentual del evento entre lineas de negocio."""

    evento_distribucion_id = models.BigAutoField(primary_key=True)
    evento = models.ForeignKey(
        "eventos.EventoRiesgo",
        on_delete=models.CASCADE,
        related_name="distribuciones_linea",
        db_column="evento_id",
    )
    linea = models.CharField(max_length=200)
    linea_valor = models.ForeignKey(
        "catalogos.CatalogoValor",
        on_delete=models.PROTECT,
        related_name="distribuciones_linea",
        db_column="linea_valor_id",
    )
    linea_snapshot = models.CharField(max_length=500, null=True, blank=True)
    porcentaje = models.DecimalField(max_digits=7, decimal_places=4)

    class Meta:
        db_table = "evento_distribucion_linea"
