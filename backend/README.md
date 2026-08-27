# EMMA Backend Django

Este backend es la base inicial de Django para la reconstruccion gradual de EMMA.

La aplicacion actual de EMMA sigue siendo principalmente Streamlit con persistencia en Excel. Esta carpeta no migra esa funcionalidad. Su objetivo es preparar una base ordenada para que, en fases posteriores, se puedan crear modelos Django, migraciones funcionales, servicios, APIs y autenticacion.

## Versiones utilizadas

- Python: 3.14.4
- Django: 5.2.17 LTS
- Psycopg: 3.3.4

Django 5.2 soporta Python 3.14 desde Django 5.2.8. Psycopg 3 soporta Python 3.10 a 3.14 y PostgreSQL 10 a 18.

## Estructura

```text
backend/
├── manage.py
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── apps/
│   ├── usuarios/
│   ├── matriz/
│   ├── eventos/
│   ├── planes/
│   ├── catalogos/
│   └── auditoria/
├── requirements.txt
├── .env.example
├── README.md
└── REGISTRO_CAMBIOS.md
```

## Para que sirve cada carpeta

- `config/`: configuracion principal de Django. Aqui estan `settings.py`, `urls.py`, `asgi.py` y `wsgi.py`.
- `apps/`: carpeta para organizar las aplicaciones Django por dominios funcionales.
- `apps/usuarios/`: futura organizacion de seguridad y usuarios. Todavia no contiene modelos funcionales.
- `apps/matriz/`: futura organizacion de matriz de riesgos. Todavia no contiene modelos funcionales.
- `apps/eventos/`: futura organizacion de eventos de riesgo. Todavia no contiene modelos funcionales.
- `apps/planes/`: futura organizacion de planes de accion. Todavia no contiene modelos funcionales.
- `apps/catalogos/`: futura organizacion de catalogos. Todavia no contiene modelos funcionales.
- `apps/auditoria/`: futura organizacion de auditoria. Todavia no contiene logica funcional.

## Crear el entorno virtual

Desde la raiz del proyecto:

```bash
python3 -m venv backend/.venv
```

Activar el entorno:

```bash
source backend/.venv/bin/activate
```

Comprobar Python:

```bash
python --version
```

Debe mostrar Python 3.14.4 en este entorno.

## Instalar dependencias

Con el entorno virtual activo:

```bash
pip install -r backend/requirements.txt
```

Dependencias directas de esta fase:

- `Django==5.2.17`: framework web base.
- `psycopg[binary]==3.3.4`: driver PostgreSQL moderno para Python.

No se instalo Django REST Framework porque las APIs se trabajaran en una fase posterior.

## Configurar variables de entorno

El archivo `backend/.env.example` es solo una plantilla. No contiene secretos reales.

Django lee variables desde el entorno del sistema. Este proyecto no carga automaticamente archivos `.env`, para evitar agregar dependencias adicionales en esta fase.

Variables esperadas:

```bash
DJANGO_SECRET_KEY=
DJANGO_DEBUG=
DJANGO_ALLOWED_HOSTS=
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=
```

Ejemplo de configuracion manual en una terminal de desarrollo:

```bash
export DJANGO_SECRET_KEY="clave-local-no-productiva"
export DJANGO_DEBUG="True"
export DJANGO_ALLOWED_HOSTS="localhost,127.0.0.1"
export DB_NAME="nombre_de_base"
export DB_USER="usuario_postgresql"
export DB_PASSWORD="password_postgresql"
export DB_HOST="host_postgresql"
export DB_PORT="puerto_postgresql"
```

No guardes credenciales reales en Git. Si creas un archivo `.env`, debe permanecer excluido por `.gitignore`.

## Comprobar configuracion de Django

Desde la raiz del proyecto:

```bash
backend/.venv/bin/python backend/manage.py check
```

Este comando valida la configuracion general de Django y las apps registradas. No comprueba una conexion real a PostgreSQL.

## Comprobar que PostgreSQL esta configurado como motor

```bash
backend/.venv/bin/python backend/manage.py shell -c "from django.conf import settings; print(settings.DATABASES['default']['ENGINE'])"
```

Debe mostrar:

```text
django.db.backends.postgresql
```

## Probar conexion real con PostgreSQL

Primero deben existir y estar configuradas las variables `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` y `DB_PORT`.

Luego ejecutar:

```bash
backend/.venv/bin/python backend/manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('Conexion OK')"
```

Si la conexion falla, Django o Psycopg mostraran un error indicando si el problema esta en host, puerto, usuario, password, base de datos o disponibilidad del servidor.

## Ejecutar migraciones iniciales

No ejecutes migraciones hasta tener PostgreSQL real configurado.

Algunos comandos relacionados con migraciones pueden intentar consultar la base de datos aunque no creen tablas. Si `DB_NAME` no esta definido, Django mostrara un error de configuracion de base de datos.

Cuando la conexion este lista:

```bash
backend/.venv/bin/python backend/manage.py migrate
```

En esta fase solo se crean tablas internas de Django, por ejemplo:

- `auth_user`
- `auth_group`
- `auth_permission`
- `django_admin_log`
- `django_content_type`
- `django_migrations`
- `django_session`

Estas tablas son propias de Django. No son todavia las tablas funcionales de EMMA.

## Iniciar Django

Con PostgreSQL configurado:

```bash
backend/.venv/bin/python backend/manage.py runserver
```

Por defecto Django quedara disponible en:

```text
http://127.0.0.1:8000/
```

## Como saber si la aplicacion se conecto correctamente

Una comprobacion minima es:

```bash
backend/.venv/bin/python backend/manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('Conexion OK')"
```

Si imprime `Conexion OK`, Django pudo abrir conexion con PostgreSQL usando las variables de entorno.

## Que no esta implementado todavia

- Modelos funcionales de EMMA.
- Migraciones funcionales de negocio.
- CRUDs.
- Serializers.
- APIs.
- ViewSets.
- Routers.
- Permisos y roles de negocio.
- Microsoft Entra ID.
- Auditoria funcional.
- Migracion de archivos Excel.
- Frontend separado.

## Proximos pasos

- Crear Django Models a partir del modelo fisico aprobado.
- Crear migraciones funcionales.
- Definir servicios y logica de negocio.
- Construir APIs.
- Integrar el frontend separado.
- Definir autenticacion y autorizacion.
- Implementar auditoria funcional.
