# Estado del motor de Riesgos y permisos

**Fecha de revisión:** 2026-10-21  
**Fuentes funcionales:**

- `Archivos emma/sprint 4/Tarea 3. Reglas_Motores_Riesgo_EMMA_Reglas_Confirmadas.xlsx`.
- `Archivos emma/sprint 4/2.Matriz_Perfiles_Permisos_EMMA.xlsx`.

Este documento es un inventario. No modifica fórmulas ni habilita permisos.

## Alcance de la Tarea 3

La Tarea 3 define el motor de valoración de la Matriz de Riesgos:

1. Probabilidad inherente histórica, cualitativa, por ocurrencia y final.
2. Impacto inherente como el mayor de las siete dimensiones aprobadas.
3. Severidad inherente mediante el cruce de probabilidad e impacto.
4. Efectividad de controles y movimientos de probabilidad/impacto residual.
5. Probabilidad, impacto y severidad residuales.

No es solamente un endpoint de cálculo: define entradas, precedencias, reglas
de reducción y resultados que deben persistirse en `RIESGO`.

## Motor actual: implementado vs. pendiente

| Componente | Implementado actualmente | Pendiente para cumplir Tarea 3 |
| --- | --- | --- |
| Configuración vigente | Existen `CfgProbabilidad`, `CfgNivelImpacto` y `CfgSeveridad`; los servicios filtran por versión y vigencia. | Completar la verificación de probabilidad e impacto; la severidad ya fue contrastada. |
| Probabilidad simple | `calcular_probabilidad()` consulta una regla con un `nivel` recibido. | Calcular exposición, complejidad, entorno, ocurrencia e histórica; obtener el promedio cualitativo y seleccionar el mayor de los tres componentes definidos. |
| Probabilidad histórica | No existe. | Calcular Eventos de Riesgo / Población Expuesta y clasificar con los límites exactos de Tarea 3. |
| Ocurrencia | No existe como entrada ni cálculo. | Incluir la escala de ocurrencia aprobada y compararla con los demás componentes. |
| Impacto inherente | `calcular_impacto_mayor()` toma el máximo de las claves enviadas. | Exigir y validar exactamente Legal, Reputacional, Servicio al cliente, Información, Continuidad, Contagio y Financiero. Actualmente el diccionario admite cualquier subconjunto o nombre de dimensión. |
| Severidad inherente | `calcular_severidad()` consulta `CfgSeveridad` mediante la concatenación de etiquetas. La versión activa `2026.1` tiene las 25 combinaciones de la matriz fuente, sin faltantes, sobrantes ni duplicados, y todas tienen la severidad esperada. | Mantenerla sin cambios; reutilizarla para el motor reconciliado. |
| Efectividad de controles | Los campos de control existen (`tipo_control`, `naturaleza`, `cumple_diseno`, `cumple_oper`, `falla_vpr`, `efectividad`). | No hay servicio que derive diseño, operatividad, falla VPR ni peso numérico desde los controles. |
| Riesgo residual | `calcular_residual()` vuelve a consultar probabilidad e impacto recibidos en la petición. | Derivar residual desde controles asociados: sin controles = inherente; preventivos reducen probabilidad; correctivos prevalecen para impacto; detectivos aplican solo si no hay reducción correctiva; Fuerte/Moderado = 1 y Débil = 0. |
| Persistencia de resultados | Crear un riesgo puede guardar los resultados que devuelva el servicio actual. | Persistir resultados del motor reconciliado sin duplicar fórmulas en serializers o vistas. |

## Verificación de severidad (2026-10-21)

Se comparó, en modo de solo lectura, `CFG_SEVERIDAD` versión activa `2026.1`
contra la tabla `Hoja2!M:N` de `Copia de Matriz Operaciones de Derivados.xlsx`,
que la Tarea 3 identifica como fuente de la matriz.

| Comprobación | Resultado |
| --- | --- |
| Combinaciones esperadas | 25 |
| Combinaciones activas configuradas | 25 |
| Faltantes | Ninguna |
| Sobrantes | Ninguna |
| Duplicados | Ninguno |
| Severidad asignada por cruce | Coincide en las 25 combinaciones |

No corresponde modificar la tabla de severidad.

## Datos que faltan para implementar el motor exactamente

La tabla `RIESGO` sí conserva los siete resultados de impacto, y `CONTROL`
conserva tipo, naturaleza, diseño, operatividad, falla VPR y efectividad. Sin
embargo, no existen campos para: exposición, grado de ocurrencia, cantidad de
eventos, población expuesta, las cuatro respuestas de diseño, ni las cinco
respuestas de operatividad (`o1` a `o5`).

Por tanto, el motor no puede derivar de forma verificable la probabilidad
cualitativa/histórica ni diseño, operatividad y falla VPR desde entradas
primarias. Antes de implementarlo se debe aprobar si esos datos llegarán como
entradas transitorias del cálculo, se persistirán en el modelo, o se obtendrán
de otro módulo/catálogo.

## Permisos: implementado vs. pendiente

| Aspecto | Implementado actualmente | Pendiente |
| --- | --- | --- |
| Login frontend | Existe flujo MSAL/Microsoft Entra en `frontend/autenticacion/`; conserva token en sesión y el cliente frontend lo envía como Bearer. | Validación del token por el backend API. |
| Usuario local | Existe `USUARIO` con `entra_object_id`, nombre, correo y estado. | Asociación de usuario con perfil y alcance de procesos. |
| DRF | DRF está instalado, pero `REST_FRAMEWORK` no define clases de autenticación ni permisos por defecto. | Configurar autenticación real una vez se defina la integración Entra para API. |
| Vistas de Riesgos | Las vistas no usan `permission_classes`; archivos `api/permissions.py` están vacíos. | Autorización por acción y por objeto/proceso. |
| Alcance de lectura | No existe filtrado de riesgos por procesos asignados al usuario. | Aplicar alcance global o por proceso según perfil. |
| Matriz de perfiles | La matriz Excel define el comportamiento objetivo. | Traducir esa matriz a claims, App Roles o grupos de Entra y al modelo de asignación de procesos, cuando Arquitectura confirme la fuente de autoridad. |

## Relación con la matriz de roles

La matriz es la fuente funcional de referencia, pero no está implementada aún
en el backend. Entre otras reglas, define consulta de riesgos para Control
Interno, Consulta Riesgo y Controles, Dueño de Proceso y Auditoría, con
alcances globales o por procesos asignados. No se implementará una simulación
de esas reglas hasta contar con la definición técnica de claims, perfiles y
asignaciones de proceso.

## Próximo paso requerido

Antes de modificar motor o permisos se debe aprobar un diseño específico para:

1. Entradas y fuentes de datos de probabilidad histórica, ocurrencia y las
   siete dimensiones de impacto.
2. Asociación y agregación de controles para el cálculo residual.
3. Tabla completa de severidad y carga/versionado de sus reglas.
4. Claims o App Roles de Entra, perfiles EMMA y relación usuario-proceso.
