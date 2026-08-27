# Registro de cambios y objetivos de EMMA Backend

Este documento registra los cambios realizados durante la creacion de la estructura minima Django del backend de EMMA.

## Objetivo de esta tarea

Crear una estructura minima de Django para gestionar el esquema futuro de EMMA, dejando preparada la configuracion para PostgreSQL mediante variables de entorno.

Esta tarea no incluye modelos funcionales, APIs, serializers, permisos de negocio, autenticacion con Microsoft Entra ID, migracion de Excel ni logica funcional de EMMA.

## Cambios realizados

### 2026-08-26

- Se inicio la estructura base en `backend/`.
- Se agrego `requirements.txt` con dependencias minimas planificadas:
  - `Django==5.2.17`
  - `psycopg[binary]==3.3.4`
- Se agrego `.gitignore` en la raiz para excluir archivos locales, entornos virtuales y caches.
- Se creo el entorno virtual en `backend/.venv/` usando Python 3.14.4.
- Se creo el proyecto Django `config` dentro de `backend/`.
- Se crearon apps Django vacias para organizar dominios iniciales:
  - `usuarios`
  - `matriz`
  - `eventos`
  - `planes`
  - `catalogos`
  - `auditoria`
- Se configuro PostgreSQL en `backend/config/settings.py` mediante variables de entorno.
- Se agrego `backend/.env.example` sin credenciales reales.
- Se agrego `backend/README.md` con instrucciones de instalacion, configuracion, ejecucion y validacion.
- Se valido `python manage.py check` correctamente.
- Se intento `makemigrations --check --dry-run`, pero Django requiere `DB_NAME` para revisar el historial de migraciones; queda pendiente hasta configurar PostgreSQL real.
- Se agrego `.gitattributes` en la raiz para normalizar saltos de linea entre Linux y Windows.
- Se agrego `backend/docs/estructura_backend_django.docx` con la estructura creada y la definicion de cada carpeta y archivo.

## Decisiones confirmadas

- El backend se ubicara en `backend/`.
- El modulo principal de configuracion de Django se llamara `config`.
- Se usara Python 3.14.4 en el entorno actual.
- Se usara Django 5.2 LTS.
- Se usara Psycopg 3 para PostgreSQL.
- Las credenciales de PostgreSQL se leeran desde variables de entorno.
- No se instalara Django REST Framework en esta fase.
- No se inicializara ni reparara Git en esta tarea.
