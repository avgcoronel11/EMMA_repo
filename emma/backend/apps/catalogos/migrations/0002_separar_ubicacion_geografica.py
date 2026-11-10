"""Separa el catálogo geográfico histórico por nivel sin perder jerarquía."""

from django.db import migrations


CATALOGOS = {
    1: ("PAIS", "País"),
    2: ("DEPARTAMENTO", "Departamento"),
    3: ("CIUDAD", "Ciudad"),
}


def separar_ubicacion_geografica(apps, schema_editor):
    Catalogo = apps.get_model("catalogos", "Catalogo")
    CatalogoValor = apps.get_model("catalogos", "CatalogoValor")

    origen = Catalogo.objects.filter(codigo_catalogo="UBICACION_GEOGRAFICA").first()
    if origen is None:
        return

    destinos = {}
    for nivel, (codigo, nombre) in CATALOGOS.items():
        destino, _ = Catalogo.objects.get_or_create(
            codigo_catalogo=codigo,
            defaults={"nombre": nombre, "descripcion": f"Catálogo de {nombre.lower()} para Eventos", "activo": True},
        )
        if not destino.activo:
            destino.activo = True
            destino.save(update_fields=["activo"])
        destinos[nivel] = destino

    for nivel, destino in destinos.items():
        CatalogoValor.objects.filter(catalogo=origen, nivel=nivel).update(catalogo=destino)

    origen.activo = False
    origen.save(update_fields=["activo"])


def reunir_ubicacion_geografica(apps, schema_editor):
    Catalogo = apps.get_model("catalogos", "Catalogo")
    CatalogoValor = apps.get_model("catalogos", "CatalogoValor")

    origen = Catalogo.objects.filter(codigo_catalogo="UBICACION_GEOGRAFICA").first()
    if origen is None:
        return
    for nivel, (codigo, _) in CATALOGOS.items():
        destino = Catalogo.objects.filter(codigo_catalogo=codigo).first()
        if destino:
            CatalogoValor.objects.filter(catalogo=destino, nivel=nivel).update(catalogo=origen)
    origen.activo = True
    origen.save(update_fields=["activo"])


class Migration(migrations.Migration):
    dependencies = [("catalogos", "0001_initial")]

    operations = [migrations.RunPython(separar_ubicacion_geografica, reunir_ubicacion_geografica)]
