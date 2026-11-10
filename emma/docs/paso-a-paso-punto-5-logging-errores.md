# Paso a paso - Punto 5: Logging y manejo centralizado de errores

Este documento explica lo implementado para que los errores no lleguen al usuario como pantallas tecnicas y queden registrados para analisis.

## 1. Objetivo del punto 5

Garantizar que:

- La API mantenga el formato estandar de error del contrato.
- Los errores esperados respondan con su codigo funcional.
- Los errores inesperados se registren con detalle tecnico en logs.
- El usuario reciba mensajes amigables.
- Los errores por llaves foraneas protegidas respondan `409`, no `500`.
- Las pantallas del frontend tengan 404 y 500 personalizadas.
- Los logs incluyan un identificador por peticion.

## 2. Logging backend

Se configuro `LOGGING` en:

```text
emma/settings.py
```

La configuracion incluye:

- Nivel configurable por `LOG_LEVEL`.
- `DEBUG` configurable por variable de entorno.
- Formato con fecha, nivel, request id, modulo y mensaje.
- Salida a consola, compatible con Azure.
- Salida a archivo:

```text
logs/emma.log
```

El formato usado es:

```text
fecha nivel [request_id] modulo: mensaje
```

No se registran cuerpos de peticiones, contrasenas, tokens ni headers de autorizacion.

El logger `django.db.backends` queda en `WARNING` para evitar registrar SQL y parametros de consultas que puedan contener datos sensibles.

## 3. Request id por peticion

Se creo:

```text
backend/apps/compartido/middleware.py
backend/apps/compartido/logging_context.py
```

`RequestIdMiddleware`:

- Lee `X-Request-ID` si viene desde el cliente.
- Genera uno nuevo si no existe.
- Lo deja disponible en `request.request_id`.
- Lo agrega a la respuesta como `X-Request-ID`.
- Lo inyecta en cada linea de log mediante `RequestIdFilter`.

## 4. Manejador global de errores DRF

El manejador global sigue registrado en:

```text
REST_FRAMEWORK["EXCEPTION_HANDLER"]
```

Archivo:

```text
backend/apps/compartido/api/exceptions.py
```

Formato publico:

```json
{
  "error": {
    "codigo": "ERROR_INTERNO",
    "mensaje": "Ocurrio un error inesperado.",
    "detalles": {}
  }
}
```

Comportamiento:

- `400 VALIDACION`: errores de serializer y parseo.
- `401 NO_AUTENTICADO`: falta de sesion o token.
- `403 SIN_PERMISO`: permisos.
- `404 NO_ENCONTRADO`: recurso inexistente.
- `409 REGLA_NEGOCIO`: reglas de negocio y registros protegidos por llaves foraneas.
- `500 ERROR_INTERNO`: errores inesperados.

Los errores inesperados se registran con `logger.exception`, por lo que el log conserva el traceback completo. La respuesta al usuario no expone el detalle tecnico.

## 5. Reglas de negocio desde services

La excepcion propia queda definida en:

```text
backend/apps/compartido/api/exceptions.py
```

Nombre:

```text
ReglaNegocioError
```

Se usa desde services. Ejemplo implementado:

```text
backend/apps/riesgos/services/riesgo_service.py
```

Cuando se intenta inactivar un riesgo sin justificacion, el servicio lanza `ReglaNegocioError` y la API responde `409 REGLA_NEGOCIO`.

## 6. Llaves foraneas protegidas

`ProtectedError` de Django se convierte a:

```text
HTTP 409
REGLA_NEGOCIO
```

Mensaje para usuario:

```text
El registro no se puede eliminar porque tiene informacion relacionada.
```

Esto evita que un intento de borrado protegido llegue como `500`.

## 7. Frontend

El cliente centralizado sigue siendo:

```text
frontend/core/api_client.py
```

El cliente captura:

- Errores devueltos por la API.
- Errores de conexion.
- Timeouts.
- Respuestas no JSON.

Todos se normalizan al contrato para que las pantallas muestren alertas consistentes.

Las alertas se muestran con:

```text
frontend/templates/components/alerts.html
```

## 8. Paginas 404 y 500

Se agregaron vistas:

```text
frontend/core/views.py
```

Se registraron handlers:

```text
frontend/config/urls.py
```

Templates:

```text
frontend/templates/errors/404.html
frontend/templates/errors/500.html
```

Estas paginas evitan mostrar la pantalla tecnica de Django al usuario.

## 9. Validacion con DEBUG=False

Se agregaron pruebas en:

```text
frontend/core/tests.py
```

Validan que con `DEBUG=False`:

- Una ruta inexistente renderiza la pagina 404 personalizada.
- La pagina 500 personalizada no expone `Traceback`.

Tambien se agregaron pruebas en:

```text
backend/apps/compartido/tests.py
backend/apps/riesgos/tests.py
```

Validan:

- Errores inesperados como `500 ERROR_INTERNO` sin detalle tecnico.
- `ProtectedError` como `409 REGLA_NEGOCIO`.
- Regla de negocio desde service como `409`.
