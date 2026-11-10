from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("riesgos", "0009_riesgo_checklist_y_factor_evento")]

    operations = [
        migrations.RunSQL(
            """
            CREATE SEQUENCE IF NOT EXISTS causa_codigo_causa_seq;
            SELECT setval(
                'causa_codigo_causa_seq',
                GREATEST(COALESCE(MAX((substring(codigo_causa from '^C([0-9]+)$'))::bigint), 0), 1),
                COALESCE(MAX((substring(codigo_causa from '^C([0-9]+)$'))::bigint), 0) > 0
            ) FROM causa WHERE codigo_causa ~ '^C[0-9]+$';
            """,
            "DROP SEQUENCE IF EXISTS causa_codigo_causa_seq;",
        ),
        migrations.RunSQL(
            """
            CREATE SEQUENCE IF NOT EXISTS control_codigo_control_seq;
            SELECT setval(
                'control_codigo_control_seq',
                GREATEST(COALESCE(MAX((substring(codigo_control from '^CT([0-9]+)$'))::bigint), 0), 1),
                COALESCE(MAX((substring(codigo_control from '^CT([0-9]+)$'))::bigint), 0) > 0
            ) FROM control WHERE codigo_control ~ '^CT[0-9]+$';
            """,
            "DROP SEQUENCE IF EXISTS control_codigo_control_seq;",
        ),
    ]
