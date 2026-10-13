# backend/audit/BACK-DB-MIGRATIONS-AUDIT-001

## Objetivo

Consolidar las reglas de Alembic que han quedado validadas en el punto 2 y separar las propuestas de puntos posteriores.

## Responsabilidad del documento

Recoge reglas de migraciones y su acceso a base de datos. No duplica la selección de entornos de Makefile ni el empaquetado Docker.

## Estado actual

**VALIDADO PARCIALMENTE — punto 2 completado.** La fase continúa por los puntos pendientes.

## Cambios realizados

Se elevan a reglas validadas la configuración central explícita de base de datos, la ausencia de fallback de plantilla o ini para Alembic y la guarda histórica de downgrade ante datos dependientes.

## Justificacion tecnica

Una única fuente de conexión evita que una migración opere contra una base distinta de la seleccionada. La precondición previa a borrados hace explícito el riesgo sobre datos operativos.

## Decisiones tomadas

### Reglas validadas

- Alembic recibe `DATABASE_URL` desde la configuración central explícita.
- Alembic no usa un fallback de configuración en `alembic.ini` ni en una plantilla de entorno.
- Un downgrade histórico con borrados comprueba antes los datos dependientes y rechaza la operación si existen.

### Propuestas pendientes

- **Punto 3:** mantener las migraciones estructurales sin DML y definir el baseline estructural futuro. Esta propuesta no implica reescribir las migraciones existentes.
- Validar el ciclo de vida completo de baseline y Docker.

## Tests ejecutados

Las reglas validadas disponen de evidencia de la validación completa del punto 2, registrada en el histórico del área. No se duplican aquí resultados.

## Riesgos o deuda tecnica

La propuesta de punto 3 y la validación de ciclo de vida siguen pendientes. Las futuras revisiones deben mantener el guardado operativo antes de eliminar datos dependientes.

## Relacion con el backend

Estas reglas protegen la evolución de la persistencia del backend y evitan que Alembic seleccione una conexión no prevista.
