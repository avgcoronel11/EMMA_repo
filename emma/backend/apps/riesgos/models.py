from django.db import models


class Riesgo(models.Model):
    """Registro maestro y vigente de cada riesgo."""

    riesgo_id = models.BigAutoField(primary_key=True)
    # Los registros históricos pueden no tener código GR; en ese caso se conserva
    # el código original y este consecutivo permanece nulo.
    consecutivo_gr = models.BigIntegerField(null=True, blank=True, db_index=True)
    codigo_riesgo = models.CharField(max_length=30, unique=True)
    nombre_riesgo = models.TextField()
    codigo_referencia_saro = models.CharField(max_length=100, null=True, blank=True)
    ciclo = models.CharField(max_length=100, null=True, blank=True)
    riesgo_generico = models.ForeignKey(
        "catalogos.RiesgoGenerico",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="riesgos",
        db_column="riesgo_generico_id",
    )
    riesgo_homologado = models.CharField(max_length=150, null=True, blank=True)
    frente_riesgo_asociado = models.JSONField(default=list, blank=True)
    checklist_riesgo = models.JSONField(default=list, blank=True)
    factor_riesgo_tipo_evento = models.JSONField(default=list, blank=True)
    control_cambios = models.CharField(
        max_length=10,
        choices=(("Nuevo", "Nuevo"), ("Antiguo", "Antiguo")),
        null=True,
        blank=True,
    )
    frecuencia = models.CharField(
        max_length=40,
        choices=(
            ("Anual", "Anual"), ("Bimestral", "Bimestral"), ("Bisemanal", "Bisemanal"),
            ("Múltiples veces al día", "Múltiples veces al día"), ("Diario", "Diario"),
            ("Eventual", "Eventual"), ("Mensual", "Mensual"), ("Quincenal", "Quincenal"),
            ("Semanal", "Semanal"), ("Semestral", "Semestral"), ("Trimestral", "Trimestral"),
            ("Cuatrimestral", "Cuatrimestral"), ("Permanente", "Permanente"),
        ),
        null=True,
        blank=True,
    )
    detalle_frecuencia = models.TextField(null=True, blank=True)
    subfactor_riesgo = models.CharField(max_length=200, null=True, blank=True)
    descripcion_proceso = models.TextField(null=True, blank=True)
    linea = models.CharField(max_length=150, null=True, blank=True)
    macroproceso = models.CharField(max_length=200, null=True, blank=True)
    dueno_proceso = models.CharField(max_length=250, null=True, blank=True)

    # Entradas del motor de riesgo inherente. Son nulas para conservar los
    # registros históricos que no fueron valorados con la metodología actual.
    exposicion = models.CharField(max_length=255, null=True, blank=True)
    complejidad = models.CharField(max_length=255, null=True, blank=True)
    condiciones_entorno = models.CharField(max_length=255, null=True, blank=True)
    grado_ocurrencia = models.CharField(max_length=255, null=True, blank=True)
    eventos_riesgo = models.PositiveIntegerField(null=True, blank=True)
    poblacion_expuesta = models.PositiveIntegerField(null=True, blank=True)

    impacto_legal = models.CharField(max_length=50, null=True, blank=True)
    impacto_reputacional = models.CharField(max_length=50, null=True, blank=True)
    impacto_servicio_cliente = models.CharField(max_length=50, null=True, blank=True)
    impacto_informacion = models.CharField(max_length=50, null=True, blank=True)
    impacto_continuidad = models.CharField(max_length=50, null=True, blank=True)
    impacto_contagio = models.CharField(max_length=50, null=True, blank=True)
    impacto_financiero = models.CharField(max_length=50, null=True, blank=True)

    prob_inherente_etiqueta = models.CharField(max_length=50, null=True, blank=True)
    prob_inherente_nivel = models.SmallIntegerField(null=True, blank=True)
    impacto_inherente_etiqueta = models.CharField(max_length=50, null=True, blank=True)
    impacto_inherente_nivel = models.SmallIntegerField(null=True, blank=True)
    severidad_inherente = models.CharField(max_length=80, null=True, blank=True)

    prob_residual_etiqueta = models.CharField(max_length=50, null=True, blank=True)
    prob_residual_nivel = models.SmallIntegerField(null=True, blank=True)
    impacto_residual_etiqueta = models.CharField(max_length=50, null=True, blank=True)
    impacto_residual_nivel = models.SmallIntegerField(null=True, blank=True)
    severidad_residual = models.CharField(max_length=80, null=True, blank=True)

    estado = models.CharField(max_length=30)
    justificacion_inactivacion = models.TextField(null=True, blank=True)
    fecha_inactivacion = models.DateField(null=True, blank=True)
    usuario_inactivacion = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="riesgos_inactivados",
        db_column="usuario_inactivacion_id",
    )
    usuario_ultima_edicion = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="riesgos_editados",
        db_column="usuario_ultima_edicion_id",
    )
    fecha_ultima_edicion = models.DateTimeField(null=True, blank=True)
    comentario_ultima_edicion = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "riesgo"

    def __str__(self):
        return f"{self.codigo_riesgo} - {self.nombre_riesgo}"


class Causa(models.Model):
    """Maestro de causas, fallas o amenazas asociadas a un riesgo."""

    causa_id = models.BigAutoField(primary_key=True)
    riesgo = models.ForeignKey(
        "riesgos.Riesgo",
        on_delete=models.PROTECT,
        related_name="causas",
        db_column="riesgo_id",
    )
    codigo_causa = models.CharField(max_length=30, unique=True)
    codigo_actual_causa = models.CharField(max_length=100, null=True, blank=True)
    descripcion_causa = models.TextField()
    subfactor = models.CharField(max_length=200, null=True, blank=True)
    linea = models.CharField(max_length=150, null=True, blank=True)
    macroproceso = models.CharField(max_length=200, null=True, blank=True)
    dueno = models.CharField(max_length=250, null=True, blank=True)
    estado = models.CharField(max_length=30)

    class Meta:
        db_table = "causa"

    def __str__(self):
        return f"{self.codigo_causa} - {self.descripcion_causa}"


class RiesgoCausa(models.Model):
    """Asociación vigente e histórica entre un riesgo y una causa maestra."""

    riesgo_causa_id = models.BigAutoField(primary_key=True)
    riesgo = models.ForeignKey("riesgos.Riesgo", on_delete=models.PROTECT, related_name="causa_asociaciones", db_column="riesgo_id")
    causa = models.ForeignKey("riesgos.Causa", on_delete=models.PROTECT, related_name="riesgo_asociaciones", db_column="causa_id")

    class Meta:
        db_table = "riesgo_causa"
        constraints = [models.UniqueConstraint(fields=["riesgo", "causa"], name="uq_riesgo_causa")]


class RiesgoCausaControl(models.Model):
    """Control que mitiga una causa concreta en el contexto de un riesgo."""

    riesgo_causa_control_id = models.BigAutoField(primary_key=True)
    riesgo_causa = models.ForeignKey(RiesgoCausa, on_delete=models.PROTECT, related_name="control_asociaciones", db_column="riesgo_causa_id")
    control = models.ForeignKey("riesgos.Control", on_delete=models.PROTECT, related_name="causa_asociaciones", db_column="control_id")

    class Meta:
        db_table = "riesgo_causa_control"
        constraints = [models.UniqueConstraint(fields=["riesgo_causa", "control"], name="uq_riesgo_causa_control")]


class Control(models.Model):
    """Maestro de controles asociados a los riesgos."""

    control_id = models.BigAutoField(primary_key=True)
    riesgo = models.ForeignKey(
        "riesgos.Riesgo",
        on_delete=models.PROTECT,
        related_name="controles",
        db_column="riesgo_id",
    )
    codigo_control = models.CharField(max_length=30, unique=True)
    codigo_actual_control = models.CharField(max_length=100, null=True, blank=True)
    nombre_control = models.TextField()
    objetivo = models.TextField(null=True, blank=True)
    descripcion_control = models.TextField()
    importancia = models.TextField(null=True, blank=True)
    evidencia = models.TextField(null=True, blank=True)
    ejecutor_texto = models.CharField(max_length=250, null=True, blank=True)
    tipo_control = models.CharField(max_length=50, null=True, blank=True)  # Preventivo/Detectivo/Correctivo
    naturaleza = models.CharField(max_length=80, null=True, blank=True)  # Manual/Dependiente TI/Automatizado
    hyperion_a = models.CharField(max_length=10, null=True, blank=True)
    hyperion_e = models.CharField(max_length=10, null=True, blank=True)
    aplicaciones_adu_ipe = models.TextField(null=True, blank=True)
    cumple_diseno = models.CharField(max_length=10, null=True, blank=True)
    cumple_oper = models.CharField(max_length=10, null=True, blank=True)
    falla_vpr = models.CharField(max_length=10, null=True, blank=True)
    efectividad = models.CharField(max_length=50, null=True, blank=True)
    # Respuestas primarias de la evaluación. Los controles históricos pueden
    # conservarlas nulas junto con sus calificaciones ya migradas.
    d1 = models.CharField(max_length=3, null=True, blank=True)
    d2 = models.CharField(max_length=3, null=True, blank=True)
    d3 = models.CharField(max_length=3, null=True, blank=True)
    d4 = models.CharField(max_length=3, null=True, blank=True)
    o1 = models.CharField(max_length=3, null=True, blank=True)
    o2 = models.CharField(max_length=3, null=True, blank=True)
    o3 = models.CharField(max_length=3, null=True, blank=True)
    o4 = models.CharField(max_length=3, null=True, blank=True)
    o5 = models.CharField(max_length=3, null=True, blank=True)
    estado = models.CharField(max_length=30)
    control_generico_valor = models.ForeignKey(
        "catalogos.CatalogoValor",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="controles_genericos",
        db_column="control_generico_valor_id",
    )

    class Meta:
        db_table = "control"

    def __str__(self):
        return f"{self.codigo_control} - {self.nombre_control}"


class ControlCuentaContable(models.Model):
    """Relación N:M entre controles y cuentas contables activas."""

    control_cuenta_contable_id = models.BigAutoField(primary_key=True)
    control = models.ForeignKey("riesgos.Control", on_delete=models.CASCADE, related_name="cuentas_contables", db_column="control_id")
    cuenta = models.ForeignKey("catalogos.CuentaContable", on_delete=models.PROTECT, related_name="controles", db_column="cuenta_id")

    class Meta:
        db_table = "control_cuenta_contable"
        constraints = [models.UniqueConstraint(fields=["control", "cuenta"], name="uq_control_cuenta_contable")]


class ControlChecklist(models.Model):
    """Valores multiselección de aserciones, atributos y riesgos de un control."""

    class Tipo(models.TextChoices):
        ASERCION = "ASERCION", "Aserción"
        ATRIBUTO = "ATRIBUTO", "Atributo"
        RIESGO = "RIESGO", "Riesgo"

    control_checklist_id = models.BigAutoField(primary_key=True)
    control = models.ForeignKey("riesgos.Control", on_delete=models.CASCADE, related_name="checklists", db_column="control_id")
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    valor = models.CharField(max_length=120)

    class Meta:
        db_table = "control_checklist"
        constraints = [models.UniqueConstraint(fields=["control", "tipo", "valor"], name="uq_control_checklist")]


class RiesgoProceso(models.Model):
    """Puente N:M entre Riesgo y Proceso."""

    pk = models.CompositePrimaryKey("riesgo_id", "proceso_id")
    riesgo = models.ForeignKey(
        "riesgos.Riesgo",
        on_delete=models.CASCADE,
        related_name="riesgo_procesos",
        db_column="riesgo_id",
    )
    proceso = models.ForeignKey(
        "procesos.CatProceso",
        on_delete=models.PROTECT,
        related_name="riesgo_procesos",
        db_column="proceso_id",
    )
    principal = models.BooleanField(null=True, blank=True)

    class Meta:
        db_table = "riesgo_proceso"


class ValoracionRiesgo(models.Model):
    """Resultado inmutable de una ejecución del motor de valoración."""

    valoracion_riesgo_id = models.BigAutoField(primary_key=True)
    riesgo = models.ForeignKey("riesgos.Riesgo", on_delete=models.PROTECT, related_name="valoraciones", db_column="riesgo_id")
    version = models.PositiveIntegerField()
    fecha_valoracion = models.DateTimeField()
    usuario = models.ForeignKey("usuarios.Usuario", on_delete=models.PROTECT, null=True, blank=True, related_name="valoraciones_riesgo", db_column="usuario_id")
    datos_entrada = models.JSONField(null=True, blank=True)
    prob_inherente_nivel = models.SmallIntegerField(null=True, blank=True)
    prob_inherente_etiqueta = models.CharField(max_length=50, null=True, blank=True)
    impacto_inherente_nivel = models.SmallIntegerField(null=True, blank=True)
    impacto_inherente_etiqueta = models.CharField(max_length=50, null=True, blank=True)
    severidad_inherente = models.CharField(max_length=80, null=True, blank=True)
    prob_residual_nivel = models.SmallIntegerField(null=True, blank=True)
    prob_residual_etiqueta = models.CharField(max_length=50, null=True, blank=True)
    impacto_residual_nivel = models.SmallIntegerField(null=True, blank=True)
    impacto_residual_etiqueta = models.CharField(max_length=50, null=True, blank=True)
    severidad_residual = models.CharField(max_length=80, null=True, blank=True)

    class Meta:
        db_table = "valoracion_riesgo"
        constraints = [models.UniqueConstraint(fields=["riesgo", "version"], name="uq_valoracion_riesgo_version")]
        ordering = ["-version"]


class ValoracionRiesgoControl(models.Model):
    """Fotografía del control que participó en una valoración histórica."""

    valoracion_control_id = models.BigAutoField(primary_key=True)
    valoracion = models.ForeignKey(ValoracionRiesgo, on_delete=models.CASCADE, related_name="controles", db_column="valoracion_riesgo_id")
    control = models.ForeignKey("riesgos.Control", on_delete=models.SET_NULL, null=True, blank=True, related_name="valoraciones_historicas", db_column="control_id")
    control_id_snapshot = models.BigIntegerField(null=True, blank=True)
    codigo_control_snapshot = models.CharField(max_length=100)
    nombre_control_snapshot = models.TextField()
    estado_snapshot = models.CharField(max_length=30, null=True, blank=True)
    tipo_control_snapshot = models.CharField(max_length=50, null=True, blank=True)
    naturaleza_snapshot = models.CharField(max_length=80, null=True, blank=True)
    cumple_diseno_snapshot = models.CharField(max_length=10, null=True, blank=True)
    cumple_oper_snapshot = models.CharField(max_length=10, null=True, blank=True)
    falla_vpr_snapshot = models.CharField(max_length=10, null=True, blank=True)
    efectividad_snapshot = models.CharField(max_length=50, null=True, blank=True)
    aporte_preventivo = models.SmallIntegerField(default=0)
    aporte_detectivo = models.SmallIntegerField(default=0)
    aporte_correctivo = models.SmallIntegerField(default=0)

    class Meta:
        db_table = "valoracion_riesgo_control"


class ControlEvaluacionHistorico(models.Model):
    class OrigenRegistro(models.TextChoices):
        OPERACION = "OPERACION", "Operación"
        BACKFILL = "BACKFILL", "Backfill"

    control_evaluacion_historico_id = models.BigAutoField(primary_key=True)
    control = models.ForeignKey("riesgos.Control", on_delete=models.PROTECT, related_name="evaluaciones_historicas", db_column="control_id")
    usuario = models.ForeignKey("usuarios.Usuario", on_delete=models.PROTECT, null=True, blank=True, related_name="evaluaciones_control_historicas", db_column="usuario_id")
    version = models.PositiveIntegerField()
    fecha_evaluacion = models.DateTimeField()
    origen_registro = models.CharField(max_length=20)
    d1 = models.CharField(max_length=3, null=True, blank=True); d2 = models.CharField(max_length=3, null=True, blank=True)
    d3 = models.CharField(max_length=3, null=True, blank=True); d4 = models.CharField(max_length=3, null=True, blank=True)
    o1 = models.CharField(max_length=3, null=True, blank=True); o2 = models.CharField(max_length=3, null=True, blank=True)
    o3 = models.CharField(max_length=3, null=True, blank=True); o4 = models.CharField(max_length=3, null=True, blank=True); o5 = models.CharField(max_length=3, null=True, blank=True)
    cumple_diseno = models.CharField(max_length=10, null=True, blank=True)
    cumple_oper = models.CharField(max_length=10, null=True, blank=True)
    falla_vpr = models.CharField(max_length=10, null=True, blank=True)
    efectividad = models.CharField(max_length=50, null=True, blank=True)
    class Meta:
        db_table = "control_evaluacion_historico"
        constraints = [models.UniqueConstraint(fields=["control", "version"], name="uq_control_evaluacion_historico_version")]
        indexes = [models.Index(fields=["control", "version"], name="ix_control_eval_version"), models.Index(fields=["control", "fecha_evaluacion"], name="ix_control_eval_fecha"), models.Index(fields=["fecha_evaluacion"], name="ix_control_eval_fecha_sola")]


class HistorialRiesgoCausa(models.Model):
    class Evento(models.TextChoices):
        ASSOCIATE = "ASSOCIATE", "Associate"
        DISASSOCIATE = "DISASSOCIATE", "Disassociate"

    class OrigenRegistro(models.TextChoices):
        OPERACION = "OPERACION", "Operación"
        BACKFILL = "BACKFILL", "Backfill"

    historial_riesgo_causa_id = models.BigAutoField(primary_key=True)
    riesgo = models.ForeignKey("riesgos.Riesgo", on_delete=models.PROTECT, related_name="historial_causas", db_column="riesgo_id")
    causa = models.ForeignKey("riesgos.Causa", on_delete=models.PROTECT, related_name="historial_riesgos", db_column="causa_id")
    version = models.PositiveIntegerField(); evento = models.CharField(max_length=20); fecha_evento = models.DateTimeField(); origen_registro = models.CharField(max_length=20)
    usuario = models.ForeignKey("usuarios.Usuario", on_delete=models.PROTECT, null=True, blank=True, related_name="historiales_riesgo_causa", db_column="usuario_id")
    class Meta:
        db_table = "historial_riesgo_causa"
        constraints = [models.UniqueConstraint(fields=["riesgo", "causa", "version"], name="uq_hist_riesgo_causa_version")]
        indexes = [models.Index(fields=["riesgo", "causa", "fecha_evento"], name="ix_hist_rc_contexto_fecha"), models.Index(fields=["riesgo"], name="ix_hist_rc_riesgo"), models.Index(fields=["causa"], name="ix_hist_rc_causa")]


class HistorialRiesgoCausaControl(models.Model):
    class Evento(models.TextChoices):
        ASSOCIATE = "ASSOCIATE", "Associate"
        DISASSOCIATE = "DISASSOCIATE", "Disassociate"

    class OrigenRegistro(models.TextChoices):
        OPERACION = "OPERACION", "Operación"
        BACKFILL = "BACKFILL", "Backfill"

    historial_riesgo_causa_control_id = models.BigAutoField(primary_key=True)
    riesgo = models.ForeignKey("riesgos.Riesgo", on_delete=models.PROTECT, related_name="historial_controles", db_column="riesgo_id")
    causa = models.ForeignKey("riesgos.Causa", on_delete=models.PROTECT, related_name="historial_controles", db_column="causa_id")
    control = models.ForeignKey("riesgos.Control", on_delete=models.PROTECT, related_name="historial_asociaciones", db_column="control_id")
    version = models.PositiveIntegerField(); evento = models.CharField(max_length=20); fecha_evento = models.DateTimeField(); origen_registro = models.CharField(max_length=20)
    usuario = models.ForeignKey("usuarios.Usuario", on_delete=models.PROTECT, null=True, blank=True, related_name="historiales_riesgo_causa_control", db_column="usuario_id")
    class Meta:
        db_table = "historial_riesgo_causa_control"
        constraints = [models.UniqueConstraint(fields=["riesgo", "causa", "control", "version"], name="uq_hist_rcc_version")]
        indexes = [models.Index(fields=["riesgo", "causa", "control", "fecha_evento"], name="ix_hist_rcc_contexto_fecha"), models.Index(fields=["riesgo"], name="ix_hist_rcc_riesgo"), models.Index(fields=["causa"], name="ix_hist_rcc_causa"), models.Index(fields=["control"], name="ix_hist_rcc_control")]
