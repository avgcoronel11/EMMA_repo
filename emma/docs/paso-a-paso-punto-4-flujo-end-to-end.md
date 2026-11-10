# Paso a paso - Punto 4: Primer flujo End-to-End

Este documento explica el flujo construido para validar la arquitectura de punta a punta:

```text
Navegador -> Frontend Django -> API backend -> PostgreSQL
```

El navegador no se comunica directamente con el backend. La pantalla del frontend recibe la interaccion del usuario y llama la API desde el servidor mediante `frontend/core/api_client.py`.

## 1. Objetivo del punto 4

Probar que la arquitectura funciona de punta a punta usando endpoints existentes.

El flujo elegido es gestion de riesgos porque ya existen:

- `GET /api/v1/riesgos/`
- `POST /api/v1/riesgos/`
- Serializer de creacion de riesgo.
- Servicio de dominio `RiesgoService.crear_riesgo`.
- Persistencia en la tabla PostgreSQL `riesgo`.

## 2. Pantalla implementada

La pantalla principal es:

```text
GET /riesgos/
```

Archivos principales:

```text
frontend/riesgos/forms.py
frontend/riesgos/views.py
frontend/riesgos/urls.py
frontend/riesgos/templates/riesgos/list.html
frontend/riesgos/templates/riesgos/partials/_workspace.html
frontend/riesgos/templates/riesgos/partials/_create_form.html
frontend/riesgos/templates/riesgos/partials/_filters.html
frontend/riesgos/templates/riesgos/partials/_table.html
```

La pantalla permite:

- Consultar riesgos reales desde la API.
- Buscar por `search`.
- Filtrar por `estado`.
- Crear un riesgo desde formulario.
- Refrescar el listado sin recargar toda la pagina usando HTMX.
- Mostrar errores de validacion debajo del campo correspondiente.
- Mostrar un mensaje amigable cuando el backend no responde.

## 3. Flujo de consulta

El usuario abre:

```text
/riesgos/
```

La vista `frontend/riesgos/views.py` llama:

```python
get_json("riesgos", params=params)
```

El cliente construye la URL:

```text
http://127.0.0.1:8000/api/v1/riesgos/
```

El backend resuelve el endpoint en:

```text
backend/apps/riesgos/api/views/riesgo.py
```

La respuesta esperada mantiene el contrato paginado:

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": []
}
```

El frontend toma `results` y renderiza la tabla.

## 4. Flujo de busqueda y filtro sin recargar

El formulario de filtros usa HTMX:

```text
GET /riesgos/tabla/
```

Ese endpoint devuelve solo el partial:

```text
frontend/riesgos/templates/riesgos/partials/_table.html
```

La API recibe parametros compatibles con el contrato:

```text
?search=fraude
?estado=Activo
```

## 5. Flujo de creacion

El formulario de creacion envia:

```text
POST /riesgos/crear/
```

La vista frontend valida el formulario Django y luego llama:

```python
post_json("riesgos", form.to_api_payload())
```

El backend recibe:

```text
POST /api/v1/riesgos/
```

La vista backend usa:

```text
RiesgoCreateSerializer
RiesgoService.crear_riesgo
```

Si la creacion es correcta, la fila queda guardada en PostgreSQL y el frontend vuelve a consultar el listado para mostrar el riesgo recien creado.

## 6. Manejo de errores

Cuando la API devuelve errores del contrato:

```json
{
  "error": {
    "codigo": "VALIDACION",
    "mensaje": "Hay errores en los datos enviados.",
    "detalles": {
      "codigo_riesgo": ["Ya existe un riesgo con este codigo."]
    }
  }
}
```

El frontend usa:

```text
frontend/core/errors.py
```

para mapear `detalles.codigo_riesgo` al campo `codigo_riesgo` del formulario.

Cuando la API no responde, `frontend/core/api_client.py` normaliza el fallo y la pantalla muestra:

```text
No fue posible comunicarse con la API.
```

## 7. Validacion para demo

Pasos sugeridos:

1. Levantar el backend en `http://127.0.0.1:8000`.
2. Levantar el frontend.
3. Abrir `/riesgos/`.
4. Crear un riesgo con un codigo nuevo, por ejemplo `R-DEMO-001`.
5. Confirmar que aparece en la tabla.
6. Consultar PostgreSQL:

```sql
SELECT riesgo_id, codigo_riesgo, nombre_riesgo, estado
FROM riesgo
WHERE codigo_riesgo = 'R-DEMO-001';
```

Si se intenta crear el mismo codigo dos veces, la API debe responder validacion y el mensaje debe mostrarse debajo del campo `Codigo`.

Validacion ejecutada:

```text
Codigo creado desde la pantalla: R-E2E-20260929-1506
```

Consulta confirmada contra PostgreSQL:

```text
{'riesgo_id': 1, 'codigo_riesgo': 'R-E2E-20260929-1506', 'nombre_riesgo': 'Riesgo demo end-to-end desde frontend', 'estado': 'Activo'}
```

Validacion de duplicado confirmada en pantalla:

```text
Ya existe un riesgo con este codigo.
```

## 8. Verificaciones automatizadas

Se agregaron pruebas en:

```text
frontend/riesgos/tests.py
```

Estas pruebas validan:

- La pantalla envia `search` a la API.
- El formulario de creacion llama `POST /api/v1/riesgos/`.
- Los errores de validacion de la API se muestran en el campo correcto.
