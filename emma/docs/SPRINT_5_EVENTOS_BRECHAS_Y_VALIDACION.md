# Sprint 5 — Eventos de Riesgo: brechas y validación backend

## Alcance contrastado

Documento elaborado a partir de `EMMA_Reglas_Backend_Eventos_Validacion.xlsx`
y del modelo industrializado existente. La fuente de verdad de las relaciones
implementadas es PostgreSQL; este documento no propone tablas, campos ni
catálogos paralelos.

## Reglas implementadas en esta entrega

- **EV-01, EV-02 y RC-01/03:** `id_ocurrencia`, usuario y fecha/hora de
  registro se generan en backend. El identificador usa UUID y conserva la
  restricción única de PostgreSQL; no se acepta su modificación por payload.
- **EV-03 a EV-05 y RC-08/09:** se validan fechas y horas completas, el orden
  Inicio ≤ Descubrimiento ≤ Registro y Fin ≥ Inicio. El exceso de 15 días
  hábiles genera advertencia HTTP, no bloqueo.
- **EV-14, EV-15 y EV-18:** riesgo, riesgo genérico, dueño y snapshots de la
  estructura se resuelven desde el riesgo seleccionado y sus relaciones de
  proceso.
- **EV-16, EV-17, EV-20 a EV-23 y RC-12/13:** cuantía estimada/casos positivos;
  causa y control obligatorios, sin duplicados y pertenecientes al riesgo.
  Una causa libre requiere texto y no crea una causa maestra.
- **EV-24, EV-25, EV-38, EV-39 y RC-16 a RC-20:** validación de Tipo A/B/C,
  pérdida Tipo A, recuperación, total de recuperaciones y pérdida neta
  calculados en servidor.
- **RC-02 y RC-23:** creación/edición atómicas y auditoría antes/después para
  el evento. Los snapshots de causa, control y cuenta son obtenidos de los
  modelos maestros, no del cliente.
- **Formulario general/clasificación:** `evento_riesgo.nombre_evento` guarda
  el nombre independiente del evento y `evento_riesgo.tipo_recuperacion`
  conserva la multiselección `SEGUROS` / `DIFERENTE_DE_SEGUROS`. La migración
  `eventos.0002_eventoriesgo_nombre_evento_and_more` fue aplicada en Azure.
- **EV-06 a EV-08:** el catálogo histórico geográfico se separó mediante
  migración reversible en `PAIS`, `DEPARTAMENTO` y `CIUDAD`. El backend exige
  una ruta padre-hijo válida y copia sus descripciones a los snapshots del
  evento.
- **EV-09, EV-10, EV-27 a EV-37:** las selecciones se persisten usando
  `EntidadCaracteristica.valor_catalogo_id`. Se validan producto y canal
  principales, segmentos, clases/tipologías, líneas y clasificación
  operacional jerárquica. Los sitios de ocurrencia y detección son
  independientes y reciben tipo (`OFICINA` o `DIRECCION_GENERAL`) e ID.
  Producto/canal adicional solo se admite mediante el valor `OTRO` y
  `valor_libre`.

## Brechas que no se implementaron por falta de contrato persistente

| Reglas | Brecha observada | Insumo requerido para implementarla sin inventar reglas |
|---|---|---|
| EV-06 a EV-10; QA-13 a QA-18 | Implementadas las rutas geográficas y los sitios independientes. | Ampliar pruebas negativas y de edición histórica contra Azure. |
| EV-11 a EV-13; QA-19 a QA-22 | El evento solo conserva snapshots organizacionales; no tiene FK a VP/proceso/subproceso ni campos de selección para validar una ruta enviada. | Definir si el evento debe referenciar `CatProceso` o entregar los IDs de ruta en el contrato. |
| EV-27 a EV-37; QA-32 a QA-35 | Producto, canal, segmento, tipología y clasificaciones N1–N3 no están representados como campos ni relaciones diferenciables en Eventos. `EntidadCaracteristica` es genérica, pero no permite identificar la semántica funcional sin códigos de catálogo aprobados. | Mapeo oficial campo → código de `Catalogo` y jerarquías `parent_valor`; contrato API para cada selección. |
| EV-40, EV-41; RC-04 a RC-07; QA-37 y QA-48 a QA-50 | `Usuario` no tiene perfil, rol, grupo ni claims persistidos. No existe matriz de permisos ejecutable para Tipo A, estados especiales o campo de cierre. | Fuente de autoridad de perfiles/claims, mapeo a usuarios y matriz acción–perfil aprobada. |
| EV-38, EV-39; QA-39 y QA-44 a QA-46 | Existe cuenta contable y relación de evento, pero no hay una clasificación persistente que distinga con certeza cuenta de pérdida, recuperación, auxiliar o tipo de recuperación. | Códigos/valores oficiales para `tipo_cuenta` y campos contables faltantes, sin depender de texto libre. |
| RC-21, RC-22; QA-53 y QA-54 | Existe `Adjunto` y endpoints CRUD para sus metadatos, pero no hay backend para recibir el binario ni integración con almacenamiento de objetos. | Configurar Azure Blob Storage para el backend: cuenta/endpoint, contenedor privado, identidad administrada o credencial como secreto de entorno, política de tamaño/retención y permisos de lectura/escritura. Luego implementar carga multipart, persistencia de metadatos en `adjunto`, descarga autorizada y compensación del blob si falla la transacción. No guardar binarios en PostgreSQL. |

## Pruebas pendientes contra PostgreSQL/Azure

Las pruebas de integración QA-01 a QA-55 deben ejecutarse sobre una base de
pruebas aislada y con conectividad real a Azure. No se deben ejecutar contra
datos productivos. La ejecución debe registrar los resultados de fechas,
relaciones, auditoría, concurrencia, recuperación y rollback.

## Criterio de cierre

Las brechas anteriores solo se cerrarán cuando exista el contrato de datos o
de autorización correspondiente. Implementar controles basados en nombres
libres, supuestos de roles o catálogos no identificados introduciría reglas de
negocio no aprobadas.
