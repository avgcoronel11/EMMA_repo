# Contrato API EMMA

Este documento define el acuerdo de comunicacion entre el frontend y el backend de EMMA. El frontend debe consumir la API siguiendo estas reglas y el backend debe mantener respuestas consistentes para todos los recursos.

## 1. Convencion de URLs

Las URLs se definen por recurso de negocio, no por tabla fisica. La version vigente de la API es `/api/v1/`.

```text
GET    /api/v1/<dominio>/<recurso>/             listar, paginado
POST   /api/v1/<dominio>/<recurso>/             crear
GET    /api/v1/<dominio>/<recurso>/{id}/        detalle
PATCH  /api/v1/<dominio>/<recurso>/{id}/        editar parcial
DELETE /api/v1/<dominio>/<recurso>/{id}/        eliminar
POST   /api/v1/<dominio>/<recurso>/{id}/<accion>/ accion de negocio
```

Cuando el recurso ya esta en la raiz de `/api/v1/`, el dominio puede omitirse para mantener compatibilidad con los endpoints actuales. Ejemplo: `/api/v1/riesgos/`.

## 2. Mapa preliminar de endpoints

No todas las tablas requieren una URL propia. Las entidades principales tienen endpoint propio; las tablas intermedias y detalles viajan dentro de la entidad principal.

| Recurso | Endpoint esperado | Estado |
| --- | --- | --- |
| Usuarios | `/api/v1/usuarios/` | Endpoint base |
| Catalogos | `/api/v1/catalogos/` | Endpoint base |
| Valores de catalogo | `/api/v1/catalogos/{codigo}/valores/` | Endpoint base |
| Procesos | `/api/v1/procesos/` | Endpoint base |
| Riesgos genericos | `/api/v1/riesgos-genericos/` | Endpoint base |
| Riesgos | `/api/v1/riesgos/` | Endpoint base |
| Eventos | `/api/v1/eventos/` | Endpoint base |
| Planes | `/api/v1/planes/` | Endpoint base |
| Adjuntos | `/api/v1/adjuntos/` | Endpoint base de metadata |
| Auditoria | `/api/v1/auditoria/` | Endpoint base, solo lectura |

Las relaciones de detalle como `RiesgoProceso`, causas, controles, cuentas contables, distribucion por linea y caracteristicas se transportan dentro de su entidad principal cuando hagan parte del flujo funcional.

## 3. Respuestas exitosas

Los detalles devuelven el objeto directamente, con su identificador.

```json
{
  "riesgo_id": 1,
  "codigo_riesgo": "R-001",
  "nombre_riesgo": "Riesgo operativo"
}
```

Los listados siempre son paginados:

```json
{
  "count": 134,
  "next": "/api/v1/riesgos/?page=3",
  "previous": "/api/v1/riesgos/?page=1",
  "results": [
    { "riesgo_id": 1 },
    { "riesgo_id": 2 }
  ]
}
```

Los filtros viajan como parametros de consulta. Se aceptan filtros exactos del recurso, busqueda con `search` y ordenamiento con `ordering`.

```text
?estado=Activo
?search=fraude
?ordering=nombre_riesgo
?ordering=-fecha_ultima_edicion
```

## 4. Formato unico de error

Todos los errores deben responder con la misma estructura:

```json
{
  "error": {
    "codigo": "VALIDACION",
    "mensaje": "Hay errores en los datos enviados.",
    "detalles": {
      "nombre_riesgo": ["Este campo es obligatorio."]
    }
  }
}
```

| HTTP | Codigo | Cuando |
| --- | --- | --- |
| 400 | `VALIDACION` | Datos invalidos. |
| 401 | `NO_AUTENTICADO` | Sin sesion o token. |
| 403 | `SIN_PERMISO` | El rol no puede realizar la accion. |
| 404 | `NO_ENCONTRADO` | El registro no existe. |
| 409 | `REGLA_NEGOCIO` | La operacion viola una regla de negocio. |
| 500 | `ERROR_INTERNO` | Error inesperado. |

## 5. Tipos de datos

Las fechas se envian en formato ISO 8601.

Los montos se envian como texto decimal para no perder precision:

```json
{
  "monto": "1500.00"
}
```

Los valores vacios se representan como `null` cuando el campo no tenga dato. Los nombres de campos usan `snake_case`. Los identificadores deben mantener un criterio estable por recurso, por ejemplo `riesgo_id`, `proceso_id` y `valor_id`.

## 6. Autenticacion

El encabezado definido para autenticacion es:

```http
Authorization: Bearer <token>
```

El contrato queda definido desde este sprint. La integracion real con Entra ID se implementara en el Sprint 3.

## 7. Reflejo en repositorios

Backend:

- Configuracion global de DRF en `emma/settings.py`.
- Paginacion, filtros y manejador de errores comunes en `backend/apps/compartido/api/`.
- Swagger disponible en `/api/docs/` usando `drf-spectacular`.
- Endpoint de ejemplo compatible: `/api/v1/catalogos/{codigo}/valores/`.

Frontend:

- `frontend/core/api_client.py` es el unico punto de comunicacion con la API.
- El cliente adjunta `Authorization: Bearer <token>` cuando hay token configurado.
- Los errores se normalizan al formato del contrato para que todas las pantallas los manejen igual.

## 8. Riesgos: consulta y código GR

### Listado

```http
GET /api/v1/riesgos/
```

El listado incluye riesgos activos e inactivos si no se envía `estado`.
La respuesta utiliza la paginación estándar (`page`, `page_size`, máximo 100).

| Parámetro | Regla |
| --- | --- |
| `estado` | Coincidencia sin distinguir mayúsculas/minúsculas. Ej.: `Activo` o `Inactivo`. |
| `codigo_riesgo` | Coincidencia exacta sin distinguir mayúsculas/minúsculas. |
| `riesgo_homologado` | Coincidencia exacta sin distinguir mayúsculas/minúsculas. |
| `vicepresidencia` | Coincidencia exacta sobre `CAT_PROCESO.vicepresidencia`. |
| `proceso` | Coincidencia exacta sobre `CAT_PROCESO.proceso_nivel0`. |
| `subproceso` | Coincidencia exacta sobre `CAT_PROCESO.proceso_nivel1`. |
| `dueno_proceso` | Coincidencia exacta sobre `RIESGO.dueno_proceso`. |
| `search` | Búsqueda de palabras clave en `nombre_riesgo`, `codigo_referencia_saro`, `ciclo`, `subfactor_riesgo`, `descripcion_proceso`, `linea`, `macroproceso` y `dueno_proceso`. |

La correspondencia aprobada para los filtros es `proceso` →
`proceso_nivel0` y `subproceso` → `proceso_nivel1`. Los selectores de
Vicepresidencia, Proceso, Subproceso y los niveles 0, 1 y 2 siguen siendo
componentes independientes de interfaz; esta API no los unifica ni modifica
el catálogo.

### Detalle

```http
GET /api/v1/riesgos/{riesgo_id}/
```

El detalle incluye la información general aprobada del riesgo, estado,
procesos asociados, riesgo homologado y riesgo genérico, valoración inherente
y residual almacenada, causas, controles —incluido el control genérico— y
características. Eventos, planes de acción e historial no hacen parte aún de
este contrato de detalle.

Las entradas que permiten reconstruir una valoración inherente (`exposicion`,
`complejidad`, `condiciones_entorno`, `grado_ocurrencia`, `eventos_riesgo` y
`poblacion_expuesta`) se incluyen en el detalle.

### Evaluación de control

```http
PATCH /api/v1/riesgos/{riesgo_id}/controles/{control_id}/evaluacion/
```

Registra una o varias respuestas `d1` a `d4` (`Sí`/`No`) y `o1` a `o5`
(`Sí`/`No`; `o5` también admite `NA`). Al completarse las nueve, el backend
recalcula diseño, operatividad, falla VPR y efectividad. Si faltan respuestas,
las calificaciones históricas no se modifican.

### Recálculo residual

```http
POST /api/v1/riesgos/{riesgo_id}/recalcular-residual/
```

El cálculo usa exclusivamente controles activos. Preventivos modifican la
probabilidad; correctivos modifican el impacto y detectivos se usan solo si no
hay reducción correctiva. Los niveles se mantienen entre 1 y 5 y el resultado
persistido incluye probabilidad, impacto y severidad residual.

### Creación y código GR

`codigo_riesgo` no se recibe en la creación. PostgreSQL genera un consecutivo
seguro y el backend almacena el valor visible como `GR<número>`. Antes de
asignarlo se sincroniza con el mayor código existente que tenga formato
`GR<número>`, incluyendo registros históricos. Los históricos conservan su
código original; aquellos que no sigan el formato GR mantienen
`consecutivo_gr` nulo.

Enviar `codigo_riesgo` en un `POST /api/v1/riesgos/` devuelve `400 VALIDACION`.

### Pendientes explícitos

- Alcance de lectura por perfiles y procesos asignados.
- Contrato de eventos, planes de acción e historial dentro del detalle.
- Correspondencia definitiva entre los cinco selectores de proceso y el
  catálogo vigente.
- Reconciliación del motor de valoración con las reglas confirmadas de Tarea 3.
