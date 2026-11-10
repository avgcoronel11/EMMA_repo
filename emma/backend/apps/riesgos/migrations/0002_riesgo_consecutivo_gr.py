from django.db import migrations, models


SECUENCIA_GR = "riesgo_codigo_gr_seq"


def inicializar_consecutivo_gr(apps, schema_editor):
    """Conserva históricos y sincroniza la secuencia con el mayor GR válido."""

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE riesgo
            SET consecutivo_gr = (substring(codigo_riesgo from '^GR([0-9]+)$'))::bigint
            WHERE codigo_riesgo ~ '^GR[0-9]+$'
            """
        )
        cursor.execute(
            """
            SELECT MAX((substring(codigo_riesgo from '^GR([0-9]+)$'))::bigint)
            FROM riesgo
            WHERE codigo_riesgo ~ '^GR[0-9]+$'
            """
        )
        maximo = cursor.fetchone()[0]
        if maximo is None:
            cursor.execute("SELECT setval(%s::regclass, %s, false)", [SECUENCIA_GR, 1])
        else:
            cursor.execute("SELECT setval(%s::regclass, %s, true)", [SECUENCIA_GR, maximo])


class Migration(migrations.Migration):
    dependencies = [
        ("riesgos", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="CREATE SEQUENCE riesgo_codigo_gr_seq START WITH 1 MINVALUE 1 NO MAXVALUE;",
            reverse_sql="DROP SEQUENCE riesgo_codigo_gr_seq;",
        ),
        migrations.AddField(
            model_name="riesgo",
            name="consecutivo_gr",
            field=models.BigIntegerField(blank=True, db_index=True, null=True),
        ),
        migrations.RunPython(inicializar_consecutivo_gr, migrations.RunPython.noop),
    ]
