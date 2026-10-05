# BACK-ARCH-HEX-001 — Implantación arquitectura hexagonal pragmática security-first

## Estado inicial

Planificación de implementación / pendiente de ejecución.

La rama de trabajo confirmada es `backend/BACK-ARCH-HEX-001-implantacion-hexagonal`.

## Fuente documental

Esta fase se apoya en la documentación backend ya consolidada en la fase `DOC-BACK-ARCH-HEX-001`:

- `docs/backend/hexagonal/architecture.md`
- `docs/backend/hexagonal/adr-backend-hexagonal-architecture.md`
- `docs/backend/hexagonal/module-structure.md`
- `docs/backend/hexagonal/security-and-tenant-rules.md`
- `docs/backend/hexagonal/testing-strategy.md`
- `docs/backend/hexagonal/iam-pilot-design.md`
- `docs/backend/hexagonal/implementation-roadmap.md`

## Objetivo

Implantar incrementalmente la arquitectura hexagonal pragmática security-first en el backend de Project Guakamole, usando como piloto IAM el endpoint:

```text
GET /api/v1/iam/organizations/{organization_id}/users
```

La fase debe validar de forma progresiva:

- `TenantContext` como contexto obligatorio de tenant y autorización.
- RBAC antes de acceso a datos.
- Filtrado de repositorio por `organization_id`.
- Schemas Pydantic seguros, sin exposición de campos sensibles como `password_hash`.
- Tests unitarios, de API, seguridad y límites arquitectónicos.
- Documentación única de avance en este archivo.

## Cambios realizados

Inicialmente solo se crea este documento de planificación de implementación. No se ha modificado código backend productivo, migraciones, Docker, Makefile, `.env`, `.env.example` ni frontend.

## Justificación técnica

Centralizar la planificación de `BACK-ARCH-HEX-001` en un único documento permite coordinar a `api-architect`, `python-implementer`, `qa-tester` y `doc-orchestrator` sin depender de información dispersa en conversaciones. Además, facilita trazabilidad por task, control de alcance y verificación de las reglas security-first antes de avanzar.

## Decisiones tomadas

- Se usará este archivo como documento único de fase: `docs/backend/BACK-ARCH-HEX-001-implementation.md`.
- La implementación será incremental y bloqueante por QA: no se avanza a la siguiente microtask/task si QA no aprueba o si los tests aplicables fallan.
- El piloto IAM será el primer corte vertical para validar arquitectura, seguridad y testing.
- No se documentarán resultados de comandos ni QA hasta que se ejecuten realmente.

## Flujo operativo obligatorio por microtask

1. `api-architect` envía engineering prompt a `python-implementer`.
2. `python-implementer` implementa únicamente el alcance acordado.
3. `api-architect` revisa arquitectura y diff.
4. `api-architect` envía engineering prompt a `qa-tester`.
5. `qa-tester` valida funcionalidad, seguridad, tests y límites de arquitectura.
6. `qa-tester` o `doc-orchestrator` documenta el resultado en este archivo único.
7. `api-architect` revisa la documentación actualizada.
8. `api-architect` realiza el commit correspondiente.

## Reglas estrictas de avance

- No avanzar si QA no aprueba.
- No avanzar si los tests aplicables fallan.
- No avanzar con cambios fuera de alcance.
- No tocar `frontend/`.
- No introducir secretos.
- No romper Alembic.
- No exponer `password_hash`.
- No omitir `TenantContext`.
- No acceder a datos antes de policy.

## Rama y documento de fase

- Rama de trabajo: `backend/BACK-ARCH-HEX-001-implantacion-hexagonal`.
- Documento único de fase: `docs/backend/BACK-ARCH-HEX-001-implementation.md`.

## Roadmap detallado

### Task 0 — Baseline y preparación

**Objetivo:** confirmar contexto de rama, documentación base, estado inicial del backend y punto de partida técnico.

**Microtasks:**

- T0.1 Crear rama de implementación.
- T0.2 Revisar documentación base.
- T0.3 Ejecutar baseline backend.
- T0.4 Explorar estructura IAM actual.
- T0.5 Crear documento único de fase.

**Criterios de cierre:** rama confirmada, documentación base revisada, baseline registrado sin inventar resultados, estructura IAM inspeccionada y este documento creado/actualizado.

### Task 1 — Estructura mínima IAM users sin comportamiento

**Objetivo:** crear la estructura mínima del módulo IAM/users respetando la arquitectura hexagonal, sin añadir comportamiento de negocio todavía.

**Microtasks:**

- T1.1 Crear estructura base.
- T1.2 Añadir imports mínimos seguros.
- T1.3 Tests mínimos de imports.
- T1.4 Validación.

**Criterios de cierre:** estructura importable, sin dependencias prohibidas y validada por tests mínimos.

### Task 2 — Schemas Pydantic del piloto IAM

**Objetivo:** definir contratos de entrada/salida seguros para listar usuarios de organización.

**Microtasks:**

- T2.1 Crear `UserListQuery`.
- T2.2 Crear `OrganizationUserRead`.
- T2.3 Crear `OrganizationUserListResponse`.
- T2.4 Tests de schemas válidos.
- T2.5 Tests de schemas inválidos/security.

**Criterios de cierre:** schemas validados, sin campos sensibles y con cobertura de entradas inválidas.

### Task 3 — TenantContext mínimo

**Objetivo:** introducir el contexto interno de tenant necesario para ejecutar autorización y aislamiento multiempresa.

**Microtasks:**

- T3.1 Crear modelo interno `TenantContext`.
- T3.2 Definir errores internos controlados.
- T3.3 Crear builder/factory de TenantContext para tests.
- T3.4 Tests unitarios TenantContext válido.
- T3.5 Tests unitarios denegaciones.

**Criterios de cierre:** `TenantContext` usable en tests, validaciones básicas cubiertas y errores controlados definidos.

### Task 4 — Policy IAM para listar usuarios

**Objetivo:** centralizar la autorización del caso de uso antes de cualquier consulta a repositorio.

**Microtasks:**

- T4.1 Crear policy.
- T4.2 Regla PLATFORM_ADMIN.
- T4.3 Regla COMPANY_ADMIN.
- T4.4 Regla GROUP_MANAGER.
- T4.5 Regla EMPLOYEE.
- T4.6 Regla usuario/org disabled.
- T4.7 Tests unitarios positivos.
- T4.8 Tests unitarios negativos.

**Criterios de cierre:** matriz RBAC implementada, denegaciones cubiertas y policy libre de dependencias FastAPI.

### Task 5 — Repository IAM users

**Objetivo:** implementar el acceso a datos filtrado por organización y protegido frente a consultas inseguras.

**Microtasks:**

- T5.1 Definir contrato repository.
- T5.2 Implementar query base filtrada por `organization_id`.
- T5.3 Implementar paginación.
- T5.4 Implementar search parametrizado.
- T5.5 Implementar sort allowlist.
- T5.6 Tests repository multi-tenant.
- T5.7 Tests search/sort security.

**Criterios de cierre:** contrato definido, consultas siempre filtradas por tenant y tests de aislamiento/search/sort superados.

### Task 6 — Service del caso de uso

**Objetivo:** orquestar policy, repository, mapping seguro de salida y preparación de auditoría.

**Microtasks:**

- T6.1 Crear service.
- T6.2 Invocar policy antes de repository.
- T6.3 Integrar repository.
- T6.4 Mapear salida segura.
- T6.5 Preparar auditoría.
- T6.6 Tests service allow.
- T6.7 Tests service deny.
- T6.8 Tests audit.

**Criterios de cierre:** service valida autorización antes de acceder a datos, devuelve salida segura y deja auditoría preparada/testeada.

### Task 7 — Dependencies FastAPI del piloto

**Objetivo:** construir dependencias de API para query params, `TenantContext` y service sin mezclar responsabilidades.

**Microtasks:**

- T7.1 Dependency de query params.
- T7.2 Dependency de TenantContext.
- T7.3 Dependency de service.
- T7.4 Tests unitarios/dependency si aplica.

**Criterios de cierre:** dependencias integrables, testeadas cuando aplique y sin lógica de negocio impropia.

### Task 8 — Router/API piloto

**Objetivo:** exponer el endpoint piloto en API v1 respetando contracts, dependencies y respuestas HTTP.

**Microtasks:**

- T8.1 Crear router.
- T8.2 Registrar router en API v1.
- T8.3 Integrar dependencies y service.
- T8.4 Definir responses HTTP.
- T8.5 Tests API 200.
- T8.6 Tests API 401/403/404.
- T8.7 Tests API 422.
- T8.8 Test API no `password_hash`.

**Criterios de cierre:** endpoint funcional, registrado, con respuestas esperadas y tests de seguridad sobre campos sensibles.

### Task 9 — Auditoría mínima

**Objetivo:** registrar eventos mínimos relevantes del piloto IAM, especialmente accesos cross-tenant autorizados y denegaciones sensibles cuando proceda.

**Microtasks:**

- T9.1 Definir evento/s IAM piloto.
- T9.2 Implementar audit fake/real según estado backend.
- T9.3 Auditar PLATFORM_ADMIN cross-tenant.
- T9.4 Auditar denegaciones sensibles si procede.
- T9.5 Tests audit.

**Criterios de cierre:** eventos definidos, mecanismo de auditoría integrado según disponibilidad del backend y tests correspondientes.

### Task 10 — Tests de límites arquitectónicos

**Objetivo:** asegurar que la implementación respeta las fronteras de la arquitectura hexagonal pragmática.

**Microtasks:**

- T10.1 Test router no importa SQLAlchemy directo.
- T10.2 Test router no importa Docker/Guacamole/GitHub.
- T10.3 Test models no importan routers/services.
- T10.4 Test policies no importan FastAPI.
- T10.5 Documentar excepciones si las hubiera.

**Criterios de cierre:** límites arquitectónicos cubiertos por tests y excepciones justificadas explícitamente si existen.

### Task 11 — Documentación única de fase

**Objetivo:** mantener documentación viva y única de la implementación, decisiones, resultados y limitaciones.

**Microtasks:**

- T11.1 Documentar estructura implementada.
- T11.2 Documentar endpoint piloto.
- T11.3 Documentar decisiones de seguridad.
- T11.4 Documentar tests.
- T11.5 Documentar limitaciones.
- T11.6 Documentar riesgos residuales.

**Criterios de cierre:** este archivo refleja fielmente lo implementado, sin inventar resultados ni omitir riesgos conocidos.

### Task 12 — QA final de fase

**Objetivo:** cerrar la fase con revisión de estado, diff, checks, seguridad y documentación.

**Microtasks:**

- T12.1 Revisar `git status`.
- T12.2 Revisar `git diff`.
- T12.3 Ejecutar checks.
- T12.4 QA security review.
- T12.5 Documentar cierre en archivo único.

**Criterios de cierre:** QA final aprobado, checks documentados, diff revisado y cierre registrado en este documento.

## Comandos esperados

Estos comandos se ejecutarán cuando aplique según la task/microtask. Sus resultados deberán registrarse en este documento solo después de ejecutarlos realmente.

```bash
make backend-check
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict .
uv run pytest
make db-upgrade
make db-current
```

## Commits recomendados por task

- `BACK-ARCH-HEX-001 docs: preparar planificación de implementación hexagonal`
- `BACK-ARCH-HEX-001 chore(iam): crear estructura mínima users`
- `BACK-ARCH-HEX-001 feat(iam): añadir schemas seguros del piloto`
- `BACK-ARCH-HEX-001 feat(security): introducir tenant context mínimo`
- `BACK-ARCH-HEX-001 feat(iam): añadir policy de listado de usuarios`
- `BACK-ARCH-HEX-001 feat(iam): implementar repository filtrado por tenant`
- `BACK-ARCH-HEX-001 feat(iam): añadir service de listado de usuarios`
- `BACK-ARCH-HEX-001 feat(api): añadir dependencies IAM piloto`
- `BACK-ARCH-HEX-001 feat(api): exponer endpoint piloto de usuarios IAM`
- `BACK-ARCH-HEX-001 feat(audit): registrar auditoría mínima IAM`
- `BACK-ARCH-HEX-001 test(architecture): validar límites hexagonales`
- `BACK-ARCH-HEX-001 docs: actualizar documentación única de fase`
- `BACK-ARCH-HEX-001 qa: cerrar validación final de fase`

## Estado inicial del roadmap

- [x] T0.1 Crear rama de implementación. Confirmada rama actual: `backend/BACK-ARCH-HEX-001-implantacion-hexagonal`.
- [ ] T0.2 Revisar documentación base.
- [ ] T0.3 Ejecutar baseline backend.
- [ ] T0.4 Explorar estructura IAM actual.
- [ ] T0.5 Crear documento único de fase.
- [ ] T1.1 Crear estructura base.
- [ ] T1.2 Añadir imports mínimos seguros.
- [ ] T1.3 Tests mínimos de imports.
- [ ] T1.4 Validación.
- [ ] T2.1 Crear `UserListQuery`.
- [ ] T2.2 Crear `OrganizationUserRead`.
- [ ] T2.3 Crear `OrganizationUserListResponse`.
- [ ] T2.4 Tests de schemas válidos.
- [ ] T2.5 Tests de schemas inválidos/security.
- [ ] T3.1 Crear modelo interno `TenantContext`.
- [ ] T3.2 Definir errores internos controlados.
- [ ] T3.3 Crear builder/factory de TenantContext para tests.
- [ ] T3.4 Tests unitarios TenantContext válido.
- [ ] T3.5 Tests unitarios denegaciones.
- [ ] T4.1 Crear policy.
- [ ] T4.2 Regla PLATFORM_ADMIN.
- [ ] T4.3 Regla COMPANY_ADMIN.
- [ ] T4.4 Regla GROUP_MANAGER.
- [ ] T4.5 Regla EMPLOYEE.
- [ ] T4.6 Regla usuario/org disabled.
- [ ] T4.7 Tests unitarios positivos.
- [ ] T4.8 Tests unitarios negativos.
- [ ] T5.1 Definir contrato repository.
- [ ] T5.2 Implementar query base filtrada por `organization_id`.
- [ ] T5.3 Implementar paginación.
- [ ] T5.4 Implementar search parametrizado.
- [ ] T5.5 Implementar sort allowlist.
- [ ] T5.6 Tests repository multi-tenant.
- [ ] T5.7 Tests search/sort security.
- [ ] T6.1 Crear service.
- [ ] T6.2 Invocar policy antes de repository.
- [ ] T6.3 Integrar repository.
- [ ] T6.4 Mapear salida segura.
- [ ] T6.5 Preparar auditoría.
- [ ] T6.6 Tests service allow.
- [ ] T6.7 Tests service deny.
- [ ] T6.8 Tests audit.
- [ ] T7.1 Dependency de query params.
- [ ] T7.2 Dependency de TenantContext.
- [ ] T7.3 Dependency de service.
- [ ] T7.4 Tests unitarios/dependency si aplica.
- [ ] T8.1 Crear router.
- [ ] T8.2 Registrar router en API v1.
- [ ] T8.3 Integrar dependencies y service.
- [ ] T8.4 Definir responses HTTP.
- [ ] T8.5 Tests API 200.
- [ ] T8.6 Tests API 401/403/404.
- [ ] T8.7 Tests API 422.
- [ ] T8.8 Test API no `password_hash`.
- [ ] T9.1 Definir evento/s IAM piloto.
- [ ] T9.2 Implementar audit fake/real según estado backend.
- [ ] T9.3 Auditar PLATFORM_ADMIN cross-tenant.
- [ ] T9.4 Auditar denegaciones sensibles si procede.
- [ ] T9.5 Tests audit.
- [ ] T10.1 Test router no importa SQLAlchemy directo.
- [ ] T10.2 Test router no importa Docker/Guacamole/GitHub.
- [ ] T10.3 Test models no importan routers/services.
- [ ] T10.4 Test policies no importan FastAPI.
- [ ] T10.5 Documentar excepciones si las hubiera.
- [ ] T11.1 Documentar estructura implementada.
- [ ] T11.2 Documentar endpoint piloto.
- [ ] T11.3 Documentar decisiones de seguridad.
- [ ] T11.4 Documentar tests.
- [ ] T11.5 Documentar limitaciones.
- [ ] T11.6 Documentar riesgos residuales.
- [ ] T12.1 Revisar `git status`.
- [ ] T12.2 Revisar `git diff`.
- [ ] T12.3 Ejecutar checks.
- [ ] T12.4 QA security review.
- [ ] T12.5 Documentar cierre en archivo único.

## Tests ejecutados

No se han ejecutado tests ni comandos de QA en esta actualización documental inicial. Quedan pendientes para las microtasks correspondientes.

## Registro de resultados por task

### Task 0 — Baseline y preparación

Pendiente de registrar resultados, salvo confirmación de rama actual.

### Task 1 — Estructura mínima IAM users sin comportamiento

Pendiente.

### Task 2 — Schemas Pydantic del piloto IAM

Pendiente.

### Task 3 — TenantContext mínimo

Pendiente.

### Task 4 — Policy IAM para listar usuarios

Pendiente.

### Task 5 — Repository IAM users

Pendiente.

### Task 6 — Service del caso de uso

Pendiente.

### Task 7 — Dependencies FastAPI del piloto

Pendiente.

### Task 8 — Router/API piloto

Pendiente.

### Task 9 — Auditoría mínima

Pendiente.

### Task 10 — Tests de límites arquitectónicos

Pendiente.

### Task 11 — Documentación única de fase

Pendiente.

### Task 12 — QA final de fase

Pendiente.

## Riesgos o deuda técnica

- La implementación aún no ha comenzado; cualquier detalle técnico queda pendiente de validación contra el estado real del backend.
- La auditoría final dependerá del estado actual del módulo de auditoría backend; si no existe integración real suficiente, se deberá documentar el uso de fake/stub y su deuda asociada.
- La policy IAM y el `TenantContext` serán puntos críticos: un error puede afectar al aislamiento multiempresa.
- Los tests de límites arquitectónicos deberán equilibrar utilidad y mantenimiento para no bloquear refactors legítimos.

## Relación con el backend

Esta fase afecta directamente al backend porque define el primer corte vertical de la arquitectura hexagonal pragmática security-first sobre IAM. El impacto esperado es establecer patrones reutilizables para routers, dependencies, services, policies, repositories, schemas, auditoría y tests de seguridad multi-tenant.
