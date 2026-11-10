from django.db import migrations, models


def separar_datos_oficina(apps, schema_editor):
    CatalogoValor = apps.get_model("catalogos", "CatalogoValor")
    oficinas = CatalogoValor.objects.filter(catalogo_id=32)
    for oficina in oficinas.iterator(chunk_size=500):
        metadata = oficina.metadata_jsonb if isinstance(oficina.metadata_jsonb, dict) else {}
        oficina.direccion = metadata.get("direccion") or None
        oficina.ciudad = metadata.get("ciudad") or None
        oficina.departamento = metadata.get("departamento") or None
        oficina.metadata_jsonb = {k: v for k, v in metadata.items() if k not in {"direccion", "ciudad", "departamento"}} or None
        oficina.save(update_fields=["direccion", "ciudad", "departamento", "metadata_jsonb"])


class Migration(migrations.Migration):
    dependencies = [("catalogos", "0002_separar_ubicacion_geografica")]

    operations = [
        migrations.AddField("catalogovalor", "direccion", models.TextField(blank=True, null=True)),
        migrations.AddField("catalogovalor", "ciudad", models.CharField(blank=True, max_length=150, null=True)),
        migrations.AddField("catalogovalor", "departamento", models.CharField(blank=True, max_length=150, null=True)),
        migrations.RunPython(separar_datos_oficina, migrations.RunPython.noop),
    ]
