# backend/audit/BACK-DB-MIGRATIONS-AUDIT-001

## Objetivo

Registrar la evolución Docker del punto 5 sin declarar cerrado el trabajo global.

## Responsabilidad del documento

Este histórico trata Compose, imagen y red. No duplica el grafo Alembic ni las guardas del Makefile.

## Estado actual

**Punto 5 documentado.** Las referencias históricas a la ausencia de un migrador Docker quedan sustituidas por el contrato actual.

## Cambios realizados

- Se mantiene el contexto de construcción reducido y la allowlist de variables de entorno.
- Se añadió el perfil explícito `migration`, que usa el mismo artefacto de imagen no root que backend, pero con comando y credenciales de migración independientes.
- `docker-compose.yml` conserva `backend_internal` con `internal: true` y el stack base publica solo Nginx; PostgreSQL, backend y frontend no se exponen al host.
- `docker-compose.local.yml` se requiere solo para desarrollo local y CI: publica PostgreSQL, backend y frontend, y cambia `backend_internal` a `internal: false` para permitir clientes del host, como pgAdmin.
- Init crea roles en volúmenes nuevos y el provisionamiento explícito cubre los volúmenes existentes.

## Justificacion tecnica

Separar migración y ejecución elimina la migración implícita del arranque, conserva un único artefacto construible y limita la exposición de red y privilegios. El override hace explícita la excepción local de conectividad, sin trasladarla a staging.

## Decisiones tomadas

- `docker-deploy` es el despliegue canónico: primero migración y después stack base.
- `docker-up` queda reservado al arranque manual local, usa el override y no ejecuta migraciones; `docker-deploy` usa solo el compose base de staging, que permanece aislado.
- Para pgAdmin local: host `localhost`, puerto `POSTGRES_PORT`, base `POSTGRES_DB`, usuario `POSTGRES_USER` y contraseña `POSTGRES_PASSWORD`.
- Se prohíbe downgrade a través de Docker.
- El migrador requiere `MIGRATION_DATABASE_URL`, `MIGRATION_ALLOWED_HOSTS`, `MIGRATION_ALLOWED_DATABASES` y `MIGRATION_EXPECTED_DB_USER`; los secretos no aparecen en documentación ni logs.
- Health y readiness se validan con base de datos lista y revisión `head`.

## Tests ejecutados

- Renderizado Compose válido, provisionamiento de roles y baseline aplicado.
- Migración repetida en estado `already_at_head`; comprobaciones `current` y `check` correctas.
- Health y readiness devolvieron HTTP 200 dentro del backend.
- Tests de migraciones disponibles: **21 passed**; mypy correcto. No hay un resultado actual completo de toda la suite.

## Riesgos o deuda tecnica

El override publica servicios para desarrollo y CI y, por tanto, no debe emplearse en staging. Los clientes del host, incluido pgAdmin, requieren el flujo local con override.

## Relacion con el backend

El empaquetado permite ejecutar el backend y el migrador con el mismo artefacto, manteniendo la separación de roles y el mínimo privilegio.
