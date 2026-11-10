from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("riesgos", "0003_motor_riesgo_tarea_3"), ("usuarios", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="ValoracionRiesgo",
            fields=[
                ("valoracion_riesgo_id", models.BigAutoField(primary_key=True, serialize=False)),
                ("version", models.PositiveIntegerField()), ("fecha_valoracion", models.DateTimeField()),
                ("datos_entrada", models.JSONField(blank=True, null=True)),
                ("prob_inherente_nivel", models.SmallIntegerField(blank=True, null=True)), ("prob_inherente_etiqueta", models.CharField(blank=True, max_length=50, null=True)),
                ("impacto_inherente_nivel", models.SmallIntegerField(blank=True, null=True)), ("impacto_inherente_etiqueta", models.CharField(blank=True, max_length=50, null=True)),
                ("severidad_inherente", models.CharField(blank=True, max_length=80, null=True)), ("prob_residual_nivel", models.SmallIntegerField(blank=True, null=True)),
                ("prob_residual_etiqueta", models.CharField(blank=True, max_length=50, null=True)), ("impacto_residual_nivel", models.SmallIntegerField(blank=True, null=True)),
                ("impacto_residual_etiqueta", models.CharField(blank=True, max_length=50, null=True)), ("severidad_residual", models.CharField(blank=True, max_length=80, null=True)),
                ("riesgo", models.ForeignKey(db_column="riesgo_id", on_delete=django.db.models.deletion.PROTECT, related_name="valoraciones", to="riesgos.riesgo")),
                ("usuario", models.ForeignKey(blank=True, db_column="usuario_id", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="valoraciones_riesgo", to="usuarios.usuario")),
            ], options={"db_table": "valoracion_riesgo", "ordering": ["-version"]},
        ),
        migrations.AddConstraint(model_name="valoracionriesgo", constraint=models.UniqueConstraint(fields=("riesgo", "version"), name="uq_valoracion_riesgo_version")),
        migrations.CreateModel(
            name="ValoracionRiesgoControl",
            fields=[
                ("valoracion_control_id", models.BigAutoField(primary_key=True, serialize=False)), ("control_id_snapshot", models.BigIntegerField(blank=True, null=True)),
                ("codigo_control_snapshot", models.CharField(max_length=100)), ("nombre_control_snapshot", models.TextField()), ("estado_snapshot", models.CharField(blank=True, max_length=30, null=True)),
                ("tipo_control_snapshot", models.CharField(blank=True, max_length=50, null=True)), ("naturaleza_snapshot", models.CharField(blank=True, max_length=80, null=True)),
                ("cumple_diseno_snapshot", models.CharField(blank=True, max_length=10, null=True)), ("cumple_oper_snapshot", models.CharField(blank=True, max_length=10, null=True)),
                ("falla_vpr_snapshot", models.CharField(blank=True, max_length=10, null=True)), ("efectividad_snapshot", models.CharField(blank=True, max_length=50, null=True)),
                ("aporte_preventivo", models.SmallIntegerField(default=0)), ("aporte_detectivo", models.SmallIntegerField(default=0)), ("aporte_correctivo", models.SmallIntegerField(default=0)),
                ("control", models.ForeignKey(blank=True, db_column="control_id", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="valoraciones_historicas", to="riesgos.control")),
                ("valoracion", models.ForeignKey(db_column="valoracion_riesgo_id", on_delete=django.db.models.deletion.CASCADE, related_name="controles", to="riesgos.valoracionriesgo")),
            ], options={"db_table": "valoracion_riesgo_control"},
        ),
    ]
