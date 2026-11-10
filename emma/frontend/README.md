# EMMA Frontend

Frontend separado para EMMA construido con Django, HTMX, Tabler y Reflex.

## Estructura

```text
frontend/
|-- manage.py
|-- config/
|-- core/
|-- catalogos/
|-- riesgos/
|-- eventos/
|-- planes/
|-- templates/
|-- static/
|-- requirements.txt
|-- .env.example
`-- README.md
```

`core/api_client.py` es el unico punto que debe comunicarse con la API del backend.

## Ejecucion local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py runserver
```

La configuracion no declara modelos ni base de datos para el frontend.
