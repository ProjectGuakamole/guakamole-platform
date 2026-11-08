# Phase 03 — Health y readiness
- goal: (baseline) liveness en /api/health y readiness en /api/ready, que solo está lista cuando PostgreSQL responde y Alembic está en la head empaquetada, sin filtrar detalles internos.

## 3.1 Contratos y comprobaciones de readiness
- layer: infrastructure
- ticket: BACK-HEALTH-001
- goal: los esquemas estables de health y readiness y la comprobación de PostgreSQL y de la revisión de Alembic, que solo devuelve estados enumerados sin detalles internos.

## 3.2 Endpoints operativos
- layer: interfaces
- goal: liveness en /api/health (y /api/v1/health) que nunca consulta dependencias, y readiness en /api/ready que responde 503 cuando una dependencia falla.
