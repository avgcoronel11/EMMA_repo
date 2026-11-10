"""Generación transaccional de códigos para Causas y Controles."""

from django.db import connection

from backend.apps.riesgos.models import Causa, Control


def _siguiente(*, modelo, tabla, columna, prefijo, secuencia, bloqueo):
    """Obtiene un código consecutivo dentro de la transacción llamadora."""
    patron = f"^{prefijo}([0-9]+)$"
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [bloqueo])
        cursor.execute(
            f"SELECT COALESCE(MAX((substring({columna} from %s))::bigint), 0) FROM {tabla} WHERE {columna} ~ %s",
            [patron, patron],
        )
        maximo = cursor.fetchone()[0]
        cursor.execute("SELECT nextval(%s::regclass)", [secuencia])
        consecutivo = cursor.fetchone()[0]
        if consecutivo <= maximo:
            cursor.execute("SELECT setval(%s::regclass, %s, true)", [secuencia, maximo])
            cursor.execute("SELECT nextval(%s::regclass)", [secuencia])
            consecutivo = cursor.fetchone()[0]
        while modelo.objects.filter(**{columna: f"{prefijo}{consecutivo}"}).exists():
            cursor.execute("SELECT nextval(%s::regclass)", [secuencia])
            consecutivo = cursor.fetchone()[0]
    return f"{prefijo}{consecutivo}"


def generar_siguiente_codigo_causa():
    return _siguiente(modelo=Causa, tabla="causa", columna="codigo_causa", prefijo="C", secuencia="causa_codigo_causa_seq", bloqueo=4_004_001)


def generar_siguiente_codigo_control():
    return _siguiente(modelo=Control, tabla="control", columna="codigo_control", prefijo="CT", secuencia="control_codigo_control_seq", bloqueo=4_004_002)
