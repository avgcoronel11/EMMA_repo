# Pendientes de pruebas de integración con Azure PostgreSQL

**Estado:** bloqueo técnico de conectividad, no pendiente funcional.

## Diagnóstico confirmado

Desde el entorno de desarrollo, el nombre de Azure PostgreSQL resuelve a una
dirección IP, pero la conexión TLS a `emmaservidor.postgres.database.azure.com`
por el puerto `5432` expira. La prueba directa con `psycopg2` y
`connect_timeout=10` devuelve:

```text
connection to server at "emmaservidor.postgres.database.azure.com" (52.162.201.0),
port 5432 failed: timeout expired
```

No se han modificado datos de producción durante estos intentos.

## Pruebas pendientes por ejecutar en PostgreSQL aislado

1. Ejecutar la suite de integración de Riesgos usando `test_emma_db`.
2. Consultar y validar los registros vigentes de `CFG_PROBABILIDAD`,
   `CFG_NIVEL_IMPACTO` y `CFG_SEVERIDAD`.
3. Verificar que los motores consulten los catálogos reales y persistan los
   resultados inherentes y residuales esperados.
4. Validar la generación concurrente y persistencia del código `GR<n>`.
5. Validar creación, futura edición parcial e inactivación de Riesgos contra
   una base de pruebas sin afectar producción.
6. Validar errores de catálogo, severidad inexistente, transacciones y
   rollback de persistencia.
7. Cuando se implemente el histórico de valoraciones, validar que una
   inactivación posterior de un control no cambie una valoración previamente
   guardada.

## Pruebas que sí se ejecutaron localmente

- Pruebas unitarias puras del motor de Riesgos: 7 correctas, sin usar base de
  datos.
- Pruebas del frontend de Riesgos: 4 correctas, sin usar base de datos.
- Verificación de configuración Django: sin incidencias.

## Acción técnica necesaria

Habilitar conectividad saliente desde este entorno al servidor Azure PostgreSQL
por el puerto `5432`, incluyendo las reglas de firewall o red privada que
correspondan; alternativamente, facilitar una instancia PostgreSQL aislada y
accesible para pruebas. Una vez disponible, se deben ejecutar las pruebas
pendientes y registrar sus resultados reales antes de declararlas aprobadas.
