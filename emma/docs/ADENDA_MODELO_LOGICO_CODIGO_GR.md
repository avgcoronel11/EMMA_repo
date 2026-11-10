# Adenda al modelo lógico: código GR de Riesgo

**Decisión funcional aprobada:** 2026-10-21  
**Entidad afectada:** `RIESGO`

## Campos

| Campo | Tipo lógico | Nulable | Regla |
| --- | --- | --- | --- |
| `riesgo_id` | bigint | No | Identificador técnico; no genera el código GR. |
| `consecutivo_gr` | bigint | Sí | Consecutivo numérico generado por PostgreSQL para riesgos nuevos. Un histórico cuyo código no cumpla el formato GR puede conservar este campo en `NULL`. |
| `codigo_riesgo` | varchar(30) | No | Código de negocio único. Para registros nuevos se forma como `GR` + `consecutivo_gr`, sin ceros a la izquierda. |

## Reglas de compatibilidad histórica

- La migración conserva literalmente `codigo_riesgo` de cada registro histórico.
- Se consideran códigos GR válidos aquellos con formato exacto `GR<número>`.
- La secuencia se inicializa y se sincroniza con el mayor número encontrado en
  todos los códigos GR válidos, sean históricos o nuevos.
- Un código histórico que no cumpla el formato GR no se renumera ni se modifica.
- Antes de asignar un código nuevo se valida toda la columna `codigo_riesgo`.
  Si hay una colisión, se toma el siguiente consecutivo disponible.
- PostgreSQL mantiene la unicidad de `codigo_riesgo` como garantía final y la
  secuencia, junto con un bloqueo transaccional, evita duplicados entre
  solicitudes simultáneas del backend.

## No incluido en esta decisión

- No se modifica `riesgo_id`.
- No se crea un segundo campo visible llamado `codigo_gr`; el nombre oficial
  del código visible es `codigo_riesgo`.
- No se renumeran datos históricos.
