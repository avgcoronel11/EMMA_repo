# Paso a paso - Punto 3: Contrato API

Este documento explica que se esta haciendo para construir el punto 3 del Sprint 2: contrato de API, endpoints y comunicacion entre backend y frontend.

El contrato formal queda documentado en `docs/contrato-api.md`. Este archivo es una bitacora tecnica del trabajo realizado y de lo que falta por crear.

## 1. Objetivo del punto 3

El objetivo es que frontend y backend tengan una forma unica y predecible de comunicarse.

Esto incluye:

- Convencion de URLs para los recursos.
- Respuestas exitosas con una estructura uniforme.
- Listados paginados con `count`, `next`, `previous` y `results`.
- Errores con un formato unico.
- Soporte para filtros, busqueda y ordenamiento.
- Swagger en `/api/docs/`.
- Cliente frontend centralizado en `frontend/core/api_client.py`.

## 2. Paso a paso realizado

### Paso 1: Crear el documento del contrato

Se creo `docs/contrato-api.md`.

Ese documento define:

- Convencion de rutas.
- Mapa preliminar de endpoints.
- Formato de respuestas exitosas.
- Formato unico de errores.
- Tipos de datos.
- Autenticacion con `Authorization: Bearer <token>`.
- Responsabilidades del backend y frontend.

### Paso 2: Agregar dependencias necesarias

Se agregaron dependencias en `requirements.txt`:

```text
django-filter==25.1
drf-spectacular==0.28.0
```

`django-filter` queda disponible para filtros en DRF.

`drf-spectacular` se usa para generar Swagger/OpenAPI.

### Paso 3: Configurar DRF globalmente

Se actualizo `emma/settings.py` para agregar:

- `django_filters`
- `drf_spectacular`
- paginacion global
- filtros globales
- manejador global de errores
- configuracion de documentacion OpenAPI

La configuracion global de DRF queda en `REST_FRAMEWORK`.

### Paso 4: Publicar Swagger

Se actualizo `emma/urls.py` para publicar:

```text
GET /api/schema/
GET /api/docs/
```

`/api/schema/` entrega el esquema OpenAPI.

`/api/docs/` muestra Swagger UI.

### Paso 5: Crear piezas comunes de API

Se crearon piezas compartidas en `backend/apps/compartido/api/`.

Archivos creados:

```text
backend/apps/compartido/api/exceptions.py
backend/apps/compartido/api/filters.py
backend/apps/compartido/api/pagination.py
```

`exceptions.py` convierte errores de DRF al formato del contrato:

```json
{
  "error": {
    "codigo": "VALIDACION",
    "mensaje": "Hay errores en los datos enviados.",
    "detalles": {}
  }
}
```

`pagination.py` define la respuesta paginada:

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": []
}
```

`filters.py` contiene helpers simples para aplicar `search` y `ordering`.

### Paso 6: Ajustar endpoints existentes

Se ajustaron endpoints actuales para que los listados ya no devuelvan una lista plana.

Antes:

```json
[
  { "riesgo_id": 1 }
]
```

Ahora:

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    { "riesgo_id": 1 }
  ]
}
```

Los endpoints ajustados fueron:

- valores de catalogo
- riesgos genericos
- procesos
- riesgos

### Paso 7: Ajustar el cliente frontend

Se actualizo `frontend/core/api_client.py`.

Ahora:

- Sigue siendo el punto unico de comunicacion con la API.
- Adjunta `Authorization: Bearer <token>` si existe `API_BEARER_TOKEN`.
- Convierte errores antiguos, de red o del backend al formato unico del contrato.

Tambien se actualizo `frontend/core/errors.py` para leer:

```text
error.codigo
error.mensaje
error.detalles
```

### Paso 8: Actualizar pruebas existentes

Se actualizaron pruebas en `backend/apps/riesgos/tests.py`.

Las pruebas de listado ahora validan `response.data["results"]` y `response.data["count"]`.

Tambien se agrego validacion del formato de error para datos invalidos.

### Paso 9: Verificaciones realizadas

Se ejecuto:

```text
venv/bin/python manage.py check
```

Resultado: correcto.

Se ejecuto:

```text
venv/bin/python -m compileall backend emma frontend/core frontend/config
```

Resultado: correcto.

Se ejecuto:

```text
venv/bin/python manage.py spectacular --file /tmp/emma-schema.yml --validate
```

Resultado: correcto, sin errores. Quedaron advertencias menores de Swagger sobre campos calculados en serializers.

La suite de pruebas:

```text
venv/bin/python manage.py test backend.apps.riesgos
```

No pudo completarse porque intenta conectar con el PostgreSQL remoto de Azure definido en `.env`, y el entorno local/sandbox no pudo resolver el host.

## 3. Endpoints creados o disponibles actualmente

### Documentacion

| Metodo | Endpoint | Estado | Comentario |
| --- | --- | --- | --- |
| GET | `/api/schema/` | Creado | Esquema OpenAPI. |
| GET | `/api/docs/` | Creado | Swagger UI. |

### Catalogos

| Metodo | Endpoint | Estado | Comentario |
| --- | --- | --- | --- |
| GET | `/api/v1/catalogos/` | Creado | Lista catalogos disponibles, paginado. |
| GET | `/api/v1/catalogos/{codigo}/` | Creado | Detalle de un catalogo por codigo. |
| GET | `/api/v1/catalogos/{codigo}/valores/` | Existente y ajustado | Lista valores de un catalogo, ahora paginado. |

### Usuarios

| Metodo | Endpoint | Estado | Comentario |
| --- | --- | --- | --- |
| GET | `/api/v1/usuarios/` | Creado | Lista usuarios locales, paginado. |
| GET | `/api/v1/usuarios/{usuario_id}/` | Creado | Detalle de usuario local. |

### Riesgos genericos

| Metodo | Endpoint | Estado | Comentario |
| --- | --- | --- | --- |
| GET | `/api/v1/riesgos-genericos/` | Existente y ajustado | Lista riesgos genericos activos, ahora paginado. |

### Procesos

| Metodo | Endpoint | Estado | Comentario |
| --- | --- | --- | --- |
| GET | `/api/v1/procesos/` | Existente y ajustado | Lista procesos activos, con filtros, busqueda y ordenamiento. |

### Riesgos

| Metodo | Endpoint | Estado | Comentario |
| --- | --- | --- | --- |
| GET | `/api/v1/riesgos/` | Existente y ajustado | Lista riesgos, ahora paginado. |
| POST | `/api/v1/riesgos/` | Existente | Crea un riesgo. |
| GET | `/api/v1/riesgos/{riesgo_id}/` | Existente | Detalle de riesgo. |
| POST | `/api/v1/riesgos/{riesgo_id}/inactivar/` | Existente | Accion de negocio para inactivar riesgo. |
| POST | `/api/v1/riesgos/calcular-valoracion/` | Existente | Calcula valoracion sin guardar. |

### Eventos

| Metodo | Endpoint | Estado | Comentario |
| --- | --- | --- | --- |
| GET | `/api/v1/eventos/` | Creado | Lista eventos paginados, con filtros y busqueda. |
| POST | `/api/v1/eventos/` | Creado | Crea evento con detalles anidados opcionales. |
| GET | `/api/v1/eventos/{evento_id}/` | Creado | Detalle de evento con causas, controles, cuentas, distribuciones y caracteristicas. |
| PATCH | `/api/v1/eventos/{evento_id}/` | Creado | Edita parcialmente el evento; reemplaza detalles anidados si se envian. |

### Planes

| Metodo | Endpoint | Estado | Comentario |
| --- | --- | --- | --- |
| GET | `/api/v1/planes/` | Creado | Lista planes paginados, con filtros y busqueda. |
| POST | `/api/v1/planes/` | Creado | Crea un plan de accion. |
| GET | `/api/v1/planes/{plan_id}/` | Creado | Detalle de plan. |
| PATCH | `/api/v1/planes/{plan_id}/` | Creado | Edita parcialmente un plan. |

### Adjuntos

| Metodo | Endpoint | Estado | Comentario |
| --- | --- | --- | --- |
| GET | `/api/v1/adjuntos/` | Creado | Lista metadata de adjuntos. |
| POST | `/api/v1/adjuntos/` | Creado | Crea metadata de adjunto. No sube archivo fisico todavia. |
| GET | `/api/v1/adjuntos/{adjunto_id}/` | Creado | Detalle de metadata de adjunto. |
| PATCH | `/api/v1/adjuntos/{adjunto_id}/` | Creado | Edita metadata de adjunto. |
| DELETE | `/api/v1/adjuntos/{adjunto_id}/` | Creado | Elimina metadata de adjunto. |

### Auditoria

| Metodo | Endpoint | Estado | Comentario |
| --- | --- | --- | --- |
| GET | `/api/v1/auditoria/` | Creado | Lista auditoria paginada, solo lectura. |
| GET | `/api/v1/auditoria/{auditoria_id}/` | Creado | Detalle de auditoria, solo lectura. |

### Modulos registrados sin endpoints internos todavia

Estos prefijos ya estan registrados en `backend/api_urls.py`, pero sus archivos `api/urls.py` aun no declaran rutas internas:

| Prefijo | Estado |
| --- | --- |
| `/api/v1/compartido/` | Registrado, sin endpoints internos. |

## 4. Endpoints que faltan por crear

Segun el contrato del Sprint 2, ya estan creados los endpoints base de catalogos, usuarios, eventos, planes, adjuntos y auditoria. Lo pendiente ahora se concentra en capacidades funcionales adicionales.

### Usuarios

Ya existen endpoints de consulta de usuarios locales. La autenticacion real con Entra ID queda para Sprint 3. Por ahora el contrato solo define `Authorization: Bearer <token>`.

Pendiente para Sprint 3:

- Validar el token Bearer contra Entra ID.
- Resolver el usuario local a partir de `entra_object_id`.
- Definir si se crea automaticamente el usuario local cuando llegue un token valido y aun no exista en la tabla `Usuario`.
- Crear, si se requiere, `GET /api/v1/usuarios/me/` para devolver el usuario asociado al token.

### Catalogos

Completar catalogos significa exponer la entidad `Catalogo` como recurso propio, no solo sus valores.

Hoy existe:

```text
GET /api/v1/catalogos/{codigo}/valores/
```

Eso sirve para consultar las opciones de un catalogo especifico, por ejemplo los valores de `PRINCIPIO_COSO`.

Ya se puede consultar la lista de catalogos disponibles y el detalle de un catalogo:

```text
GET /api/v1/catalogos/
GET /api/v1/catalogos/{codigo}/
```

Opcionalmente, si se decide administrar catalogos desde la API, tambien faltarian:

```text
POST  /api/v1/catalogos/
PATCH /api/v1/catalogos/{codigo}/
POST  /api/v1/catalogos/{codigo}/valores/
PATCH /api/v1/catalogos/{codigo}/valores/{valor_id}/
```

### Eventos

Ya existen endpoints base. Pendiente para fases funcionales:

- Definir si se permite `DELETE /api/v1/eventos/{evento_id}/` o si todo cierre/inactivacion sera accion de negocio.
- Crear acciones de negocio si aplican, por ejemplo cerrar, contabilizar o recuperar.
- Registrar auditoria automaticamente al crear o modificar eventos.

### Planes

Ya existen endpoints base. Pendiente para fases funcionales:

- Definir acciones de negocio, por ejemplo cerrar plan o actualizar avance como accion dedicada.
- Registrar auditoria automaticamente al crear o modificar planes.

### Adjuntos

Ya existen endpoints de metadata. Pendiente:

- Definir storage fisico de archivos, probablemente Azure Storage.
- Implementar carga `multipart/form-data`.
- Implementar descarga o URL segura de consulta.
- Decidir si `DELETE` elimina solo metadata o tambien el archivo fisico.

### Auditoria

Ya existen endpoints de consulta, solo lectura. Pendiente:

- Crear servicios o hooks para escribir auditoria automaticamente cuando se creen, editen, inactiven o cierren riesgos, eventos y planes.
- Definir exactamente que datos anteriores/nuevos se guardan por tipo de accion.

### Riesgos

Ya existen los endpoints principales de riesgos. Queda pendiente para fases posteriores evaluar si se necesitan:

```text
PATCH  /api/v1/riesgos/{riesgo_id}/
DELETE /api/v1/riesgos/{riesgo_id}/
```

Actualmente la baja funcional se maneja con:

```text
POST /api/v1/riesgos/{riesgo_id}/inactivar/
```

## 5. Estado general

El punto 3 ya tiene implementada la base transversal:

- contrato documentado
- Swagger
- paginacion
- formato unico de error
- filtros base
- cliente frontend preparado
- endpoints de riesgos, eventos, planes, adjuntos y auditoria alineados al contrato

Lo que falta no es repetir la base tecnica, sino completar recursos especificos: usuarios, catalogos como entidad propia, storage fisico de adjuntos y escritura automatica de auditoria.
