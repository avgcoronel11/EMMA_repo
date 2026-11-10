# Motor de Riesgos — implementación Tarea 3

**Estado:** reglas de Tarea 3 implementadas en backend.

## Datos persistidos

`RIESGO` incorpora entradas trazables de probabilidad: `exposicion`,
`complejidad`, `condiciones_entorno`, `grado_ocurrencia`, `eventos_riesgo` y
`poblacion_expuesta`. Conserva además los siete impactos y los resultados de
la valoración inherente y residual.

`CONTROL` incorpora `d1` a `d4` y `o1` a `o5`. Todos son opcionales para no
alterar controles históricos. Un control histórico sin las nueve respuestas
mantiene sus calificaciones existentes.

## Probabilidad inherente

El servicio calcula y devuelve los tres componentes de Tarea 3:

1. Cualitativo: promedio redondeado de exposición, complejidad y entorno.
2. Ocurrencia: equivalencia del grado de ocurrencia.
3. Histórico: eventos de riesgo / población expuesta, con los límites
   estrictos definidos en AJ12. Las fronteras 1%, 5%, 10% y 15% son Muy Baja.

El resultado inherente es el mayor de esos tres niveles; no acepta un nivel
precalculado como sustituto. Para la probabilidad histórica se aplican
comparaciones estrictas: `>15 %` es nivel 5; `>10 % y <15 %`, nivel 4;
`>5 % y <10 %`, nivel 3; `>1 % y <5 %`, nivel 2. Las fronteras exactas 1 %,
5 %, 10 % y 15 % recaen en nivel 1 por el valor por defecto de la fórmula
aprobada.

La media cualitativa usa tres niveles enteros y se divide entre tres, por lo
que solo produce fracciones `.0`, `.333…` o `.666…`. Aunque `REDONDEAR` de
Excel y `round()` de Python difieren en valores exactamente `.5`, esa
diferencia no se presenta con las entradas actuales y no motivó un cambio de
redondeo.

## Impacto inherente

El motor exige las siete dimensiones: Impacto Legal, Impacto Reputacional,
Impacto servicio al cliente, Información, Continuidad, Contagio y Financiero.
Cada una se resuelve con `CFG_NIVEL_IMPACTO`; solo son válidos niveles de 1 a
5. El impacto final es el mayor. Las filas técnicas activas de nivel 0 no se
aceptan como resultado de una valoración nueva.

## Evaluación de controles

Endpoint para un formulario de interfaz futuro:

```http
PATCH /api/v1/riesgos/{riesgo_id}/controles/{control_id}/evaluacion/
```

Puede recibir respuestas parciales `d1`…`d4`, `o1`…`o5`. Los valores de D son
`Sí` o `No`; O1…O4 aceptan `Sí` o `No`; O5 acepta `Sí`, `No` o `NA`.

Al tener las nueve respuestas el backend calcula exclusivamente:

- `cumple_diseno`: Sí solo con las cuatro D en Sí.
- `cumple_oper`: O1 No, O2/O3/O4 Sí y O5 No o NA.
- `falla_vpr`: No solo si diseño y operatividad son Sí.
- `efectividad`: cruce Tarea 3 de tipo, naturaleza y falla VPR.

## Riesgo residual

Tarea 3 define que solo controles activos participan; preventivos reducen
probabilidad; correctivos reducen impacto y detectivos se usan únicamente si
el correctivo no reduce. Fuerte y Moderado pesan 1; Débil pesa 0. Para cada
tipo el denominador es el total de controles activos del riesgo. Los umbrales
son: `> 0,20` baja 2; `>= 0,10` baja 1; menor baja 0.

La definición funcional confirmada conserva los niveles entre 1 y 5:

```text
Probabilidad residual = max(1, probabilidad inherente - reducción preventiva)
Impacto residual = max(1, impacto inherente - reducción correctiva)
                    o, si esta es 0, reducción detectiva
```

No se suman correctivos y detectivos. Sin controles activos, los tres valores
residuales son iguales a los inherentes. El backend obtiene las etiquetas y
consulta `CFG_SEVERIDAD`, luego persiste probabilidad, impacto y severidad
residuales. Se puede solicitar expresamente mediante:

```http
POST /api/v1/riesgos/{riesgo_id}/recalcular-residual/
```

## Migración y pruebas

La migración `riesgos.0003_motor_riesgo_tarea_3` agrega únicamente columnas
nulas y no modifica registros históricos.

Antes de la regla residual, `python manage.py test backend.apps.riesgos`
finalizó con 20 pruebas correctas. La nueva ejecución no pudo completar porque
PostgreSQL Azure agotó el tiempo de conexión durante la creación de
`test_emma_db`; no se modificaron datos de producción.
