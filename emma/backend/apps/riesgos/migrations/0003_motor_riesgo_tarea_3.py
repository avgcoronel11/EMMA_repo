# Generated from the approved Tarea 3 model adjustments.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("riesgos", "0002_riesgo_consecutivo_gr"),
    ]

    operations = [
        migrations.AddField(
            model_name="riesgo",
            name="exposicion",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="riesgo",
            name="complejidad",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="riesgo",
            name="condiciones_entorno",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="riesgo",
            name="grado_ocurrencia",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="riesgo",
            name="eventos_riesgo",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="riesgo",
            name="poblacion_expuesta",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        *[
            migrations.AddField(
                model_name="control",
                name=field_name,
                field=models.CharField(blank=True, max_length=3, null=True),
            )
            for field_name in ("d1", "d2", "d3", "d4", "o1", "o2", "o3", "o4", "o5")
        ],
    ]
