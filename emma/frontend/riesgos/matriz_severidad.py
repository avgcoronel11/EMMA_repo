"""Preparación pura de la matriz de severidad vigente para su presentación."""

COLORES = {
    1: "#2196F3",
    2: "#8BC34A",
    3: "#FFEB3B",
    4: "#F44336",
}

# Filas: probabilidad 1..5; columnas: impacto 1..5.
COLOR_MAP_DATA = (
    (1, 1, 2, 3, 4),
    (1, 1, 2, 3, 4),
    (1, 2, 2, 3, 4),
    (1, 2, 3, 3, 4),
    (1, 2, 3, 4, 4),
)

PROBABILIDADES = {
    1: "Muy Baja", 2: "Baja", 3: "Moderada", 4: "Alta", 5: "Muy Alta",
}
IMPACTOS = {
    1: "Inferior", 2: "Menor", 3: "Importante", 4: "Mayor", 5: "Superior",
}


def _nivel(valor):
    """Acepta únicamente un entero de la escala persistida 1..5."""
    try:
        nivel = int(valor)
    except (TypeError, ValueError):
        return None
    return nivel if nivel in range(1, 6) else None


def preparar_matriz_severidad(riesgo):
    """No calcula ni consulta datos: solo convierte la valoración vigente en celdas."""
    riesgo = riesgo or {}
    ri = {
        "probabilidad": _nivel(riesgo.get("prob_inherente_nivel")),
        "impacto": _nivel(riesgo.get("impacto_inherente_nivel")),
        "severidad": riesgo.get("severidad_inherente"),
    }
    rr = {
        "probabilidad": _nivel(riesgo.get("prob_residual_nivel")),
        "impacto": _nivel(riesgo.get("impacto_residual_nivel")),
        "severidad": riesgo.get("severidad_residual"),
    }
    valoracion_valida = all((ri["probabilidad"], ri["impacto"], rr["probabilidad"], rr["impacto"]))

    filas = []
    for nivel_probabilidad, colores_fila in enumerate(COLOR_MAP_DATA, start=1):
        celdas = []
        for nivel_impacto, categoria_color in enumerate(colores_fila, start=1):
            marcadores = []
            if valoracion_valida and (nivel_probabilidad, nivel_impacto) == (ri["probabilidad"], ri["impacto"]):
                marcadores.append({"codigo": "RI", "clase": "ri", "descripcion": "Riesgo inherente"})
            if valoracion_valida and (nivel_probabilidad, nivel_impacto) == (rr["probabilidad"], rr["impacto"]):
                marcadores.append({"codigo": "RR", "clase": "rr", "descripcion": "Riesgo residual"})
            celdas.append({
                "probabilidad": nivel_probabilidad,
                "impacto": nivel_impacto,
                "color": COLORES[categoria_color],
                "marcadores": marcadores,
            })
        filas.append({"nivel": nivel_probabilidad, "etiqueta": PROBABILIDADES[nivel_probabilidad], "celdas": celdas})

    return {
        "valida": valoracion_valida,
        "pendiente": not valoracion_valida,
        "filas": filas,
        "impactos": [{"nivel": nivel, "etiqueta": IMPACTOS[nivel]} for nivel in range(1, 6)],
        "ri": ri,
        "rr": rr,
    }
