"""Shared helpers for valuation services."""

import re
from datetime import date

from django.db.models import Q


def reglas_vigentes(model, *, fecha: date | None = None, version: str | None = None):
    fecha = fecha or date.today()
    queryset = model.objects.filter(
        activo=True,
        fecha_inicio_vigencia__lte=fecha,
    ).filter(Q(fecha_fin_vigencia__isnull=True) | Q(fecha_fin_vigencia__gte=fecha))
    if version:
        queryset = queryset.filter(version=version)
    return queryset.order_by("-fecha_inicio_vigencia", "-version")


def normalizar_texto(value):
    if value is None:
        return None
    text = " ".join(str(value).strip().split())
    return text or None


def normalizar_concatenado(*values):
    return re.sub(r"\s+", "", "".join(str(value or "") for value in values))


def extraer_nivel(value):
    if value is None:
        return None
    match = re.search(r"\d+", str(value))
    return int(match.group(0)) if match else None
