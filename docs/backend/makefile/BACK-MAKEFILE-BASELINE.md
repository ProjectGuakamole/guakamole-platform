# backend/audit/BACK-DB-MIGRATIONS-AUDIT-001

## Objetivo

Preparar el baseline del área Makefile para las reglas de targets, selección de configuración, orquestación, ayuda y guardas de comandos de la fase coordinada `BACK-DB-MIGRATIONS-AUDIT-001`.

## Responsabilidad del documento

Recoger únicamente las reglas de la interfaz Makefile relacionada con migraciones y bootstrap. Las decisiones y evidencias se conservan en el histórico del área. Las reglas estructurales Alembic y las de ejecución Docker no se duplican aquí.

## Estado actual

**BORRADOR NO VALIDADO.** No certifica los targets actuales ni su seguridad. Esta intervención no modifica comandos y no autoriza reanudar el punto 2.

## Cambios realizados

Se crea este borrador con alcance, organización y orientaciones iniciales. No se edita el Makefile, no se ejecutan targets y no se implanta una nueva selección de configuración.

## Justificacion tecnica

La interfaz de comandos debe ser comprensible y conservar compatibilidad cuando se revisa la ejecución de migraciones. La ayuda y las guardas deben corresponder al comportamiento real; su mera mención documental no demuestra esa correspondencia.

## Decisiones tomadas

### Organización acordada del área

- Las reglas de targets, selección de configuración, orquestación, ayuda y guardas se mantienen en `docs/backend/makefile/`.
- El histórico se denomina `BACK-MAKEFILE-fase-completa.md` y el baseline `BACK-MAKEFILE-BASELINE.md`.
- No incorporar aquí el proceso común, la tabla de reparto ni copias de evidencia de otras áreas.

### Orientación aprobada: propuesta pendiente de implantación y validación

- Preservar los targets existentes y `db-bootstrap` al revisar la interfaz operativa; no retirar ni renombrar comandos sin una decisión explícita revisada.
- Mantener una ayuda que explique el propósito y los parámetros de los comandos y sea coherente con su comportamiento efectivo.
- Seleccionar configuración de forma explícita y segura, sin documentar secretos ni asumir cambios de entorno ya implantados.
- Revisar las guardas de comandos para detectar selección ausente, inválida o ambigua antes de ejecutar operaciones, con criterios concretos pendientes de revisión.
- Mantener en Makefile la responsabilidad de invocación y orquestación, sin duplicar la lógica de migraciones ni la configuración propia del contenedor.

Estas orientaciones no acreditan compatibilidad ni guardas ya verificadas. No se afirma que `APP_ENV` ni una transición entre configuraciones de entorno estén implantados; nombres, valores y mecanismos concretos siguen pendientes de revisión autorizada.

## Condición de actualización

Incorporar reglas definitivas solo tras revisión de `api-architect` y QA, evidencia aplicable a Makefile y revisión de exactitud documental por el arquitecto. El histórico conserva decisiones y tests; el baseline conserva reglas, sin duplicar resultados. Mantener **BORRADOR NO VALIDADO** hasta completar esa revisión.

## Tests ejecutados

No se han ejecutado targets ni tests Makefile en esta intervención. No existe nueva evidencia para validar ayuda, compatibilidad, selección de configuración o guardas.

## Riesgos o deuda tecnica

El borrador no demuestra que los comandos existentes cumplan estas orientaciones. Convertirlas en reglas definitivas sin comprobarlas podría ocultar diferencias entre ayuda, configuración y ejecución efectiva.

## Relacion con el backend

El baseline prepara criterios para la interfaz de operación de migraciones y bootstrap. No modifica el backend, su configuración ni sus mecanismos de ejecución.
