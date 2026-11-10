# Documentacion del proyecto EMMA

## 2026-09-08

### Contexto

El proyecto inicio con una sola app Django llamada `backend`, donde el archivo `backend/models.py` concentraba los modelos del sistema. Ese archivo contenia los dominios funcionales separados por comentarios, pero vivia como una estructura monolitica.

La decision acordada es migrar hacia una organizacion por dominios, usando varias apps Django independientes para reducir conflictos de merge, mejorar mantenibilidad y reflejar mejor los limites funcionales del sistema.

### Apps de dominio creadas

Se creo el contenedor:

```text
backend/apps/
```

Dentro de ese contenedor se ubicaron las apps Django por dominio:

```text
backend/apps/usuarios/
backend/apps/catalogos/
backend/apps/procesos/
backend/apps/riesgos/
backend/apps/eventos/
backend/apps/planes/
backend/apps/compartido/
```

Cada app tiene la estructura base generada por Django:

```text
admin.py
apps.py
models.py
tests.py
views.py
migrations/
```

Tambien se ajusto el atributo `name` de cada `apps.py` para apuntar a su ruta real, por ejemplo:

```python
name = "backend.apps.usuarios"
```

### Acciones que aun no se han hecho

Todavia no se han generado migraciones nuevas.
Todavia no se ha aplicado ningun cambio sobre la base de datos.

### Modelos movidos por dominio

Se movieron los modelos desde `backend/models.py` hacia su app correspondiente:

```text
backend/apps/usuarios/models.py      -> Usuario
backend/apps/catalogos/models.py     -> Catalogo, CatalogoValor
backend/apps/procesos/models.py      -> CatProceso
backend/apps/riesgos/models.py       -> Riesgo, Causa, Control, RiesgoProceso
backend/apps/eventos/models.py       -> EventoRiesgo, EventoCausa, EventoControl, EventoCuentaContable, EventoDistribucionLinea
backend/apps/planes/models.py        -> PlanAccion
backend/apps/compartido/models.py    -> EntidadCaracteristica, Adjunto, Auditoria
```

`backend/models.py` quedo sin modelos y ahora solo conserva una nota indicando que los modelos fueron separados por dominio.

Las relaciones entre apps se actualizaron usando referencias por texto con el `app_label` de Django, por ejemplo:

```python
models.ForeignKey("riesgos.Riesgo", on_delete=models.PROTECT)
```

Aunque la ruta Python de la app sea `backend.apps.riesgos`, el `app_label` por defecto sigue siendo `riesgos`. Por eso las relaciones deben quedar como `"riesgos.Riesgo"`, `"eventos.EventoRiesgo"`, `"usuarios.Usuario"`, etc.

### Registro en INSTALLED_APPS

Se registraron las apps nuevas en `emma/settings.py`, dentro de `INSTALLED_APPS`, respetando el orden logico de dependencias:

```python
"backend.apps.usuarios",
"backend.apps.catalogos",
"backend.apps.procesos",
"backend.apps.riesgos",
"backend.apps.eventos",
"backend.apps.planes",
"backend.apps.compartido",
```

### Validacion realizada

Se ejecuto una validacion de carga de Django con las apps nuevas registradas en `settings.py`.

Resultado:

```text
System check identified no issues (0 silenced).
```

### Siguiente paso propuesto

El siguiente paso es revisar el estado de las migraciones existentes y decidir si se elimina la migracion inicial antigua de `backend` antes de generar las nuevas migraciones por app.

### Revision de migracion antigua

Se reviso `backend/migrations/0001_initial.py`.

Hallazgos:

- La migracion fue generada el `2026-08-27`.
- Es una migracion inicial de la app `backend`.
- Crea los modelos del esquema monolitico anterior dentro de una sola app.
- Las relaciones internas apuntan a modelos con label `backend`, por ejemplo `backend.usuario`, `backend.riesgo`, `backend.catalogovalor`, etc.
- Esa estructura ya no corresponde al diseño actual, porque los modelos fueron movidos a apps separadas por dominio.

Decision tecnica:

- La migracion antigua `backend/migrations/0001_initial.py` fue eliminada antes de generar las nuevas migraciones por app.
- El equipo confirmo que no hay datos reales en las tablas ya creadas en Azure.
- Las tablas ya creadas en Azure pueden eliminarse antes de aplicar las nuevas migraciones.
- Si hay datos reales en Azure, no se deben borrar tablas directamente; en ese caso habria que hacer una migracion controlada de datos.

## 2026-09-28

### Frontend

Se creo la carpeta `frontend` como proyecto Django separado para la capa de presentacion del sistema.

Tecnologias acordadas:

```text
Django
HTMX
Tabler
Reflex
```

Estructura inicial:

```text
frontend/
frontend/manage.py
frontend/config/
frontend/core/
frontend/catalogos/
frontend/riesgos/
frontend/eventos/
frontend/planes/
frontend/templates/
frontend/static/
```

`frontend/config/settings.py` no define base de datos. `frontend/core/api_client.py` queda como unico punto de comunicacion con la API del backend, y `frontend/core/errors.py` centraliza la traduccion de errores hacia mensajes de interfaz y formularios.

## 2026-09-29

### Primer flujo End-to-End

Se implemento el punto 4 del Sprint 2: primer flujo de validacion punta a punta.

Flujo validado:

```text
Navegador -> Frontend Django -> API backend -> PostgreSQL
```

La pantalla de riesgos permite consultar datos reales, buscar y filtrar con HTMX sin recargar toda la pagina, crear un riesgo mediante `POST /api/v1/riesgos/`, reflejarlo en la tabla y mostrar errores de validacion de la API debajo del campo correspondiente.

Documentacion tecnica:

```text
docs/paso-a-paso-punto-4-flujo-end-to-end.md
```

### Logging y manejo centralizado de errores

Se implemento el punto 5 del Sprint 2: logging y manejo centralizado de errores.

Incluye:

```text
Backend:
- LOGGING en emma/settings.py con salida a consola y archivo logs/emma.log.
- Request id por peticion usando X-Request-ID.
- Manejador global DRF que conserva el contrato de errores.
- Registro tecnico de errores inesperados sin exponer detalles al usuario.
- ProtectedError como 409 REGLA_NEGOCIO.
- ReglaNegocioError usada desde services/.

Frontend:
- api_client normaliza errores de API, conexion, timeout y JSON invalido.
- Alertas consistentes en componentes compartidos.
- Paginas personalizadas 404 y 500.
- Pruebas con DEBUG=False para verificar que no se exponen detalles tecnicos.
```

Documentacion tecnica:

```text
docs/paso-a-paso-punto-5-logging-errores.md
```

## 2026-10-07

### Sprint 3 - Login

Se reviso la guia de login ubicada en:

```text
documentacion-m/emma_login.pdf
```

Se analizo como adaptar el paso a paso al estado actual del proyecto, teniendo en cuenta que el frontend ya existe como proyecto Django separado y que ya cuenta con Tabler, HTMX, `base.html` y el cliente centralizado `frontend/core/api_client.py`.

Decision tecnica principal:

- El login interactivo se implementara en el frontend con Microsoft Entra ID y MSAL.
- El token quedara guardado en la sesion del servidor del frontend, no en el navegador.
- El frontend enviara el token al backend en cada peticion mediante `Authorization: Bearer <token>`.
- El backend validara el token en cada peticion y lo asociara con la tabla `usuario` usando el identificador `oid` de Entra ID.

Documentacion tecnica:

```text
docs/sprint-3-login.md
```

Implementacion inicial realizada:

- App `frontend/autenticacion/` para login con Microsoft Entra ID.
- Rutas `/auth/login/`, `/auth/callback/`, `/auth/logout/` e `/inicio/`.
- Login visual con Tabler.
- Proteccion de pantallas internas mediante sesion.
- Envio del token al backend desde `frontend/core/api_client.py`.
- Redirect URI usada en este entorno: `http://localhost:8000/auth/callback`.
- Para evitar choque local de puertos, el frontend queda en `8000` y `API_BASE_URL` apunta al backend en `8001`.
- Login redisenado con los logos de EMMA y Banco Popular y paleta visual alineada al banco.
- Vista `/inicio/` ajustada para mostrar los modulos despues del login con mayor escala visual, tipografia mas grande y layout de escritorio ampliado.
- Middleware local agregado para redirigir `127.0.0.1:8000` a `localhost:8000` y evitar perdida de sesion durante el callback de Microsoft.
