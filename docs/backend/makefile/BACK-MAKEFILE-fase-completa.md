# backend/audit/BACK-DB-MIGRATIONS-AUDIT-001

## Objetivo

Registrar la evidencia del punto 2 sobre la selección de configuración, los targets de base de datos y sus guardas operativas.

## Responsabilidad del documento

Este histórico es la fuente de detalle de configuración de la fase. No reproduce el grafo Alembic ni el contexto de construcción Docker.

## Estado actual

**EN CURSO — punto 2 aprobado y completado.** Quedan puntos posteriores de la fase; no se declara la implementación global como terminada.

## Cambios realizados

- Los targets Makefile seleccionan `ENV_FILE` de forma explícita y usan `.env` como fichero local.
- `backend-test-db` exige `TEST_DATABASE_URL`, verifica que corresponde a una base de pruebas mediante el sufijo `test` y exporta el entorno de pruebas; no admite fallback.
- Los downgrades están limitados a los entornos `development` y `test`, además de respetar la guarda de migración para datos dependientes.
- El script de seeds incorpora una guarda de entorno.
- Se actualizaron ayuda y preflight para reflejar las precondiciones operativas.
- CI emplea un `.env.ci` efímero; no utiliza el fichero de ejemplo.

## Justificacion tecnica

La selección explícita elimina ambigüedad entre configuración local, pruebas y CI. La base de pruebas obligatoria y las guardas de downgrade y seeds previenen operaciones destructivas o de carga sobre un entorno no autorizado.

El `.env` local está ignorado por Git. El fichero de ejemplo es una plantilla no operativa y no aporta fallback; `APP_ENV` no contiene valores en esta documentación. Se validó la matriz de seguridad de `APP_ENV` para `development`, `test`, `staging` y `production`.

## Decisiones tomadas

- Requerir `ENV_FILE` explícito en la interfaz Makefile y evitar cualquier fallback a plantillas.
- Reservar `TEST_DATABASE_URL` para operaciones de prueba y comprobar su destino antes de usarlo.
- Permitir downgrade solo en `development` y `test`, sujeto a la guarda de datos de la migración.
- Mantener las guardas de seeds y los checks previos como parte de la interfaz operativa.
- Dejar el target de bootstrap futuro para el punto 4; no se declara implantado en este punto.

## Tests ejecutados

- Calidad: **OK**.
- Unitarios: **433** pruebas.
- Base de datos: **53** pruebas.
- Seguridad: **22** pruebas.
- Validación completa: **508** pruebas.

## Riesgos o deuda tecnica

- El target futuro de bootstrap queda propuesto para el punto 4.
- El ciclo de vida completo de baseline y la tarea Docker de migraciones requieren puntos posteriores.

## Relacion con el backend

Los comandos operativos del backend seleccionan explícitamente su configuración y reducen el riesgo de ejecutar pruebas, downgrades o seeds contra una base no permitida.
