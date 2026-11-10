# Pasos 2 y 3 - Separacion de modelos Django por dominio

Este documento explica de forma simple que se hizo en los pasos 2 y 3 para pasar de un `models.py` monolitico a una estructura por apps de dominio.

## Punto 2: crear las apps por dominio

### Objetivo

Crear una app Django por cada dominio funcional del sistema.

Antes, el proyecto tenia una sola app principal:

```text
backend/
```

Y todos los modelos estaban concentrados en:

```text
backend/models.py
```

La idea fue crear una estructura mas ordenada dentro de `backend/apps/`.

### Apps creadas

Se crearon estas apps:

```text
backend/apps/usuarios/
backend/apps/catalogos/
backend/apps/procesos/
backend/apps/riesgos/
backend/apps/eventos/
backend/apps/planes/
backend/apps/compartido/
```

Cada carpeta representa un dominio funcional:

```text
usuarios     -> usuarios y trazabilidad de personas
catalogos    -> listas y valores reutilizables
procesos     -> estructura de procesos
riesgos      -> riesgos, causas, controles y relacion riesgo-proceso
eventos      -> eventos de riesgo y sus detalles
planes       -> planes de accion
compartido   -> entidades transversales como adjuntos, auditoria y caracteristicas
```

### Comando usado

Las apps se crearon con el comando estandar de Django:

```bash
python manage.py startapp nombre_app
```

En este proyecto se uso el Python del entorno virtual:

```bash
/home/valen/EMMA/.venv/bin/python manage.py startapp usuarios
/home/valen/EMMA/.venv/bin/python manage.py startapp catalogos
/home/valen/EMMA/.venv/bin/python manage.py startapp procesos
/home/valen/EMMA/.venv/bin/python manage.py startapp riesgos
/home/valen/EMMA/.venv/bin/python manage.py startapp eventos
/home/valen/EMMA/.venv/bin/python manage.py startapp planes
/home/valen/EMMA/.venv/bin/python manage.py startapp compartido
```

Inicialmente Django las creo al mismo nivel de `manage.py`. Luego se movieron dentro de:

```text
backend/apps/
```

### Archivos que Django crea automaticamente

Cada app queda con una estructura como esta:

```text
admin.py
apps.py
models.py
tests.py
views.py
__init__.py
migrations/
```

Significado de cada archivo:

```text
__init__.py
```

Hace que la carpeta sea reconocida como paquete Python.

```text
admin.py
```

Sirve para registrar modelos en el panel administrativo de Django.

```text
apps.py
```

Define la configuracion de la app.

```text
models.py
```

Contiene los modelos/tablas de esa app.

```text
tests.py
```

Archivo inicial para pruebas automatizadas.

```text
views.py
```

Archivo inicial para vistas o endpoints.

```text
migrations/
```

Carpeta donde Django guarda las migraciones de base de datos de esa app.

### Ajuste realizado en `apps.py`

Como las apps quedaron dentro de `backend/apps/`, se ajusto el atributo `name` de cada app.

Ejemplo:

```python
class UsuariosConfig(AppConfig):
    name = "backend.apps.usuarios"
```

Esto le indica a Django la ruta real donde vive la app.

## Punto 3: mover los modelos a su dominio

### Objetivo

Tomar los modelos que estaban todos juntos en:

```text
backend/models.py
```

Y moverlos al `models.py` de la app que corresponde a su dominio.

### Distribucion aplicada

Los modelos quedaron distribuidos asi:

```text
backend/apps/usuarios/models.py
    Usuario

backend/apps/catalogos/models.py
    Catalogo
    CatalogoValor

backend/apps/procesos/models.py
    CatProceso

backend/apps/riesgos/models.py
    Riesgo
    Causa
    Control
    RiesgoProceso

backend/apps/eventos/models.py
    EventoRiesgo
    EventoCausa
    EventoControl
    EventoCuentaContable
    EventoDistribucionLinea

backend/apps/planes/models.py
    PlanAccion

backend/apps/compartido/models.py
    EntidadCaracteristica
    Adjunto
    Auditoria
```

### Que paso con `backend/models.py`

El archivo `backend/models.py` ya no contiene los modelos.

Quedo solo con una nota indicando que los modelos fueron separados por dominio:

```python
"""Los modelos del proyecto fueron separados por dominio en backend.apps."""
```

### Ajuste de relaciones entre modelos

Cuando todos los modelos estaban en el mismo archivo, una relacion podia escribirse asi:

```python
usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT)
```

Pero al separar los modelos en distintas apps, se actualizaron las relaciones usando texto:

```python
usuario = models.ForeignKey("usuarios.Usuario", on_delete=models.PROTECT)
```

La estructura usada es:

```text
"nombre_app.NombreModelo"
```

Ejemplos:

```python
"usuarios.Usuario"
"catalogos.CatalogoValor"
"procesos.CatProceso"
"riesgos.Riesgo"
"riesgos.Control"
"eventos.EventoRiesgo"
"planes.PlanAccion"
```

Esto evita problemas de importaciones circulares entre apps.

### Ejemplos reales

En `riesgos/models.py`, `Riesgo` apunta a `Usuario`:

```python
usuario_ultima_edicion = models.ForeignKey(
    "usuarios.Usuario",
    on_delete=models.PROTECT,
    null=True,
    blank=True,
    related_name="riesgos_editados",
)
```

En `eventos/models.py`, `EventoRiesgo` apunta a `Riesgo`:

```python
riesgo = models.ForeignKey(
    "riesgos.Riesgo",
    on_delete=models.PROTECT,
    related_name="eventos",
)
```

En `planes/models.py`, `PlanAccion` apunta a `EventoRiesgo`:

```python
evento = models.ForeignKey(
    "eventos.EventoRiesgo",
    on_delete=models.CASCADE,
    related_name="planes_accion",
)
```

En `compartido/models.py`, `Adjunto` puede apuntar a evento o plan:

```python
evento = models.ForeignKey(
    "eventos.EventoRiesgo",
    on_delete=models.CASCADE,
    null=True,
    blank=True,
    related_name="adjuntos",
)

plan = models.ForeignKey(
    "planes.PlanAccion",
    on_delete=models.CASCADE,
    null=True,
    blank=True,
    related_name="adjuntos",
)
```

### Validacion realizada

Se valido que los archivos de Python compilaran correctamente.

Tambien se hizo una prueba de carga de Django registrando las apps nuevas temporalmente en memoria, sin modificar `settings.py`.

Resultado:

```text
System check identified no issues (0 silenced).
```

## Que no se ha hecho todavia

Todavia no se han generado migraciones nuevas.

Todavia no se ha aplicado ningun cambio sobre la base de datos.

## Paso posterior realizado

Se registraron las apps nuevas en `INSTALLED_APPS`, dentro de `emma/settings.py`.

Orden usado:

```python
"backend.apps.usuarios",
"backend.apps.catalogos",
"backend.apps.procesos",
"backend.apps.riesgos",
"backend.apps.eventos",
"backend.apps.planes",
"backend.apps.compartido",
```

## Siguiente paso

El siguiente paso es revisar el estado de las migraciones existentes, especialmente `backend/migrations/0001_initial.py`, antes de generar migraciones nuevas para las apps separadas.

Despues de esa revision se podra decidir si se elimina la migracion antigua y luego ejecutar `makemigrations`.
