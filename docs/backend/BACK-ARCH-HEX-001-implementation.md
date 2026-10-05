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

Se crea y actualiza este documento de planificación y baseline de implementación. En Task 0 se ha documentado el estado inicial real de la rama, los comandos ejecutados, el resultado de Alembic y la estructura IAM observada. No se ha modificado código backend productivo, migraciones, Docker, Makefile, `.env`, `.env.example` ni frontend.

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
- T0.2 Revisar documentación base. **Completada en baseline Task 0.**
- T0.3 Ejecutar baseline backend. **Completada con bloqueo parcial documentado.**
- T0.4 Explorar estructura IAM actual. **Completada en baseline Task 0.**
- T0.5 Crear documento único de fase. **Completada/actualizada en baseline Task 0.**

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
- [x] T0.2 Revisar documentación base.
- [x] T0.3 Ejecutar baseline backend.
- [x] T0.4 Explorar estructura IAM actual.
- [x] T0.5 Crear documento único de fase.
- [x] T1.1 Crear estructura base.
- [x] T1.2 Añadir imports mínimos seguros.
- [x] T1.3 Tests mínimos de imports.
- [x] T1.4 Validación.
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

Baseline real ejecutado durante Task 0:

- `git branch --show-current`: OK. Rama actual confirmada: `backend/BACK-ARCH-HEX-001-implantacion-hexagonal`.
- `git status --short`: OK. Sin cambios iniciales registrados antes de actualizar este documento.
- `make backend-check`: FALLA. El objetivo ejecuta `curl -i http://localhost:8000/api/health` y no puede conectar con `localhost:8000`; no parece estar levantado el servicio FastAPI local.
- `make db-current`: OK. Alembic informa `0012_seed_initial_iam_catalogs (head)`.
- `make db-history`: OK. Historial lineal desde `0001_create_schema_iam` hasta `0012_seed_initial_iam_catalogs (head)`.
- `make db-upgrade`: OK. Ejecutado porque el entorno permitió validar Alembic sin destruir datos; `alembic upgrade head` no aplicó cambios pendientes visibles al estar ya en head.

Validación real ejecutada durante Task 1:

- `git branch --show-current`: OK. Rama actual confirmada: `backend/BACK-ARCH-HEX-001-implantacion-hexagonal`.
- `git status --short`: OK al inicio de Task 1, sin cambios pendientes.
- `uv run pytest backend/tests/architecture/test_iam_users_structure.py`: FALLA antes de ejecutar tests por configuración existente de pytest: `Unknown config option: asyncio_mode`. Pytest llega a recolectar 2 tests, pero termina con código 4. También aparece un warning preexistente relacionado con el filtro de warnings de `starlette`.
- `uv run ruff check .`: FALLA porque el ejecutable `ruff` no está disponible en el entorno gestionado por `uv` (`No such file or directory`).
- `uv run mypy --strict .`: FALLA por errores preexistentes de entorno/tipado, principalmente imports no encontrados de `sqlalchemy`, `fastapi` y atributos de `alembic`. No se han corregido por estar fuera del alcance de Task 1.

## Registro de resultados por task

### Task 0 — Baseline y preparación

Task 0 completada como baseline/preparación sin cambios funcionales.

- **Rama confirmada:** `backend/BACK-ARCH-HEX-001-implantacion-hexagonal`.
- **Documentación base revisada:**
  - `docs/backend/hexagonal/architecture.md`.
  - `docs/backend/hexagonal/adr-backend-hexagonal-architecture.md`.
  - `docs/backend/hexagonal/module-structure.md`.
  - `docs/backend/hexagonal/security-and-tenant-rules.md`.
  - `docs/backend/hexagonal/testing-strategy.md`.
  - `docs/backend/hexagonal/iam-pilot-design.md`.
  - `docs/backend/hexagonal/implementation-roadmap.md`.
  - `docs/backend/BACK-ARCH-HEX-001-implementation.md`.
- **Comandos ejecutados:** `git branch --show-current`, `git status --short`, `make backend-check`, `make db-current`, `make db-history` y `make db-upgrade`.
- **Resultado de baseline:** Alembic está en head (`0012_seed_initial_iam_catalogs`). El baseline de health check falla porque FastAPI no está escuchando en `localhost:8000`; no se ha intentado corregir por estar fuera del alcance de Task 0.
- **Estructura IAM observada:** existe `backend/app/domain/iam/` con subdominios `access`, `geography`, `organizations`, `users` y `departments`, además de `constants.py` con `IAM_SCHEMA = "sch_iam"`. La estructura actual contiene principalmente modelos SQLAlchemy y schemas Pydantic; todavía no se observan `routers.py`, `services.py`, `policies.py`, `repositories.py` ni `dependencies.py` para el piloto hexagonal de users.
- **Modelos/tablas IAM principales observados:**
  - `Status` → `sch_iam.tbl_status`.
  - `PlatformRole` → `sch_iam.tbl_platform_role`.
  - `OrganizationRole` → `sch_iam.tbl_organization_role`.
  - `Country`, `State`, `City` → catálogos geográficos `sch_iam.tbl_country`, `sch_iam.tbl_state`, `sch_iam.tbl_city`.
  - `Organization` → `sch_iam.tbl_organization`, con FKs a país, provincia/estado, ciudad y estado.
  - `User` → `sch_iam.tbl_users`, con `id_organization`, roles global/organización, geografía, estado, email, `password_hash`, datos personales y `last_login_at`.
  - `Department` → `sch_iam.tbl_department`, asociado a organización.
  - `DepartmentRelation` → `sch_iam.tbl_department_relations`, relación entre departamento y usuario.
- **Tests IAM actuales observados:** hay tests en `backend/tests/` para modelos, schemas y migraciones IAM: usuarios, organización, roles de plataforma/organización, estados, país/provincia/ciudad, departamentos, relaciones departamento-usuario, preparación ORM y seeds iniciales. Ya existe un test específico que comprueba que `UserRead` no expone `password_hash`.
- **Migraciones/head observadas:** migraciones lineales `0001_create_schema_iam` → `0012_seed_initial_iam_catalogs (head)`. Las migraciones cubren schema IAM, catálogos geográficos, estados, roles, organización, usuarios, departamentos, relaciones departamento-usuario y seeds iniciales IAM.
- **Secretos:** no se han añadido secretos ni se han modificado archivos de configuración sensible (`.env`, `.env.example`).
- **Limitaciones/riesgos identificados:** el IAM actual es una implementación relacional simplificada frente al domain model objetivo: `User` pertenece directamente a una organización y tiene un rol global/organizativo directo; no se observa todavía `OrganizationMembership`, `MembershipRole`, `Group`, `GroupMember` ni `GroupManager` como tablas/modelos separados. El endpoint piloto deberá documentar y tratar esta limitación al diseñar `TenantContext`, RBAC y aislamiento multi-tenant. El fallo de `make backend-check` queda como bloqueo operativo del baseline si QA requiere health check con servidor local levantado.

### Task 1 — Estructura mínima IAM users sin comportamiento

Task 1 completada y aprobada por QA a nivel de implementación de scaffolding, con bloqueos de validación automática del entorno documentados. El cierre QA confirma que los problemas detectados no son atribuibles al scaffolding de Task 1 y que no se han introducido cambios funcionales.

- **Estructura creada/completada:** se mantiene `backend/app/domain/iam/users/models.py` sin moverlo ni reestructurarlo y se conserva `schemas.py` existente sin cambios funcionales. Se añade el scaffolding mínimo importable para `routers.py`, `services.py`, `policies.py`, `repositories.py` y `dependencies.py`. También se añade un docstring mínimo y `__all__` vacío en `__init__.py`.
- **Archivos creados/modificados:**
  - `backend/app/domain/iam/users/__init__.py`.
  - `backend/app/domain/iam/users/routers.py`.
  - `backend/app/domain/iam/users/services.py`.
  - `backend/app/domain/iam/users/policies.py`.
  - `backend/app/domain/iam/users/repositories.py`.
  - `backend/app/domain/iam/users/dependencies.py`.
  - `backend/tests/architecture/__init__.py`.
  - `backend/tests/architecture/test_iam_users_structure.py`.
  - `docs/backend/BACK-ARCH-HEX-001-implementation.md`.
- **Tests añadidos:** `backend/tests/architecture/test_iam_users_structure.py` intenta importar los módulos mínimos de IAM/users y verifica que `routers.py` no expone todavía un `router` funcional.
- **Comandos ejecutados:** `git branch --show-current`, `git status --short`, `uv run pytest backend/tests/architecture/test_iam_users_structure.py`, `uv run ruff check .` y `uv run mypy --strict .`.
- **Resultados:** la rama esperada se confirma y el estado inicial estaba limpio. La validación automática queda bloqueada por problemas de entorno/configuración preexistentes: pytest falla por `asyncio_mode` desconocido, aunque llega a recolectar 2 tests; ruff no está instalado/disponible en el entorno `uv`; y mypy falla por dependencias/stubs no disponibles de SQLAlchemy/FastAPI/Alembic. QA confirma imports manuales correctos y no observa fallos atribuibles al scaffolding añadido.
- **Cierre QA:** aprobado. QA verifica que no hay endpoint real, router funcional expuesto, policies funcionales, repositories con queries, services con lógica de negocio ni dependencies funcionales. También confirma que `models.py` y `schemas.py` existentes no se han modificado, que no se han añadido secretos y que los cambios quedan limitados al alcance esperado.
- **Alcance respetado:** no se implementa endpoint funcional, no se crean schemas funcionales del piloto, no se introduce `TenantContext`, policies, repository ni service funcional, no se modifican migraciones, Docker, Makefile, `.env`, `.env.example` ni frontend, y no se mueven modelos SQLAlchemy existentes.
- **Riesgos/bloqueos:** antes de avanzar olvidando la deuda de entorno, debe mantenerse visible que la validación automática completa sigue bloqueada: compatibilidad de pytest con `asyncio_mode`, disponibilidad de `ruff` y dependencias/stubs necesarios para `mypy --strict`. Task 1 queda aprobada por QA, pero la rama todavía no dispone de una ejecución completa en verde de checks automáticos.

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
