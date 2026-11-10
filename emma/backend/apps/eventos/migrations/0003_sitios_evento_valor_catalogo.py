import django.db.models.deletion
from django.db import migrations, models


def vincular_sitios_legacy(apps, schema_editor):
    Evento = apps.get_model("eventos", "EventoRiesgo")
    Valor = apps.get_model("catalogos", "CatalogoValor")
    for evento in Evento.objects.all().iterator(chunk_size=500):
        changes = []
        for nombre, valor_field in (
            ("sitio_ocurrencia", "sitio_ocurrencia_valor_id"),
            ("sitio_deteccion", "sitio_deteccion_valor_id"),
        ):
            texto = getattr(evento, nombre)
            if not texto:
                continue
            matches = list(Valor.objects.filter(catalogo__codigo_catalogo__in=("OFICINA", "GERENCIA_EVENTO"), descripcion=texto, activo=True).values_list("valor_id", flat=True)[:2])
            if len(matches) == 1:
                setattr(evento, valor_field, matches[0])
                changes.append(valor_field)
        if changes:
            evento.save(update_fields=changes)


class Migration(migrations.Migration):
    dependencies = [
        ("catalogos", "0003_catalogovalor_ubicacion_oficina"),
        ("eventos", "0002_eventoriesgo_nombre_evento_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="eventoriesgo",
            name="sitio_ocurrencia_valor",
            field=models.ForeignKey(blank=True, db_column="sitio_ocurrencia_valor_id", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="eventos_ocurrencia", to="catalogos.catalogovalor"),
        ),
        migrations.AddField(
            model_name="eventoriesgo",
            name="sitio_deteccion_valor",
            field=models.ForeignKey(blank=True, db_column="sitio_deteccion_valor_id", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="eventos_deteccion", to="catalogos.catalogovalor"),
        ),
        migrations.RunPython(vincular_sitios_legacy, migrations.RunPython.noop),
    ]
