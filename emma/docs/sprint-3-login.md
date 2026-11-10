# Sprint 3 - Login

Este documento registra el analisis y la ruta de ejecucion para crear la pantalla de login de EMMA y conectarla con Microsoft Entra ID, tomando como base la guia ubicada en:

```text
documentacion-m/emma_login.pdf
```

## 1. Objetivo

Implementar el login del frontend de EMMA con una pantalla basada en Tabler y autenticacion contra Microsoft Entra ID.

El flujo esperado es:

```text
Navegador -> Frontend Django -> Microsoft Entra ID -> Frontend Django -> Backend API
```

El frontend inicia la sesion, recibe el token desde Entra ID y lo conserva en la sesion del servidor. Luego el frontend envia ese token al backend en cada llamada a la API usando:

```http
Authorization: Bearer <token>
```

El backend no debe hacer el login interactivo. Su responsabilidad es validar el token recibido en cada peticion y resolver el usuario local para auditoria y permisos.

## 2. Contexto revisado

Se revisaron los documentos previos del proyecto:

```text
DOCUMENTACION_PROYECTO.md
docs/contrato-api.md
docs/paso-a-paso-punto-3-contrato-api.md
docs/paso-a-paso-punto-4-flujo-end-to-end.md
docs/paso-a-paso-punto-5-logging-errores.md
```

Tambien se reviso la estructura actual del frontend:

```text
frontend/
frontend/config/settings.py
frontend/config/urls.py
frontend/core/api_client.py
frontend/templates/base.html
frontend/static/vendor/tabler/
frontend/static/css/app.css
frontend/riesgos/
frontend/eventos/
frontend/planes/
frontend/catalogos/
```

Hallazgos principales:

- El frontend ya existe como proyecto Django separado.
- Tabler y HTMX ya estan descargados en `frontend/static/vendor/`.
- `frontend/templates/base.html` ya usa Tabler como layout principal.
- `frontend/core/api_client.py` ya es el punto unico de comunicacion con la API.
- El cliente ya soporta `Authorization: Bearer <token>`, pero hoy lo toma de `API_BEARER_TOKEN`.
- El frontend fue creado sin base de datos de negocio. Para el login con MSAL se requiere una sesion del lado servidor; esa sesion no guarda datos de EMMA, solo datos temporales de autenticacion.

## 3. Lo tomado de la guia `emma_login.pdf`

La guia define estos puntos como base del Sprint 3:

- Crear una pantalla de login con Tabler, basada en la plantilla `sign-in-cover`.
- Quitar usuario y contrasena locales, porque EMMA debe iniciar sesion con Microsoft.
- Usar una app Django llamada `autenticacion/` en el frontend.
- Crear rutas de autenticacion:

```text
/auth/login/
/auth/callback/
/auth/logout/
```

- Registrar en Entra ID la URL de retorno. La guia original proponia el puerto `8001`, pero para este entorno se recibio y valido en Azure:

```text
http://localhost:8000/auth/callback
```

- Configurar variables:

```text
ENTRA_TENANT_ID
ENTRA_CLIENT_ID
ENTRA_CLIENT_SECRET
ENTRA_REDIRECT_URI=http://localhost:8000/auth/callback
ENTRA_SCOPE=User.Read
API_BASE_URL
```

- Guardar el token en la sesion del servidor del frontend.
- Proteger las pantallas internas con un decorador equivalente a `login_requerido`.
- Enviar el token al backend desde `frontend/core/api_client.py`.
- En Sprint 3 tambien debe quedar pendiente o implementada la proteccion del backend con validacion real del token.

## 4. Como se ejecutara en este repositorio

La ejecucion no debe repetir los pasos iniciales de la guia que ya estan hechos. En este repositorio se hara asi:

### Paso 1: Preparar configuracion del frontend

Actualizar `frontend/requirements.txt` para incluir:

```text
msal
python-decouple
```

Actualizar `frontend/.env.example` con las variables de Entra ID, dejando el secreto como placeholder para no versionarlo.

Actualizar `frontend/config/settings.py` para:

- Leer `.env`.
- Registrar `django.contrib.sessions`.
- Registrar la app `autenticacion`.
- Habilitar `SessionMiddleware`.
- Definir configuracion `ENTRA_*`.

Decision tecnica: se usara la sesion de Django del lado servidor con cache local en desarrollo. No se almacenaran datos de negocio de EMMA en el frontend ni se enviara el token al navegador.

### Paso 2: Crear app de autenticacion en el frontend

Crear:

```text
frontend/autenticacion/
frontend/autenticacion/entra.py
frontend/autenticacion/views.py
frontend/autenticacion/urls.py
frontend/autenticacion/decoradores.py
frontend/autenticacion/templates/autenticacion/login.html
frontend/autenticacion/templates/autenticacion/inicio.html
```

Responsabilidades:

- `entra.py`: encapsula MSAL y genera la URL de login.
- `views.py`: maneja login, callback y logout.
- `decoradores.py`: protege vistas internas.
- `login.html`: pantalla publica de inicio de sesion con Tabler.
- `inicio.html`: pantalla de validacion posterior al login.

### Paso 3: Ajustar rutas

Actualizar `frontend/config/urls.py` para:

- Enviar `/` al login o al inicio segun sesion.
- Incluir `auth/`.
- Definir `/inicio/`.

Las pantallas funcionales existentes (`/riesgos/`, `/eventos/`, `/planes/`, `/catalogos/`) deberan quedar protegidas.

### Paso 4: Integrar el token con el cliente API

Modificar `frontend/core/api_client.py` para permitir pasar el token de la sesion a cada llamada.

El patron esperado en vistas sera:

```python
token = request.session.get("access_token")
get_json("riesgos", params=params, token=token)
```

La compatibilidad con `API_BEARER_TOKEN` puede mantenerse como respaldo local, pero el flujo principal del Sprint 3 sera el token de Entra ID.

### Paso 5: Proteger el backend

Crear o completar en backend:

```text
backend/apps/usuarios/autenticacion.py
```

Ese componente debe:

- Leer el header `Authorization`.
- Validar firma con las llaves publicas de Microsoft.
- Validar emisor, audiencia, tenant y vencimiento.
- Buscar o crear el usuario local por `oid` contra la tabla `usuario`.
- Dejar el usuario disponible en `request.user`.

Luego se activara en `emma/settings.py` dentro de `REST_FRAMEWORK`:

```python
DEFAULT_AUTHENTICATION_CLASSES
DEFAULT_PERMISSION_CLASSES
```

La meta es que las llamadas sin token respondan `401 NO_AUTENTICADO`.

### Paso 6: Validaciones

Validaciones manuales:

1. Abrir `http://localhost:8000/inicio/` sin sesion: debe redirigir al login.
2. Hacer clic en "Iniciar sesion con Microsoft": debe abrir `login.microsoftonline.com`.
3. Iniciar sesion: debe volver a `/auth/callback/` y luego a `/inicio/`.
4. Ver nombre, correo y `oid` del usuario autenticado.
5. Abrir `/riesgos/`: debe consultar la API con token.
6. Abrir la API local en el puerto que se asigne al backend, por ejemplo `http://localhost:8001/api/v1/procesos/`, sin token: debe responder `401`.
7. Enviar un token invalido o vencido: debe responder `401`.

Validaciones automaticas:

- Tests de vistas de login usando mocks de MSAL.
- Tests del decorador de sesion.
- Tests de `api_client.py` verificando envio de `Authorization`.
- Tests backend para peticiones sin token, token invalido y token valido simulado.

## 5. Informacion requerida para completar la conexion real

Para conectar contra Entra ID real se necesita:

```text
ENTRA_TENANT_ID=d4227148-4930-4f06-8baa-0845ff57e541
ENTRA_CLIENT_ID=adffe407-2225-4be0-86aa-889564379ea1
ENTRA_CLIENT_SECRET=<secreto-del-cliente>
ENTRA_REDIRECT_URI=http://localhost:8000/auth/callback
ENTRA_SCOPE=User.Read
```

Tambien se debe confirmar en el portal de Azure:

- Que `http://localhost:8000/auth/callback` esta registrado como Redirect URI de tipo Web.
- Que la API de EMMA esta expuesta en Entra ID con un scope propio, por ejemplo `api://<api-client-id>/access_as_user`.
- Que el frontend esta autorizado para solicitar ese scope.
- Si se usaran App roles: `Analista`, `Consultor`, `Administrador`.
- Si `Assignment required` quedara activo para impedir usuarios no asignados.

## 6. Lo hecho en esta revision

En esta revision se realizo:

- Se identifico y analizo `documentacion-m/emma_login.pdf`.
- Se extrajo el flujo funcional del login con Tabler, MSAL y Entra ID.
- Se reviso el estado real del frontend ya creado.
- Se confirmo que Tabler y HTMX ya estan disponibles en el frontend.
- Se confirmo que `core/api_client.py` es el punto correcto para centralizar el envio del token al backend.
- Se documento la ruta de implementacion del Sprint 3.
- Se recibieron los identificadores de tenant y cliente, y se confirmo la Redirect URI validada en Azure. El secreto real no se documento en archivos versionables.

## 7. Implementacion inicial realizada

Se implemento la primera version del login en el frontend:

- App `frontend/autenticacion/`.
- Vista publica de login con Tabler.
- Rutas `/auth/login/`, `/auth/callback`, `/auth/callback/` y `/auth/logout/`.
- Vista protegida `/inicio/`.
- Decorador `login_requerido` para pantallas internas.
- Lectura de variables `ENTRA_*` desde `.env`.
- Sesion de Django configurada con cache local para conservar el token del lado servidor.
- `frontend/core/api_client.py` ahora acepta `token=` y lo envia como `Authorization: Bearer`.
- Pantallas existentes de `riesgos`, `eventos`, `planes` y `catalogos` quedaron protegidas.
- `frontend/.env.example` fue actualizado sin incluir secretos reales.
- Se ajusto la experiencia visual del login con los colores de Banco Popular y los logos de `logos/`.
- Se corrigio la vista autenticada `/inicio/` para mostrar los modulos internos despues del login.
- Se amplio el layout interno de escritorio: barra lateral, contenedor principal, tarjetas, tablas y tipografia.
- Se agrego redireccion local de `127.0.0.1:8000` hacia `localhost:8000` para conservar la sesion del login con la Redirect URI registrada en Azure.
- Como la Redirect URI validada usa el frontend en `http://localhost:8000`, el `API_BASE_URL` local del frontend quedo apuntando a `http://127.0.0.1:8001/api/v1` para evitar choque de puertos con el backend.
- Se ajusto la pantalla de login con logos oficiales de EMMA y Banco Popular, usando una composicion de escritorio y colores alineados con Banco Popular Colombia.
- Se agrego redireccion local de `127.0.0.1:8000` a `localhost:8000` para que la cookie de sesion coincida con la Redirect URI de Entra ID y no se pierda el `auth_flow`.

## 8. Pendientes inmediatos

- Implementar validacion de tokens en el backend.
- Activar proteccion global de API.
- Actualizar pruebas del backend cuando se active la validacion real del token.
- Definir el scope definitivo de la API de EMMA. Con `User.Read` el login valida al usuario contra Microsoft Graph; para proteger la API propia se recomienda exponer un scope tipo `api://<api-client-id>/access_as_user`.
