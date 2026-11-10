# Propósito y alcance

Esta es la fuente consolidada de decisiones, reglas y pendientes del módulo Riesgos de EMMA. Reúne las decisiones ya documentadas sin completar vacíos mediante supuestos. Cuando una fuente contradice otra o el código actual, se conserva la diferencia como una cuestión abierta.

# Fuentes consolidadas

| Fuente | Contenido que aporta | Tratamiento |
|---|---|---|
| Tarea 1 y 2 Inventario Completo de Interfaz y Validaciones | Acciones del Riesgo, campos de interfaz, estados, validaciones y definición GR | Fuente funcional de interfaz y reglas de negocio |
| Matriz de Perfiles y Permisos | Perfiles, acciones autorizadas y alcance | Fuente funcional de autorización |
| Reglas de Motores de Riesgo Confirmadas | Riesgo inherente, residual y efectividad de controles | Fuente funcional del motor |
| Contrato API | Rutas, filtros, respuestas, detalle y paginación | Fuente de integración vigente, con pendientes explícitos |
| Adenda Modelo Lógico Código GR | Consecutivo, formato y preservación de históricos | Fuente de código GR |
| Modelo lógico, UML y entidades | Entidades, atributos y relaciones disponibles | Fuente de estructura de datos |
| Código frontend y backend | Estado real implementado | Evidencia técnica, no reemplaza la decisión funcional |

# Decisiones aprobadas

## Código GR

- El código visible de un riesgo nuevo es `GR<número>`, sin ceros a la izquierda.

- PostgreSQL genera un consecutivo numérico seguro.

- El código no se digita ni se modifica manualmente.

- Antes de asignar un nuevo código se sincroniza con el mayor histórico que cumpla el patrón `GR<número>`.

- Los registros históricos conservan literalmente su código original; si no cumple el patrón GR, su consecutivo puede permanecer nulo.

- La unicidad final del código corresponde a PostgreSQL.

## Estados y conservación histórica

- Los estados claramente definidos para Riesgo son Activo e Inactivo.

- Activo puede consultarse, editarse y relacionarse con causas, controles, eventos y demás elementos permitidos.

- Inactivo se conserva para consulta histórica y no elimina relaciones ni información asociada.

- La inactivación exige justificación y confirmación expresa del usuario.

- La fuente de validaciones establece justificación mínima de 10 caracteres.

- Borrador se menciona como una posibilidad a evaluar; no queda aprobado como estado operativo.

- La reactivación de Inactivo a Activo queda pendiente de definición de negocio.

## Consulta y filtros

El listado debe permitir consulta de riesgos activos e inactivos. Los filtros aprobados son:

- código de riesgo;

- estado;

- riesgo homologado;

- vicepresidencia;

- proceso;

- subproceso;

- dueño del proceso.

El contrato establece estas correspondencias:

| Parámetro | Regla |
|---|---|
| `estado` | Coincidencia exacta sin distinción de mayúsculas |
| `codigo_riesgo` | Coincidencia exacta sin distinción de mayúsculas |
| `riesgo_homologado` | Coincidencia exacta sin distinción de mayúsculas |
| `vicepresidencia` | Sobre la estructura de procesos |
| `proceso` | Corresponde a proceso nivel 0 |
| `subproceso` | Corresponde a proceso nivel 1 |
| `dueno_proceso` | Sobre el dueño del riesgo |
| `search` | Nombre, referencia SARO, ciclo, subfactor, descripción de proceso, línea, macroproceso y dueño |

Los listados paginados usan `count`, `next`, `previous` y `results`.

## Contenido funcional de un Riesgo

La creación aprobada contempla registrar información general, estructura organizacional, riesgo homologado, factores y subfactores, valoración inherente, causas, controles, valoración residual y elementos aplicables como sistemas, cuentas contables, aserciones y atributos de información.

La consulta de detalle debe contemplar como mínimo:

- información general;

- estado;

- proceso y estructura organizacional;

- riesgo homologado;

- valoración inherente;

- causas;

- controles;

- valoración residual;

- eventos relacionados;

- planes de acción relacionados;

- historial de modificaciones.

La obligatoriedad exacta de la información mínima antes de finalizar el registro aparece pendiente de definición en el inventario funcional.

## Motor de valoración inherente

- La probabilidad histórica se deriva de Eventos de Riesgo dividido por Población Expuesta.

- La probabilidad cualitativa es el promedio redondeado de Exposición, Complejidad y Entorno.

- La probabilidad inherente final es el mayor nivel entre cualitativa, ocurrencia e histórica.

- El impacto inherente corresponde al mayor nivel de siete dimensiones: Legal, Reputacional, Servicio al cliente, Información, Continuidad, Contagio y Financiero.

- La severidad inherente resulta del cruce de probabilidad e impacto en la tabla de severidad vigente.

Para probabilidad histórica, la fuente indica que las fronteras exactas 1 %, 5 %, 10 % y 15 % recaen en el valor por defecto Muy Baja conforme a la fórmula original. Cualquier implementación debe respetar esa definición literal o requerir una decisión funcional explícita para cambiarla.

## Motor de valoración residual

- Sin controles asociados, probabilidad, impacto y severidad residual toman los valores inherentes.

- Diseño: cumple solo cuando las cuatro respuestas de diseño son Sí.

- Operatividad: o1 en Sí implica incumplimiento; o2, o3 y o4 deben ser Sí; o5 debe ser No o NA.

- Falla VPR es No únicamente si diseño y operatividad cumplen.

- Efectividad Fuerte y Moderado equivalen a 1 para los indicadores de reducción; Débil equivale a 0.

- Los controles preventivos reducen probabilidad.

- Para impacto, los correctivos prevalecen; los detectivos se usan solo si no hay reducción correctiva.

- No se suman las reducciones detectiva y correctiva.

- La severidad residual usa el mismo cruce de severidad.
- El nivel mínimo de Probabilidad Residual e Impacto Residual es 1, mediante `max(1, nivel_inherente - reducción)`. Esta decisión fue confirmada para la Fase 4.

## Roles y permisos aprobados

| Perfil | Riesgos | Alcance |
|---|---|---|
| Control Interno | Consultar, crear, editar e inactivar | Todo el banco |
| Consulta Riesgo y Controles | Solo consultar | Procesos asignados |
| Dueño de Proceso | Consultar y editar | Edición en procesos asignados; la fuente debe aplicarse literalmente para el alcance de consulta |
| Auditoría | Solo consultar | Todo el banco |
| Informador | Sin gestión aprobada de Riesgos | Registra eventos, no Riesgos |
| Creación Usuarios | Sin gestión funcional aprobada de Riesgos | Administración de usuarios |
| AdministradorGeneralCERO | Sin gestión funcional aprobada de Riesgos | Configuración técnica y permisos |

La autorización debe aplicarse en frontend y API; ocultar un botón no sustituye una validación de backend.

# Contrato API actual

| Operación | Endpoint actual |
|---|---|
| Listar y crear | `GET/POST /api/v1/riesgos/` |
| Detalle y edición | `GET/PATCH /api/v1/riesgos/{riesgo_id}/` |
| Inactivar | `POST /api/v1/riesgos/{riesgo_id}/inactivar/` |
| Calcular valoración sin guardar | `POST /api/v1/riesgos/calcular-valoracion/` |
| Evaluar control | `PATCH /api/v1/riesgos/{riesgo_id}/controles/{control_id}/evaluacion/` |
| Recalcular residual | `POST /api/v1/riesgos/{riesgo_id}/recalcular-residual/` |
| Historial de valoraciones | `GET /api/v1/riesgos/{riesgo_id}/valoraciones/` |

El contrato actual declara pendientes eventos, planes de acción e historial dentro del detalle, además de alcance de lectura por perfiles/procesos y correspondencia definitiva de selectores de proceso.

# Estado de implementación verificado

## Frontend existente

- Listado con filtros, búsqueda, tabla, paginación y estado vacío.

- Creación de un subconjunto de información general.

- Detalle que muestra información general reducida, valoración resumida, conteos de procesos/causas/controles e historial de valoraciones.

- Edición de un subconjunto de campos generales.

- Inactivación con confirmación del navegador.

- Cliente HTTP único que envía el token de sesión como Bearer.

## Backend existente

- Endpoints de listado, detalle, creación, PATCH, inactivación, valoración, evaluación de controles y recálculo residual.

- Generación backend de código GR.

- Filtros y paginación de riesgos.

- Persistencia de resultados de valoración e historial de valoraciones.

## Brechas verificadas

| Área | Brecha |
|---|---|
| Detalle | No muestra procesos, causas y controles en detalle; no incluye eventos, planes ni historial de modificaciones |
| Creación | No captura relaciones, valoración, causas, controles ni varios campos funcionales |
| Edición | No gestiona relaciones ni valoración y no bloquea visualmente los inactivos |
| Inactivación | La interfaz y backend no aplican el mínimo de 10 caracteres; backend no impide re-inactivar |
| Estados | Backend acepta valores y modificaciones sin validación completa del flujo de estados |
| Catálogos | Varios campos frontend son texto libre en lugar de catálogo o estructura validada |
| Permisos | No hay autorización por acción, rol ni proceso en frontend o backend |
| Motor | La probabilidad final actual conserva prioridad cualitativa en lugar del máximo; los umbrales históricos y el límite residual no coinciden con la fuente funcional |
| Pruebas | Las pruebas frontend mockean API; no existe evidencia de integración ejecutada contra API y PostgreSQL reales |

# Contradicciones registradas

| Tema | Fuente o código en conflicto | Estado |
|---|---|---|
| Probabilidad final | Reglas confirmadas: máximo de tres componentes; código actual: prioridad cualitativa | Debe corregirse o aprobarse una excepción |
| Umbrales históricos | Reglas confirmadas usan definición literal con fronteras; código usa rangos distintos | Debe corregirse o aprobarse una excepción |
| Límite residual | Fuente anterior no fijaba mínimo explícito; Fase 4 confirma mínimo 1 | Decisión resuelta: conservar `max(1, ...)` |
| Justificación de inactivación | Inventario exige mínimo 10; código solo exige valor no vacío | Debe corregirse |
| Código manual | Documentación de flujo/prueba antigua usa códigos manuales; adenda y contrato exigen GR generado | La adenda y contrato prevalecen |
| Detalle completo | Inventario exige eventos, planes e historial; contrato actual los declara pendientes | Requiere ampliar contrato o ajustar alcance |
| Permisos | Matriz define perfiles; código no implementa autorización | Pendiente técnico y de arquitectura |

# Definiciones confirmadas para Fase 4

La Fase 4 industrializa exclusivamente el backend de Causas, Controles, evaluación de efectividad, relaciones Riesgo–Causa–Control e integración de controles con el motor residual. No reabre el diseño funcional de los motores inherente y residual, no modifica frontend, eventos, planes, Azure, Entra, código GR ni catálogos de valoración existentes.

## Causas

- Una causa puede asociarse a múltiples riesgos y toda causa debe conservar al menos una asociación válida.
- La combinación Riesgo + Causa es única. Una causa existente se reutiliza conservando su identidad; asociarla no crea una nueva causa maestra.
- La creación de una causa nueva y su primera asociación debe ser transaccional.
- No se puede retirar una asociación si deja la causa sin asociaciones válidas.
- No se elimina físicamente ni se inactiva una causa salvo regla expresa posterior.
- El código automático original usa la forma `C<número>`; su generación debe ser única y segura ante concurrencia, conservando códigos de referencia adicionales cuando existan.
- Los atributos que deben contrastarse con el modelo vigente son: código, código actual o referencia, descripción, subfactor, línea, macroproceso, dueño y relaciones aprobadas.

## Controles

- Todo control debe relacionarse, como mínimo, con una causa.
- Una causa puede tener varios controles y un control puede mitigar varias causas.
- Un control se puede reutilizar entre riesgos y puede mitigar varias causas del mismo riesgo.
- La tripleta Riesgo + Causa + Control es única.
- Un control no puede quedar relacionado solamente a un riesgo sin identificar la causa mitigada.
- La reutilización preserva la identidad del control; no crea una nueva entidad maestra.
- No se elimina físicamente ni se inactiva un control salvo regla expresa posterior.
- Tipo: Preventivo, Detectivo o Correctivo. Naturaleza: Manual, Dependiente de TI o Automatizado.
- Frecuencia, ejecutores y características multivalor deben usar catálogos o relaciones existentes en PostgreSQL; no se crean columnas solo porque un campo exista en la interfaz original.

## Diseño, operatividad y efectividad

- Cumple Diseño es Sí solo si D1, D2, D3 y D4 son Sí.
- Cumple Operatividad es Sí solo si O1 es No, O2 a O4 son Sí y O5 es No o NA.
- Falla VPR es No únicamente cuando Diseño y Operatividad son Sí; en cualquier otra combinación es Sí.
- Con Falla VPR Sí, la Efectividad es Débil.
- Con Falla VPR No, la matriz aprobada es:

| Tipo | Manual | Dependiente de TI | Automatizado |
|---|---|---|---|
| Correctivo | Débil | Moderado | Moderado |
| Preventivo | Moderado | Moderado | Fuerte |
| Detectivo | Moderado | Moderado | Fuerte |

- Las respuestas D1–D4 y O1–O5, los resultados de Diseño, Operatividad, Falla VPR y Efectividad son capas separadas: las respuestas se persisten y los resultados se calculan centralizadamente en un servicio backend.
- Los resultados calculados no pueden modificarse libremente contradiciendo las respuestas.

## Relaciones e integridad

- Riesgo ↔ Causa es N:M.
- Causa ↔ Control es N:M en el contexto de un Riesgo.
- La relación Riesgo + Causa + Control identifica explícitamente el control que mitiga una causa dentro de un riesgo y es única.
- No puede existir una tripleta si la causa no está asociada al riesgo, o si el riesgo, causa o control no existen.
- La inactivación de un riesgo conserva causas, controles, asociaciones e historial para consulta histórica y no aplica inactivación en cascada.
- No se debe usar `CASCADE` como mecanismo predeterminado de borrado histórico.
- Las versiones documentales 1:N anteriores no prevalecen sobre estas cardinalidades N:M confirmadas. La implementación debe inspeccionar estructuras existentes antes de proponer migraciones y preservar datos históricos.

## Integración con Riesgo Residual

- Los controles asociados al riesgo alimentan el motor residual sin recalcular valoraciones históricas.
- Fuerte y Moderado aportan 1; Débil aporta 0.
- Cada promedio por tipo usa como denominador todos los controles asociados al riesgo. Un control de otro tipo aporta 0 al promedio evaluado.
- Un mismo control asociado a varias causas del mismo riesgo se cuenta una sola vez por identificador de control.
- No se introducen filtros nuevos Activo/Inactivo que alteren el conjunto de controles de la fórmula original.
- Promedio mayor a 0,20 reduce 2 niveles; promedio entre 0,10 y 0,20, inclusivo, reduce 1; promedio menor a 0,10 reduce 0.
- Preventivos reducen probabilidad. Correctivos reducen impacto y prevalecen sobre Detectivos; Detectivos reducen impacto solo si no existe reducción Correctiva. Las reducciones no se suman.
- Sin controles asociados, el residual conserva los valores inherentes.

## Permisos y auditoría para Fase 4

- Control Interno tiene consulta global, creación y edición funcional global, gestión de relaciones y calificación autorizada.
- Dueño de Proceso consulta global y edita riesgos y controles solo de procesos asignados; no se le concede creación, inactivación o edición de causas sin permiso expreso.
- Consulta Riesgo y Controles consulta solo procesos asignados y no modifica.
- Auditoría consulta global sin modificación. Informador, Creación Usuarios y AdministradorGeneralCERO no reciben permisos funcionales de Causas o Controles por defecto.
- Los permisos se aplican sobre entidades y asociaciones en API, no solo en interfaz.
- Se reutiliza la auditoría transversal existente. Debe registrar entidad, acción, usuario, fecha/hora, valores previos y nuevos, relaciones modificadas y motivo cuando aplique.

## Restricciones y orden de ejecución

- No se ejecutan migraciones ni se escribe código de Fase 4 sin aprobación del plan técnico posterior a la inspección.
- No se crean tablas nuevas por conveniencia: primero se verifica el modelo, las migraciones y PostgreSQL.
- No se proponen nuevas migraciones desde Excel ni se recrean catálogos ya existentes en PostgreSQL.
- Las operaciones de múltiples entidades o asociaciones deben ser transaccionales.
- Las pruebas de integración usan PostgreSQL aislado y nunca información productiva.

## Inspección técnica Fase 4

### Aprobación técnica Fase 4

La implementación técnica de Fase 4 fue aprobada con estas condiciones:

- No se eliminan todavía las FKs directas históricas `causa.riesgo_id` y `control.riesgo_id`.
- Las migraciones de relaciones deben ser escalonadas, reversibles cuando sea posible y no pueden ejecutarse hasta revisar datos afectados en PostgreSQL aislado.
- La asociación histórica Riesgo–Causa se migra conservando identificadores y comprobando ausencia de pérdidas y duplicados.
- No se inventan relaciones históricas Control–Causa. Los controles sin causa conocida se preservan y se identifican para remediación.
- Las nuevas relaciones deben imponerse tanto en backend como en base de datos.
- El filtro de controles Activos del residual debe compararse con el comportamiento original antes de conservarse o retirarse; no se modifica automáticamente por inferencia.
- Las valoraciones históricas no se recalculan ni sobrescriben automáticamente.
- La autorización debe proteger API y relaciones. Mientras la identidad/perfiles definitivos dependan de Entra, los endpoints de modificación no pueden quedar abiertos sin autenticación.
- La auditoría transversal debe registrar Causas, Controles, evaluaciones, efectividad, asociaciones y desvinculaciones.

### Estructura actual verificada en código y migraciones

| Elemento | Estado actual | Resultado frente a Fase 4 |
|---|---|---|
| `causa` | Tiene FK obligatoria `riesgo_id`, código único y `on_delete=PROTECT` | Modelo 1:N anterior; no permite reutilización N:M |
| `control` | Tiene FK obligatoria `riesgo_id`, código único y `on_delete=PROTECT` | Modelo 1:N anterior; no identifica causa mitigada ni reutilización N:M |
| Relación Riesgo–Causa | No existe tabla puente; la FK está en `causa` | Falta para cardinalidad confirmada |
| Relación Riesgo–Causa–Control | No existe tabla puente ni restricción de tripleta | Falta para cardinalidad confirmada |
| Respuestas D1–D4 y O1–O5 | Existen en `control`, agregadas por migración `riesgos.0003` | Compatible |
| Servicio de efectividad | Calcula Diseño, Operatividad, Falla VPR y Efectividad en `control_service.py` | Compatible en lógica básica; falta desacoplarlo de la FK directa Riesgo–Control y completar auditoría/permisos |
| Endpoint de evaluación | Existe `PATCH /api/v1/riesgos/{riesgo_id}/controles/{control_id}/evaluacion/` | Parcial: depende de la FK directa actual y recalcula residual automáticamente |
| CRUD de causas | Serializer de detalle; view y service vacíos; sin rutas | No implementado |
| CRUD de controles | Serializer de detalle y endpoint de evaluación; sin CRUD ni rutas | Parcial |
| Auditoría transversal | Modelo y API de lectura existen; Riesgo ya lo utiliza | Reutilizable; Causa, Control y relaciones no la registran |
| Permisos | Módulo `api/permissions.py` vacío y vistas sin `permission_classes` | No implementado |
| Residual | Deduplica controles por código e implementa pesos y prioridad; actualmente filtra controles Activos | Debe adaptarse a controles obtenidos por relaciones y retirar el filtro de estado nuevo si altera el conjunto aprobado |

### Migraciones existentes

- `riesgos.0001_initial` creó `causa` y `control` con FKs directas a `riesgo`.
- `riesgos.0003_motor_riesgo_tarea_3` agregó respuestas D1–D4 y O1–O5 a `control`.
- `riesgos.0004_valoraciones_historicas` crea fotos de controles para valoraciones; no representa relaciones Causa–Control.

No fue posible confirmar el esquema o migraciones aplicadas en PostgreSQL: el host Azure configurado no resuelve desde este entorno. La inspección de base real queda bloqueada técnicamente hasta disponer de conectividad o una base PostgreSQL de integración.

### Estrategia técnica propuesta, pendiente de aprobación

1. Agregar una entidad puente Riesgo–Causa con unicidad de la pareja y FKs de protección histórica.
2. Agregar una entidad puente Riesgo–Causa–Control con unicidad de la tripleta y validación de que su causa pertenezca al mismo riesgo.
3. Migrar cada `causa.riesgo_id` existente a Riesgo–Causa sin alterar la causa maestra.
4. Conservar temporalmente las FKs directas históricas mientras se verifica y remedia información; después retirarlas solo cuando las relaciones puente estén completas y verificadas.
5. No derivar automáticamente tripletas históricas: el esquema actual permite saber el riesgo de un control, pero no la causa que mitiga. Se requiere una fuente de mapeo o una decisión técnica de conservación histórica antes de retirar la FK directa de Control.
6. Implementar CRUD y asociaciones mediante servicios transaccionales, serializers de entrada, selectors de consulta, endpoints siguiendo las convenciones vigentes y auditoría transversal.
7. Adaptar evaluación de controles y recálculo residual para resolver controles mediante relaciones, deduplicar por `control_id` dentro del riesgo y no recalcular valoraciones históricas.
8. Aplicar permisos por acción y alcance de proceso únicamente después de definir la integración técnica de identidad y usuario–proceso; no simular permisos.
9. Crear pruebas unitarias e integración PostgreSQL que cubran entidades, asociaciones, concurrencia, auditoría, efectividad y residual.

### Archivos candidatos a modificar, pendientes de aprobación

- `backend/apps/riesgos/models.py`
- Nueva migración en `backend/apps/riesgos/migrations/`
- `backend/apps/riesgos/services/causa_service.py`
- `backend/apps/riesgos/services/control_service.py`
- Nuevo servicio de relaciones o extensión de los servicios existentes
- `backend/apps/riesgos/selectors/`
- `backend/apps/riesgos/api/serializers/causa.py`
- `backend/apps/riesgos/api/serializers/control.py`
- Nuevos serializers de relaciones
- `backend/apps/riesgos/api/views/causa.py`
- `backend/apps/riesgos/api/views/control.py`
- Nuevas vistas de relaciones o extensiones de las vistas anteriores
- `backend/apps/riesgos/api/urls.py`
- `backend/apps/riesgos/api/permissions.py`
- `backend/apps/riesgos/services/riesgo_service.py`
- `backend/apps/riesgos/services/valoracion/residual.py`
- `backend/apps/riesgos/tests.py`

No se modifica ningún archivo de esta lista hasta aprobar el plan técnico.

### Implementación iniciada tras aprobación

- Se agregó la migración preparada `riesgos.0005_relaciones_riesgo_causa_control`, sin ejecutarla, con tablas puente y migración de las asociaciones históricas Riesgo–Causa.
- Las FKs directas históricas no se retiran ni se alteran en esta migración.
- Se iniciaron servicios, serializers, vistas y rutas para Causas, Controles y asociaciones.
- Los endpoints nuevos requieren autenticación DRF mediante `IsAuthenticated` como protección mínima; la autorización por los siete perfiles continúa bloqueada por la falta de integración backend de claims/perfiles/procesos.
- El servicio residual une controles de las relaciones nuevas con los controles de la FK histórica y deduplica por identificador, para conservar controles históricos sin causa determinada durante la transición.
- El filtro de estado Activo existente no fue retirado: permanece documentado como diferencia pendiente de comparación contra el comportamiento original.
- La verificación sintáctica y `manage.py check` terminaron correctamente. Las pruebas de integración y la ejecución de migraciones continúan bloqueadas por falta de conexión a PostgreSQL.

### Revisión PostgreSQL de datos afectados

La conexión de solo lectura se verificó posteriormente fuera del sandbox. El estado encontrado antes de aplicar la migración `riesgos.0005` es:

| Elemento | Resultado |
|---|---:|
| Migraciones de Riesgos aplicadas | `0001` a `0004` |
| Migración `0005_relaciones_riesgo_causa_control` | No aplicada |
| Riesgos | 1 |
| Causas | 0 |
| Controles | 0 |
| Tablas de asociación nuevas | No existen aún |

Las restricciones reales confirman que `causa.codigo_causa` y `control.codigo_control` son únicos y que ambas tablas tienen FK directa a `riesgo`. No existen datos históricos de Causas o Controles que migrar actualmente; por tanto, aplicar `0005` solo crearía las estructuras puente y su migración de datos no insertaría filas.

Procedimiento propuesto antes de aplicar `0005`:

1. Mantener una copia lógica o punto de restauración de la base de integración.
2. Ejecutar la migración sin retirar ni alterar las FKs directas.
3. Verificar existencia de las dos tablas nuevas y sus restricciones de unicidad.
4. Verificar conteos: Riesgo–Causa debe permanecer en 0 y Riesgo–Causa–Control en 0, pues las tablas fuente están vacías.
5. Ejecutar pruebas de creación y reutilización contra PostgreSQL aislado.
6. No retirar FKs directas hasta que existan datos de prueba y las nuevas relaciones estén verificadas.

### Rectificación posterior: migración y validación HTTP en DEV (2026-10-26)

Esta sección reemplaza los estados anteriores que indicaban que la conectividad, la migración o las tablas puente seguían bloqueadas.

- `riesgos.0005_relaciones_riesgo_causa_control` fue aplicada exclusivamente en PostgreSQL DEV y verificada físicamente: existen `riesgo_causa` y `riesgo_causa_control`, con sus PK, FK `PROTECT`, únicos `uq_riesgo_causa` y `uq_riesgo_causa_control` e índices de FK.
- Las FKs históricas `causa.riesgo_id` y `control.riesgo_id` permanecen. No se retiraron columnas ni se revirtieron migraciones.
- Se probaron por HTTP en DEV creación, consulta, edición, asociación, consulta de asociaciones, rechazo de duplicados y retiro de asociación de Causas; y creación, consulta, edición, asociación y rechazo de duplicados de Controles.
- Las pruebas demostraron que el residual incorpora relaciones nuevas y la FK histórica, con deduplicación por `control_id`; el mínimo de nivel 1 y la prioridad aprobada continúan presentes.
- Se agregaron pruebas automatizadas iniciales de contrato Fase 4 en `backend/apps/riesgos/tests.py`. Aún no se ejecutan contra la base de pruebas porque `test_emma_db` es una base previa (11 MB), queda en migración `riesgos.0004` y no puede borrarse, recrearse, migrarse ni limpiarse sin autorización explícita.

#### Hallazgos abiertos de la rectificación

1. `ControlWriteSerializer` no valida `control_generico_valor_id`: un ID inexistente llega a la FK de PostgreSQL y devuelve HTTP 500. Debe validarse como catálogo existente y activo antes de llamar al servicio; no se corrigió todavía.
2. `ControlListCreateView` devuelve una lista sin paginación, mientras Causas usa la paginación global. El cambio mínimo es aplicar `ContractPaginationMixin` a Controles y usar `paginated_response`.
3. No existe endpoint para desvincular una tripleta Riesgo–Causa–Control ni consultas inversas de riesgos de una causa, causas de un control o riesgos de un control.
4. El endpoint de evaluación consulta `Control` por su FK histórica `riesgo_id`. Una asociación nueva de ese mismo control a otro riesgo mediante la tabla puente recibe 404 aunque la relación sea válida. El endpoint debe resolver la relación puente sin retirar la FK histórica.
5. Causas, Controles y Evaluación exigen `IsAuthenticated`, pero el recálculo residual y los endpoints preexistentes de Riesgo no lo exigen. Ninguna ruta aplica aún perfiles, claims o alcance por proceso.
6. No había `Usuario` EMMA activo en DEV durante la prueba. Con un `request.user` autenticado sin correspondencia local, las operaciones se ejecutan pero no generan auditoría; la evidencia de auditoría positiva queda bloqueada por la integración/semilla de identidad.
7. El filtro `estado = Activo` sigue codificado en `residual.py` y en el histórico de valoración. Las reglas posteriores piden no introducirlo si no reproduce EMMA original; se debe decidir con evidencia funcional antes de modificarlo.

### Correcciones técnicas Fase 4 autorizadas (2026-10-26)

- `control_generico_valor_id` se valida ahora como valor existente, activo y perteneciente a `CONTROL_GENERICO`; los valores inválidos producen HTTP 400 antes de alcanzar la FK de PostgreSQL. El campo es opcional según el modelo vigente, por lo que `null` permanece permitido.
- El listado de Controles reutiliza `ContractPaginationMixin` y devuelve el contrato estándar `{count, next, previous, results}`.
- Se agregó `DELETE /api/v1/riesgos/{riesgo_id}/causas/{causa_id}/controles/{control_id}/`, que retira exclusivamente la asociación de `riesgo_causa_control` y conserva entidades y demás relaciones.
- Se agregaron consultas puente: `GET /causas/{causa_id}/riesgos/`, `GET /controles/{control_id}/causas/` y `GET /controles/{control_id}/riesgos/` bajo el prefijo `/api/v1/riesgos/`.
- La evaluación valida Riesgo y Control de forma separada y reconoce tanto la asociación nueva por `riesgo_causa_control` como la FK histórica temporal para controles históricos sin causa determinada. Al recalcular, usa el Riesgo solicitado, no necesariamente el `riesgo_id` histórico del Control.
- El recálculo residual exige ahora `IsAuthenticated`. No se implementaron aún perfiles ni alcance por proceso.
- Se configuró `DB_TEST_NAME` con valor por defecto `test_emma_fase4_db` para pruebas. Esta base aislada fue creada con todas las migraciones, incluida `riesgos.0005`; `test_emma_db` no fue alterada.
- La batería específica de Fase 4 pasó 10/10 pruebas. La regresión completa de Riesgos ejecutó 37 pruebas: 36 correctas y una falla preexistente del motor inherente (`test_probabilidad_inherente_toma_el_mayor_de_tres_componentes`, esperaba 1 y obtiene 3). No se cambió esa fórmula por estar fuera del alcance.

### Corrección aprobada del motor inherente (2026-10-26)

La fuente definitiva es `Tarea 3. Reglas_Motores_Riesgo_EMMA_Reglas_Confirmadas.xlsx`; el Streamlit histórico no prevalece sobre ella.

- La probabilidad histórica ahora aplica literalmente los intervalos estrictos aprobados: `>15 % → 5`, `>10 % y <15 % → 4`, `>5 % y <10 % → 3`, `>1 % y <5 % → 2`; cualquier otro valor, incluidas las fronteras exactas 1 %, 5 %, 10 % y 15 %, devuelve nivel 1.
- La probabilidad inherente final es `max(cualitativa, ocurrencia, histórica)`. Se retiró la prioridad técnica anterior que retornaba el primer valor verdadero.
- La prueba de regresión que fallaba se corrigió con los componentes que realmente producen sus datos: cualitativa 3, ocurrencia 2, histórica 5 y final 5. Se agregaron fronteras históricas, intervalos internos y escenarios donde cada componente —o sus empates— determina el máximo.
- Se agregó cobertura de endpoint de valoración, creación y edición de Riesgo con valoración, severidad inherente y propagación de la probabilidad corregida al residual.
- `REDONDEAR` de Excel y `round()` de Python difieren para `.5`, pero el promedio de tres niveles enteros nunca produce `.5`; no se modificó el redondeo.
- Se ejecutaron 40/40 pruebas de `backend.apps.riesgos` correctamente en `test_emma_fase4_db`, preservada y separada de DEV. No se recalcularon ni sobrescribieron datos o valoraciones históricas de DEV.

### Corrección frontend Riesgos: consulta, detalle, creación y edición (2026-10-26)

- La búsqueda general ya no promete código GR. El placeholder enumera solo los campos que el backend soporta mediante `search`; el código conserva su filtro específico `codigo_riesgo`.
- Se incorporó un indicador de carga reutilizable para HTMX en listado, filtros, búsqueda y creación. Los enlaces a detalle y los formularios de edición/inactivación activan el mismo indicador durante navegación o envío normal.
- El detalle presenta, con los datos del contrato existente: valoración inherente y residual separadas; estructura de procesos; tablas de causas y controles; e historial de valoraciones. No calcula fórmulas en frontend.
- La paginación interpreta correctamente el enlace anterior de DRF aunque omita `page=1`.
- Los errores de API en edición e inactivación se muestran como alerta de usuario, además de los errores de campo cuando existen. Los errores HTMX del listado sobreviven al reemplazo de la tabla.
- La creación conserva que GR no es editable ni generado por frontend; el backend lo asigna y el frontend muestra el código devuelto. El formulario actual no incluye valoración: el contrato exige entradas configuradas de probabilidad e impacto, pero no existe endpoint frontend-consumible para listar esas configuraciones. No se agregaron campos de texto libre ni catálogos inventados.
- La gestión de asociaciones y evaluación de controles no se agregó a la edición de Riesgo. La definición aprobada de Fase 4 las ubicó en backend; no existe una decisión funcional que las ubique en este formulario. Además, los endpoints puente requieren autenticación que permanece pendiente de integración Entra.
- Eventos y Planes no forman parte del contrato de detalle de Riesgo actual; se mantienen como trabajo de módulos/fases correspondientes.
- Pruebas frontend: 12/12 correctas. Pruebas reales DEV cubrieron filtros de riesgo homologado, vicepresidencia, proceso, subproceso, dueño y combinación; limpieza y vacío; paginación de dos páginas; detalle de relaciones; creación GR; edición e inactivación.
- Datos técnicos DEV conservados e identificables: `R-AUD-FILTRO-F4-20261026`, el Proceso `AUDITORIA_FRONTEND_F4_*` y `R-AUD-PAG-F4-20261026-01` a `-21`. Un riesgo técnico previo `GR2` fue creado desde el frontend; se inactivó `R-AUD-PAG-F4-20261026-01` para validar el flujo.

### Cierre técnico frontend Riesgos en DEV (2026-10-26)

- Se expuso `GET /api/v1/riesgos/configuracion-valoracion/`. El contrato devuelve exclusivamente opciones activas y versión para exposición, complejidad, condiciones de entorno, ocurrencia e impactos; no expone fórmulas. El frontend construye los selects desde este contrato y remite las entradas al backend en `valoracion`.
- La creación y edición no calculan probabilidad, impacto ni severidad en JavaScript. El código GR tampoco se recibe ni se calcula en frontend: el backend lo asigna al crear y se presenta en la respuesta.
- La edición precarga la última `datos_entrada` del historial de valoración; al guardar, envía un `PATCH` y el backend persiste una nueva fotografía de valoración. Los niveles y la severidad continúan siendo solo resultados de backend.
- El detalle usa las asociaciones nuevas: Causas se obtienen mediante `riesgo_causa`; Controles mediante `riesgo_causa_control`, deduplicados por `control_id`. La FK histórica se conserva como compatibilidad temporal.
- En DEV se verificó el Riesgo técnico `GR7`: creación por la ruta HTMX, GR automático, persistencia de la valoración inicial (`3/1/Bajo`), edición de ocurrencia, `PATCH` exitoso y nueva valoración persistida (`5/1/Moderado`).
- En los detalles de los Riesgos técnicos `GR1` y `GR3` se verificó una Causa reutilizada visible en ambos y un Control reutilizado visible una sola vez aun cuando estaba asociado a dos Causas del mismo Riesgo.
- Se ajustó el timeout del cliente frontend DEV de 10 a 30 segundos. El valor anterior podía informar timeout aunque el backend hubiese completado el alta; el flujo HTMX fue validado con el valor nuevo.
- La precarga de asociaciones puente se aplica solo al selector de detalle, no al listado. Así se preserva el límite de consultas del listado y se evita trabajo adicional de paginación.
- Pruebas frontend tras esta corrección: 13/13 correctas. La base de pruebas de backend permanece separada en `test_emma_fase4_db`; `test_emma_db` no se eliminó ni modificó.
- Regresión final backend: `backend.apps.riesgos` ejecutó 42/42 pruebas correctas en `test_emma_fase4_db` (`456.730 s`). La única desviación detectada durante la primera pasada era una precarga puente innecesaria en el listado; se restringió al selector de detalle y la pasada final quedó verde.
- Pendientes no bloqueantes para producción: integración Entra, claims, perfiles y alcance por proceso. Pendientes de tarea/definición posterior: gestión visual de asociaciones y evaluación de controles, Eventos y Planes de Acción.

# Preguntas abiertas

## Autenticación Entra para API EMMA — dependencia de infraestructura (2026-10-26)

- El login actual del frontend usa MSAL y reenvía al backend el `access_token` de la sesión. La configuración vigente solicita únicamente `User.Read`, que corresponde a Microsoft Graph.
- No existe en el repositorio evidencia verificable de una App Registration separada para la API EMMA, Application ID URI, scope delegado propio ni configuración backend para validar Bearer/OIDC.
- Por seguridad, un token con audiencia Graph no se acepta ni se debe aceptar como token de la API EMMA. `IsAuthenticated` se conserva sin bypasses.
- Infraestructura/Entra debe identificar o crear la App Registration de API, definir su Application ID URI, exponer un scope delegado (por ejemplo conceptual `access_as_user`), concederlo al cliente frontend y publicar el consentimiento necesario en DEV.
- El frontend deberá recibir el scope de API únicamente mediante `ENTRA_SCOPE` de entorno; no se deben hardcodear identificadores ni scopes en código. El token resultante debe tener audiencia de API EMMA, issuer y tenant esperados, vigencia válida y el scope delegado de EMMA.
- Con esa configuración, la fase posterior de backend podrá implementar validación OIDC/JWKS de firma, issuer, tenant, audiencia, algoritmo, expiración y `nbf`; un token Graph deberá seguir siendo rechazado.
- Esto bloquea únicamente el E2E autenticado real de Causas y Controles. No es un defecto funcional de sus pantallas ni habilita todavía roles, perfiles, claims funcionales, alcance por proceso o mapeo de auditoría a `Usuario` EMMA.

## Cierre técnico frontend Causas y Controles — contrato y pruebas (2026-10-26)

- El frontend usa exclusivamente las rutas ya publicadas de Causas, Controles, asociaciones y evaluación. No se modificó backend, modelos, migraciones, FKs históricas, autenticación, Entra ni autorización.
- Causas: listado con búsqueda/paginación/estado vacío/loading, creación, edición, detalle, Riesgos asociados por contrato, asociación y retiro de relación con confirmación explícita de que no elimina la entidad.
- Controles: listado con búsqueda/paginación/estado vacío/loading, creación, edición, selector de `CONTROL_GENERICO` alimentado por catálogo API, detalle de asociaciones y resultados de evaluación, y acciones de relación desde el detalle de Riesgo donde se conoce la tripleta real.
- La evaluación solo envía D1–D4/O1–O5 y muestra el resultado backend. No hay fórmulas locales de Diseño, Operatividad, VPR, Efectividad ni residual. Cuando la respuesta contiene `residual`, se informa la actualización.
- La suite frontend de Riesgos ejecutó 22/22 pruebas correctas, incluidas cobertura de formularios, listados, errores API, reutilización visual de Causa, retiro de relación, catálogo de Control Genérico y respuesta residual.
- El E2E visual autenticado permanece como `BLOQUEO EXTERNO DE AUTENTICACIÓN`: el frontend obtiene token Entra para Microsoft Graph (`User.Read`) y el backend protegido no puede aceptarlo como token de API EMMA sin la configuración de scope/audience de infraestructura. Este bloqueo no implica relajar `IsAuthenticated` ni cambiar el frontend funcional.

## Históricos de Matriz — diseño aprobado pendiente de migración (2026-10-26)

- Se mantiene la separación: `Auditoria` registra trazabilidad operativa; los nuevos históricos funcionales no la sustituyen ni dependen de que exista Usuario EMMA.
- Se mantienen sin cambio `ValoracionRiesgo` y `ValoracionRiesgoControl`, que ya constituyen histórico funcional de valoración.
- Se aprueban conceptualmente tres históricos append-only: `ControlEvaluacionHistorico`, `HistorialRiesgoCausa` y `HistorialRiesgoCausaControl`. Los tres incorporarán `origen_registro` con valores conceptuales `OPERACION` y `BACKFILL`.
- `HistorialRiesgoCausa` y `HistorialRiesgoCausaControl` registrarán eventos funcionales `ASSOCIATE` y `DISASSOCIATE`; no se actualizará una fecha de fin en un registro histórico existente.
- La evaluación vigente es global al `Control`: las respuestas D1–D4/O1–O5 y resultados se guardan en `Control`, y el servicio de evaluación no recibe Riesgo ni Causa. El `riesgo_id` del endpoint valida asociación y define el Riesgo al que se recalcula residual. Por tanto, el histórico de evaluación se versiona por `control_id` y no requiere `riesgo_id`, `causa_id` ni `riesgo_causa_id` como contexto funcional.
- Las operaciones vigentes e históricas deberán ser transaccionales. La creación/retiro de asociación y su evento histórico se harán en la misma transacción; la evaluación actualizará Control, insertará snapshot y recalculará residual en la misma unidad atómica cuando corresponda.
- La generación de versiones no usará `MAX(version)+1` sin protección: se propone bloqueo de fila del Control para evaluaciones y bloqueo asesorado PostgreSQL por clave compuesta para asociaciones, dentro de transacciones.
- Backfill aprobado conceptualmente pero no ejecutado: baseline de los 2 Controles evaluados, 5 relaciones Riesgo–Causa y 5 relaciones Riesgo–Causa–Control vigentes en DEV, identificando `origen_registro=BACKFILL`. Su fecha será de incorporación al histórico, no fecha funcional original.
- Se recomienda evaluar después un trigger PostgreSQL `BEFORE UPDATE OR DELETE` para impedir mutación de históricos. No se crea todavía.

## Históricos de Matriz — implementación backend DEV (2026-10-26)

- Se aplicaron en PostgreSQL DEV las migraciones `riesgos.0006_historicos_matriz` y `riesgos.0007_backfill_historicos_matriz`. No se modificaron las tablas vigentes de Riesgo, Causa, Control, relaciones puente, ValoracionRiesgo, ValoracionRiesgoControl ni Auditoria.
- `0006` crea las tablas append-only `control_evaluacion_historico`, `historial_riesgo_causa` e `historial_riesgo_causa_control`, con FK `PROTECT`, usuario nullable, restricciones de versión por contexto e índices de consulta por entidad/contexto y fecha.
- `0007` incorporó el baseline técnico de DEV: 2 evaluaciones vigentes, 5 relaciones Riesgo–Causa y 5 relaciones Riesgo–Causa–Control. Todos llevan `origen_registro=BACKFILL`, usuario `NULL`; su fecha es fecha de incorporación al histórico, no una fecha funcional original inferida.
- Las nuevas operaciones llevan `origen_registro=OPERACION`. Las asociaciones y retiros de Causa y Control insertan su evento histórico en la misma transacción que la modificación de la tabla puente. Si la inserción histórica falla, la relación vigente revierte.
- Cada evaluación admitida bloquea el Control, actualiza su estado vigente, crea un snapshot completo y conserva las versiones anteriores. La evaluación sigue siendo global al Control. La versión se obtiene dentro de la transacción después del bloqueo de la entidad/contexto; las restricciones `UNIQUE` son una segunda defensa frente a colisiones.
- Se habilitaron solo consultas autenticadas: `GET /api/v1/riesgos/controles/{control_id}/evaluaciones-historicas/`, `GET /api/v1/riesgos/{riesgo_id}/causas/{causa_id}/historial-asociacion/` y `GET /api/v1/riesgos/{riesgo_id}/causas/{causa_id}/controles/{control_id}/historial-asociacion/`. Sus resultados se ordenan de versión más reciente a más antigua. No hay endpoints de escritura para históricos.
- Auditoría continúa siendo independiente: puede no existir cuando no se resuelve `Usuario` EMMA, pero eso no impide el histórico funcional porque `usuario_id` es nullable.
- No se implementó trigger PostgreSQL de inmutabilidad. Por ahora la protección append-only es de aplicación: sin rutas de actualización/eliminación, servicios de inserción, transacciones, FK `PROTECT`, restricciones e integración de pruebas. El trigger queda como endurecimiento posterior para bloquear también cambios SQL directos.
- Deuda técnica independiente: cuando un Control reutilizado se evalúa desde Riesgo A, la evaluación global se persiste una sola vez y el flujo actual recalcula automáticamente solo el residual de Riesgo A. No se cambió la semántica residual ni se convirtió la evaluación en contextual.
- Verificación técnica: `manage.py check` finaliza sin incidencias. La regresión de `backend.apps.riesgos` ejecutó 47/47 pruebas correctas en `test_emma_fase4_db`; el caso adicional posterior de historial vacío y método de escritura rechazado ejecutó 1/1 correctamente. La base de pruebas sigue aislada de DEV.

### Ajuste de garantías de Históricos de Matriz (2026-10-28)

- `0006_historicos_matriz` explicita índices independientes para fecha, pareja Riesgo–Causa y tripleta Riesgo–Causa–Control, además de los índices individuales de las entidades. Los tres FKs funcionales y el FK de usuario permanecen `PROTECT`; `usuario_id` es nullable.
- Los valores admitidos se acotan en el modelo: origen `OPERACION` o `BACKFILL`, y evento `ASSOCIATE` o `DISASSOCIATE`. No se agregan rutas de modificación o borrado de históricos.
- Para asignar una versión se bloquea el contexto funcional en orden estable: Riesgo, Causa, Control (si aplica), y luego la relación vigente. La evaluación bloquea el Control. La versión se consulta e inserta dentro de esa transacción; el `UNIQUE` continúa como defensa adicional y una colisión provoca rollback.
- La cobertura transaccional fuerza errores de escritura histórica para asociación y retiro de Causa, asociación y retiro de Control, y evaluación. En todos los casos la tabla vigente conserva su estado anterior.
- La fecha de `0007_backfill_historicos_matriz` continúa siendo únicamente la incorporación técnica al histórico; no afirma la fecha original de la operación de negocio.

### API y permisos técnicos de Matriz (2026-10-28)

- Las views de Riesgo para listado/alta, detalle/edición, inactivación, valoraciones y cálculo de valoración, así como listado y detalle de Auditoría, requieren explícitamente `IsAuthenticated`. El recálculo residual, Causas, Controles, asociaciones, evaluación e históricos ya conservaban esa protección.
- La respuesta para solicitudes no autenticadas sigue el mecanismo DRF configurado actualmente (HTTP 403 en las pruebas). No se alteraron `authentication_classes`, Entra, Bearer/OIDC ni contratos.
- Históricos y Auditoría son únicamente de lectura: escrituras no soportadas retornan HTTP 405. Los errores funcionales previsibles (payload, catálogo, duplicado, inexistente) permanecen en 4xx conforme al manejador y contrato actual; errores inducidos de persistencia solo se usan para probar rollback.
- Catálogos de solo lectura conservan acceso actual sin permiso explícito. **POLÍTICA DE ACCESO PENDIENTE DE DEFINICIÓN FUNCIONAL**.
- `IsAuthenticated` es autenticación técnica, no autorización funcional. **AUTORIZACIÓN POR ROL** y **ALCANCE POR PROCESO** permanecen pendientes de definición funcional; futuras políticas deberán poder diferenciar consulta, creación, edición, inactivación, asociación, retiro, evaluación e historial, sin inventar roles en esta fase.
- El E2E navegador autenticado continúa bloqueado externamente: el scope actual `User.Read` emite token para Microsoft Graph, no para la audiencia de la API EMMA.

1. ¿Cuáles campos son obligatorios para guardar un riesgo nuevo y cuáles son obligatorios solo para activarlo?

2. ¿La creación debe permitir únicamente Activo o existe un estado inicial distinto aprobado?

3. ¿Se aprobará Borrador? Si sí, ¿cuáles son sus transiciones y restricciones?

4. ¿Se permitirá reactivar un riesgo Inactivo? ¿Quién puede hacerlo?

5. ¿Qué excepciones, si existen, permiten editar un riesgo Inactivo?

6. ¿Causas y controles son obligatorios al crear, al activar o en ningún momento?

7. ¿Qué relación exacta debe existir entre causas, controles y riesgos, especialmente si una causa o control puede reutilizarse?

8. ¿Cuáles campos deben ser catálogos, cuáles texto libre y cuál es el endpoint/fuente oficial para cada catálogo?

9. ¿El detalle debe incorporar eventos, planes e historial de modificaciones en esta tarea? Si sí, ¿qué datos mínimos debe devolver cada bloque?

10. ¿Qué fuente técnica implementará roles: App Roles, claims, grupos Entra o perfiles internos?

11. ¿Cómo se asignarán procesos a usuarios y cómo se resuelven usuarios con varios perfiles?

12. ¿Cuál es el alcance de consulta definitivo del Dueño de Proceso cuando las fuentes distinguen consulta y edición?

13. ¿La regla literal de fronteras históricas del Excel debe mantenerse o negocio quiere normalizar los límites?

14. ¿El nivel residual puede bajar de 1 según la fórmula fuente o se debe imponer un mínimo? Si se impone, ¿con qué aprobación?

15. ¿Cuál es el comportamiento aprobado para redondeos .5 de la probabilidad cualitativa?

16. ¿Qué ambiente PostgreSQL de integración, datos semilla y acceso se usarán para las pruebas end-to-end?

