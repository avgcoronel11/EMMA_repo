# Migracion de Archivos a Base de Datos

Este procedimiento carga los Excel de la carpeta `Archivos/` en las tablas maestras y de configuracion de EMMA.

## 1. Activar entorno virtual

Desde la carpeta del proyecto:

```bash
cd /home/valen/EMMA/emma
source /home/valen/EMMA/.venv/bin/activate
```

Verificar:

```bash
which python
python --version
```

Debe apuntar a `/home/valen/EMMA/.venv/bin/python`.

## 2. Instalar dependencias de lectura Excel

El comando necesita `pandas` y `openpyxl`.

```bash
python -m pip install pandas openpyxl
```

Verificar:

```bash
python -c "import pandas, openpyxl; print(pandas.__version__, openpyxl.__version__)"
```

## 3. Verificar variables de base de datos

El archivo `.env` debe tener estos valores configurados:

```text
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=
```

El proyecto usa PostgreSQL con `sslmode=require`.

## 4. Validar modelos y migraciones

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
```

Ambos comandos deben terminar sin errores.

## 5. Aplicar migraciones de esquema

Antes de cargar datos, las tablas deben existir en la base.

```bash
python manage.py migrate
```

Si la base ya tenia tablas antiguas del modelo monolitico, confirmar antes si se deben borrar o migrar datos. No borrar tablas si hay datos reales que conservar.

## 6. Validar carga sin persistir datos

Ejecutar primero en modo `dry-run`. Esto lee los Excel, valida columnas y prueba las operaciones ORM, pero revierte la transaccion al final.

```bash
python manage.py migrar_archivos_bd \
  --origen Archivos \
  --version-reglas 2026.1 \
  --vigencia 2026-09-14 \
  --dry-run \
  --continuar-con-error \
  --reporte reportes/migracion_archivos_dry_run.json
```

Revisar el reporte:

```bash
cat reportes/migracion_archivos_dry_run.json
```

## 7. Ejecutar carga real

Si el `dry-run` esta correcto:

```bash
python manage.py migrar_archivos_bd \
  --origen Archivos \
  --version-reglas 2026.1 \
  --vigencia 2026-09-14 \
  --reporte reportes/migracion_archivos.json
```

## 8. Reprocesar archivos ya cargados

El comando calcula un hash SHA-256 por archivo. Si una fuente ya fue cargada exitosamente con el mismo hash, se omite.

Para forzar reproceso:

```bash
python manage.py migrar_archivos_bd \
  --origen Archivos \
  --version-reglas 2026.1 \
  --vigencia 2026-09-14 \
  --force \
  --reporte reportes/migracion_archivos_force.json
```

## 9. Cargar solo una o varias fuentes

Ejemplo:

```bash
python manage.py migrar_archivos_bd \
  --origen Archivos \
  --solo SARO ARBOL_PROCESOS CLASIFICACIONES \
  --dry-run
```

Codigos disponibles:

```text
SARO
ARBOL_PROCESOS
ESTRUCTURA
CLASIFICACIONES
GERENCIA_DIRECCION
SISTEMA
PRINCIPIO_COSO
SUBFACTOR_RIESGO
CUENTAS_GENERAL
CUENTAS_RO_2026
CUENTAS_OPERATIVO
CFG_PROBABILIDAD
CFG_IMPACTO
CFG_SEVERIDAD
```

## 10. Validacion posterior

Entrar a Django shell:

```bash
python manage.py shell
```

Ejemplos de conteos:

```python
from django.apps import apps

for table in [
    "fuente_dato",
    "carga_fuente",
    "riesgo_generico",
    "cat_proceso",
    "catalogo",
    "catalogo_valor",
    "estructura_organizacional",
    "cuenta_contable",
    "cfg_probabilidad",
    "cfg_nivel_impacto",
    "cfg_severidad",
]:
    model = next(m for m in apps.get_models() if m._meta.db_table == table)
    print(table, model.objects.count())
```

## Comando creado

El comando vive en:

```text
backend/apps/compartido/management/commands/migrar_archivos_bd.py
```
