"""Generación transaccional del código de negocio GR."""

from django.db import connection

from backend.apps.riesgos.models import Riesgo


NOMBRE_SECUENCIA_GR = "riesgo_codigo_gr_seq"
_BLOQUEO_ADVISORY_GR = 918_204_731


def generar_siguiente_codigo_gr() -> tuple[int, str]:
    """Obtiene el siguiente GR disponible sin cambiar códigos históricos.

    La secuencia de PostgreSQL resuelve la concurrencia. El bloqueo advisory
    mantiene atómica la sincronización con códigos GR que puedan provenir de
    cargas históricas, y la verificación final incluye toda la columna
    ``codigo_riesgo``.

    Debe ejecutarse dentro de una transacción atómica que incluya la creación
    del riesgo, para que el bloqueo viva hasta que se guarde el registro.
    """

    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [_BLOQUEO_ADVISORY_GR])
        cursor.execute(
            """
            SELECT COALESCE(MAX((substring(codigo_riesgo from '^GR([0-9]+)$'))::bigint), 0)
            FROM riesgo
            WHERE codigo_riesgo ~ '^GR[0-9]+$'
            """
        )
        maximo_existente = cursor.fetchone()[0]

        cursor.execute("SELECT nextval(%s::regclass)", [NOMBRE_SECUENCIA_GR])
        consecutivo = cursor.fetchone()[0]

        # Una carga histórica posterior a la migración puede traer un GR mayor
        # que el valor actual de la secuencia. Se sincroniza antes de generar.
        if consecutivo <= maximo_existente:
            cursor.execute(
                "SELECT setval(%s::regclass, %s, true)",
                [NOMBRE_SECUENCIA_GR, maximo_existente],
            )
            cursor.execute("SELECT nextval(%s::regclass)", [NOMBRE_SECUENCIA_GR])
            consecutivo = cursor.fetchone()[0]

        while Riesgo.objects.filter(codigo_riesgo=f"GR{consecutivo}").exists():
            cursor.execute("SELECT nextval(%s::regclass)", [NOMBRE_SECUENCIA_GR])
            consecutivo = cursor.fetchone()[0]

    return consecutivo, f"GR{consecutivo}"
