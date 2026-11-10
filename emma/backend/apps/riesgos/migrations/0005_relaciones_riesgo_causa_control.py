from django.db import migrations, models
import django.db.models.deletion


def migrar_causas_historicas(apps, schema_editor):
    Causa = apps.get_model("riesgos", "Causa")
    RiesgoCausa = apps.get_model("riesgos", "RiesgoCausa")
    for causa_id, riesgo_id in Causa.objects.exclude(riesgo_id__isnull=True).values_list("causa_id", "riesgo_id").iterator():
        RiesgoCausa.objects.get_or_create(riesgo_id=riesgo_id, causa_id=causa_id)


def revertir_causas_historicas(apps, schema_editor):
    # Las FKs históricas nunca se eliminan en esta migración; no hay reversión de datos que hacer.
    pass


class Migration(migrations.Migration):
    dependencies = [("riesgos", "0004_valoraciones_historicas")]

    operations = [
        migrations.CreateModel(
            name="RiesgoCausa",
            fields=[
                ("riesgo_causa_id", models.BigAutoField(primary_key=True, serialize=False)),
                ("causa", models.ForeignKey(db_column="causa_id", on_delete=django.db.models.deletion.PROTECT, related_name="riesgo_asociaciones", to="riesgos.causa")),
                ("riesgo", models.ForeignKey(db_column="riesgo_id", on_delete=django.db.models.deletion.PROTECT, related_name="causa_asociaciones", to="riesgos.riesgo")),
            ],
            options={"db_table": "riesgo_causa"},
        ),
        migrations.CreateModel(
            name="RiesgoCausaControl",
            fields=[
                ("riesgo_causa_control_id", models.BigAutoField(primary_key=True, serialize=False)),
                ("control", models.ForeignKey(db_column="control_id", on_delete=django.db.models.deletion.PROTECT, related_name="causa_asociaciones", to="riesgos.control")),
                ("riesgo_causa", models.ForeignKey(db_column="riesgo_causa_id", on_delete=django.db.models.deletion.PROTECT, related_name="control_asociaciones", to="riesgos.riesgocausa")),
            ],
            options={"db_table": "riesgo_causa_control"},
        ),
        migrations.AddConstraint(model_name="riesgocausa", constraint=models.UniqueConstraint(fields=("riesgo", "causa"), name="uq_riesgo_causa")),
        migrations.AddConstraint(model_name="riesgocausacontrol", constraint=models.UniqueConstraint(fields=("riesgo_causa", "control"), name="uq_riesgo_causa_control")),
        migrations.RunPython(migrar_causas_historicas, revertir_causas_historicas),
    ]
