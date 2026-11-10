from django.db import models


class FuenteDato(models.Model):
    fuente_id = models.BigAutoField(primary_key=True)
    codigo_fuente = models.CharField(max_length=80, unique=True)
    nombre_fuente = models.CharField(max_length=255)
    frecuencia = models.CharField(max_length=20, null=True, blank=True)
    hoja_principal = models.CharField(max_length=120, null=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "fuente_dato"

    def __str__(self):
        return self.codigo_fuente


class RiesgoGenerico(models.Model):
    riesgo_generico_id = models.BigAutoField(primary_key=True)
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=500)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "riesgo_generico"

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Catalogo(models.Model):
    """Familias de listas reutilizables de EMMA."""

    catalogo_id = models.BigAutoField(primary_key=True)
    codigo_catalogo = models.CharField(max_length=80, unique=True)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "catalogo"

    def __str__(self):
        return self.nombre


class CatalogoValor(models.Model):
    """Opciones disponibles dentro de cada catálogo.

    ``parent_valor`` puede relacionar niveles de catálogos diferentes cuando
    forman una ruta aprobada, por ejemplo País → Departamento → Ciudad.
    """

    valor_id = models.BigAutoField(primary_key=True)
    catalogo = models.ForeignKey(
        "catalogos.Catalogo",
        on_delete=models.PROTECT,
        related_name="valores",
        db_column="catalogo_id",
    )
    codigo = models.CharField(max_length=120, null=True, blank=True)
    descripcion = models.TextField()
    parent_valor = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="hijos",
        db_column="parent_valor_id",
    )
    nivel = models.SmallIntegerField(null=True, blank=True)
    orden = models.IntegerField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    metadata_jsonb = models.JSONField(null=True, blank=True)
    direccion = models.TextField(null=True, blank=True)
    ciudad = models.CharField(max_length=150, null=True, blank=True)
    departamento = models.CharField(max_length=150, null=True, blank=True)

    class Meta:
        db_table = "catalogo_valor"

    def __str__(self):
        return self.descripcion


class EstructuraOrganizacional(models.Model):
    estructura_id = models.BigAutoField(primary_key=True)
    gerencia_direccion = models.CharField(max_length=255)
    cargo_aprobado = models.CharField(max_length=255)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "estructura_organizacional"

    def __str__(self):
        return f"{self.gerencia_direccion} - {self.cargo_aprobado}"


class CuentaContable(models.Model):
    cuenta_id = models.BigAutoField(primary_key=True)
    fuente = models.ForeignKey(
        "catalogos.FuenteDato",
        on_delete=models.PROTECT,
        related_name="cuentas_contables",
        db_column="fuente_id",
    )
    cuenta_10 = models.CharField(max_length=10, null=True, blank=True)
    cuenta_6 = models.CharField(max_length=6, null=True, blank=True)
    descripcion = models.CharField(max_length=500)
    clave_homologacion = models.CharField(max_length=120)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "cuenta_contable"

    @property
    def display_cuenta(self):
        cuenta = self.cuenta_10 or self.cuenta_6 or ""
        return f"{cuenta} - {self.descripcion}".strip(" -")

    @property
    def display_cuenta_6(self):
        return self.cuenta_6 or ""

    def __str__(self):
        return self.display_cuenta


class CfgProbabilidad(models.Model):
    cfg_probabilidad_id = models.BigAutoField(primary_key=True)
    complejidad = models.CharField(max_length=255, null=True, blank=True)
    condiciones_entorno = models.CharField(max_length=255, null=True, blank=True)
    nivel = models.CharField(max_length=100, null=True, blank=True)
    probabilidad_inherente = models.CharField(max_length=255)
    activo = models.BooleanField(default=True)
    version = models.CharField(max_length=30)
    fecha_inicio_vigencia = models.DateField()
    fecha_fin_vigencia = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "cfg_probabilidad"
        constraints = [
            models.UniqueConstraint(
                fields=["version", "complejidad", "condiciones_entorno", "nivel"],
                name="uq_cfg_probabilidad_version_regla",
            ),
        ]

    def __str__(self):
        return f"{self.version} - {self.nivel} - {self.probabilidad_inherente}"


class CfgNivelImpacto(models.Model):
    cfg_impacto_id = models.BigAutoField(primary_key=True)
    nivel = models.CharField(max_length=100)
    tipo_impacto = models.CharField(max_length=100)
    criterio = models.CharField(max_length=2000, null=True, blank=True)
    impacto_inherente = models.CharField(max_length=255, null=True, blank=True)
    activo = models.BooleanField(default=True)
    version = models.CharField(max_length=30)
    fecha_inicio_vigencia = models.DateField()
    fecha_fin_vigencia = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "cfg_nivel_impacto"
        constraints = [
            models.UniqueConstraint(
                fields=["version", "tipo_impacto", "nivel"],
                name="uq_cfg_impacto_version_tipo_nivel",
            ),
        ]

    def __str__(self):
        return f"{self.version} - {self.tipo_impacto} - {self.nivel}"


class CfgSeveridad(models.Model):
    cfg_severidad_id = models.BigAutoField(primary_key=True)
    concatenado = models.CharField(max_length=100)
    severidad = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)
    version = models.CharField(max_length=30)
    fecha_inicio_vigencia = models.DateField()
    fecha_fin_vigencia = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "cfg_severidad"
        constraints = [
            models.UniqueConstraint(
                fields=["version", "concatenado"],
                name="uq_cfg_severidad_version_concatenado",
            ),
        ]

    def __str__(self):
        return f"{self.version} - {self.concatenado} = {self.severidad}"
