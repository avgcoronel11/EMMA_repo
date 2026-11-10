# Pruebas unitarias — Módulo Matriz EMMA

## Alcance y criterio de lectura

Este documento registra el estado técnico validado de la Matriz de Riesgos y
las acciones realizadas específicamente durante la tarea de pruebas. Las reglas
funcionales, contratos API, permisos, motor de valoración y autenticación no se
modificaron. Las funcionalidades marcadas como existentes corresponden a código
previamente implementado que fue revisado y ejecutado en regresión.

## 1. Frontend Riesgos: consultas, filtros y detalle

**Estado:** validado y ampliado.

- El cliente HTTP está centralizado en `frontend/core/api_client.py`.
- Las vistas usan helpers para filtros, paginación, respuesta de lista y carga
  de detalle/valoraciones.
- Se verificaron búsqueda, paginación, estados vacíos, detalle, precarga de la
  última valoración y render HTMX/loading.

## 2. Frontend Riesgos: creación y edición

**Estado:** existente y validado.

- `RiesgoCreateForm` construye el payload y exige una valoración completa si
  se diligencia cualquier dato de valoración.
- Se verificaron creación, edición sin código GR, errores de API por campo,
  inactivación con justificación y transformación de payload.
- El frontend no calcula fórmulas de riesgo; solo envía entradas al backend.
- Se añadieron las multiselecciones de frente, checklist y factor/tipo de
  evento, junto con control de cambios, frecuencia y detalle para `Eventual`.

## 3. Frontend Causas y Controles

**Estado:** validado y ampliado.

- Formularios serializan IDs de riesgo, causa y catálogo sin duplicar lógica
  de negocio.
- Se verificaron listado, búsqueda, vacío, creación, edición, detalle,
  asociación, retiro, reutilización, catálogo, evaluación y mensaje residual.
- Los mocks del cliente API prueban vistas y contratos locales; no sustituyen
  una prueba E2E real.
- Control carga sistemas y principios COSO desde `catalogo_valor`; persiste
  cuentas por relación N:M y checklists por control.

## 4. Backend Riesgos: CRUD, estados y validaciones

**Estado:** existente y validado por integración.

- El CRUD HTTP está coordinado por las views de API y delega persistencia en
  `RiesgoService`.
- `RiesgoCreateSerializer` y `RiesgoUpdateSerializer` validan el contrato;
  no se permite enviar manualmente `codigo_riesgo`.
- La inactivación exige justificación mediante `RiesgoInactivarSerializer` y
  `RiesgoService.inactivar_riesgo`.
- La suite de regresión cubrió respuestas de validación, conflictos y estados
  activo/inactivo.

## 5. Generación segura de códigos GR

**Estado:** existente y validado por integración.

- `codigo_gr_service.py` usa secuencia PostgreSQL, bloqueo advisory y consulta
  de máximo histórico para evitar colisiones.
- La generación permanece dentro de la transacción de creación del riesgo.
- No se alteró la secuencia, el formato `GR<n>` ni la regla de concurrencia.

## 6. Motor de evaluación inherente y residual

**Estado:** ampliado con pruebas unitarias.

- El motor está separado en `services/valoracion/`: probabilidad, impacto,
  severidad, residual y utilidades.
- Se validaron fronteras históricas aprobadas: 1 %, 5 %, 10 % y 15 %, además
  de valores inmediatamente superiores.
- Se validaron nulos, población inválida, eventos negativos, máximo de los
  componentes, mínimos residuales, deduplicación de controles y umbrales de
  movimiento.
- No se modificaron fórmulas, equivalencias ni etiquetas aprobadas.

## 7. Backend Causas

**Estado:** existente y validado por integración.

- `CausaService` centraliza creación, edición, asociación y retiro.
- La generación de código de causa usa bloqueo transaccional PostgreSQL.
- Se mantienen la validación de riesgo inexistente, duplicados y la protección
  contra retirar la última asociación válida.

## 8. Backend Controles y efectividad

**Estado:** ampliado con pruebas unitarias y validado por integración.

- `ControlService` centraliza creación, edición, asociación, retiro y
  evaluación.
- Las reglas de Diseño, Operatividad, VPR y Efectividad se conservan en
  `recalcular_evaluacion` y `_efectividad`.
- Se probaron evaluación completa/incompleta, matriz de efectividad,
  normalización de claves y fallback débil para combinaciones no aprobadas.

## 9. Relaciones Riesgo–Causa–Control

**Estado:** existente y validado por integración.

- Las tablas puente `RiesgoCausa` y `RiesgoCausaControl` son la fuente de las
  asociaciones vigentes.
- Se validaron asociación, reutilización, rechazo de duplicados, retiro y
  consultas inversas.
- La compatibilidad temporal con FKs históricas se conserva sin cambios.

## 10. Auditoría e históricos de Matriz

**Estado:** existente y ampliado con unitarias aisladas.

- `historico_matriz_service.py` centraliza versiones y origen
  `OPERACION`/`BACKFILL`.
- Se probaron cálculo de siguiente versión y constantes de origen sin depender
  de PostgreSQL.
- La regresión existente cubre snapshots, histórico inmutable, solo lectura y
  rollback cuando falla la escritura histórica.

## 11. Integración Frontend + Backend + PostgreSQL de Matriz

**Estado:** regresión backend verde; E2E real no cubierto por mocks frontend.

- La regresión ejecutada por consola completó **66 pruebas backend** en verde
  usando PostgreSQL de pruebas reutilizada con `--keepdb`.
- Frontend ejecutó **32 pruebas** en verde con cliente API simulado.
- La integración real navegador–frontend–API no se declara cubierta por estas
  pruebas; requeriría una suite E2E separada.

## 12. API, permisos y regresión de Matriz

**Estado:** existente y validado.

- Las views sensibles mantienen `IsAuthenticated`.
- La regresión validó 400, 403, 404, 405, 409 y errores de rollback esperados.
- Los logs de `ValidationError`, `NotFound`, `NotAuthenticated`,
  `ReglaNegocioError` e `IntegrityError` inducido por mocks forman parte de
  escenarios negativos aprobados y no representan fallos de la suite.

## 13. Desarrollo Matriz de Riesgos

**Estado:** reglas existentes conservadas; modelo extendido para los campos
autorizados de la matriz.

- Se respetaron Riesgos, Causas, Controles, evaluación inherente y residual,
  históricos, rollback, auditoría y permisos técnicos existentes.
- No se modificaron Entra/MSAL, Bearer, roles, perfiles, claims, alcance por
  proceso ni las reglas aprobadas de Riesgo y Control.
- Se añadieron las migraciones `0008` y `0009` de Riesgos para relaciones y
  campos expresamente solicitados. La aplicación de `0009` queda pendiente de
  confirmar mientras el host PostgreSQL configurado no resuelva desde este
  entorno.

## 14. Pruebas unitarias realizadas

### Archivos y organización

```text
backend/apps/riesgos/tests/
  test_unitarios.py
  test_integracion_regresion.py
frontend/riesgos/tests/
  test_unitarios.py
  test_views.py
frontend/core/tests/
  test_api_client.py
  test_error_pages.py
```

### Cambios de esta tarea

- Se añadieron 10 pruebas unitarias backend en
  `backend/apps/riesgos/tests/test_unitarios.py`.
- Se añadieron 10 pruebas frontend para cliente API, errores, payloads,
  filtros, paginación, precarga histórica y nuevos campos de matriz.
- Se reorganizaron los archivos de prueba en paquetes `tests/`.
- Se añadió `requirements-dev.txt` con `coverage==7.17.0`.

### Ejecuciones confirmadas

| Suite | Resultado |
| --- | --- |
| Backend integración y regresión | 66/66 correctas |
| Backend unitarias nuevas | 10/10 correctas |
| Frontend Core + Riesgos | 35/35 correctas |

### Cobertura medida

| Capa | Líneas medibles | Cubiertas | Cobertura |
| --- | ---: | ---: | ---: |
| Frontend Matriz y Core relevante | 640 | 519 | 80 % |
| Backend unitario aislado | 297 | 189 | 60 % |

La cobertura backend integral y el consolidado no se consignan como cerrados:
la medición instrumentada de toda la regresión backend debe ejecutarse contra
la base PostgreSQL de pruebas disponible. No se debe inferir un porcentaje
consolidado a partir de un promedio simple.

## Comandos de ejecución

```bash
.venv/bin/python manage.py test backend.apps.riesgos.tests.test_unitarios
.venv/bin/python manage.py test backend.apps.riesgos backend.apps.compartido --keepdb
.venv/bin/python frontend/manage.py test core riesgos
```

Para cobertura backend completa:

```bash
COVERAGE_FILE=/tmp/emma_backend_coverage .venv/bin/coverage run --branch manage.py test backend.apps.riesgos backend.apps.compartido --keepdb
COVERAGE_FILE=/tmp/emma_backend_coverage .venv/bin/coverage report --include='backend/apps/riesgos/*,backend/apps/compartido/*' --omit='*/migrations/*,*/tests.py,*/test_*.py,*/__init__.py' --show-missing
```

## 15. Conexión de catálogos y persistencia de la matriz

| Dato visible | Fuente / persistencia | Columnas o relación |
| --- | --- | --- |
| Sistemas / aplicaciones | `catalogo_valor` | Catálogo `SISTEMA`: `valor_id`, `codigo`, `descripcion`; relación por `entidad_caracteristica.control_id` y `valor_catalogo_id` |
| Principio COSO | `catalogo_valor` | Catálogo `PRINCIPIO_COSO`, con la misma relación `entidad_caracteristica` |
| Cuenta contable | `cuenta_contable` | `cuenta_id`, `cuenta_10`, `cuenta_6`, `descripcion`; puente `control_cuenta_contable(control_id, cuenta_id)` |
| Aserciones, atributos y checklist de riesgos del control | `control_checklist` | `control_id`, `tipo` (`ASERCION`, `ATRIBUTO`, `RIESGO`) y `valor` |
| Código homologado Grupo Aval del control | `catalogo_valor` | Catálogo `CONTROL_GENERICO`: se muestran `codigo` y `descripcion`; se guarda `control.control_generico_valor_id` |
| Frente, checklist y factor/tipo del riesgo | `riesgo` | JSON `frente_riesgo_asociado`, `checklist_riesgo`, `factor_riesgo_tipo_evento` |
| Control de cambios y frecuencia | `riesgo` | `control_cambios`, `frecuencia`, `detalle_frecuencia` |

La relación que parecía faltar entre `catalogo` y `catalogo_valor` existe como
`catalogo_valor.catalogo_id → catalogo.catalogo_id`. El frontend consulta el
catálogo correspondiente —por ejemplo `catalogos/SISTEMA/valores`— en vez de
reutilizar valores de control genérico.
