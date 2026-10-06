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
- T6.4 Manejar errores controlados.
- T6.5 Tests service allowed.
- T6.6 Tests service denied.
- T6.7 Tests orden policy antes que repository.
- T6.8 Tests no campos sensibles.

**Criterios de cierre:** service valida autorización antes de acceder a datos, usa la organización solicitada validada del `TenantContext`, propaga errores controlados sin HTTP y devuelve salida segura.

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
- [x] T2.1 Crear `UserListQuery`.
- [x] T2.2 Crear `OrganizationUserRead`.
- [x] T2.3 Crear `OrganizationUserListResponse`.
- [x] T2.4 Tests de schemas válidos.
- [x] T2.5 Tests de schemas inválidos/security.
- [x] T3.1 Crear modelo interno `TenantContext`.
- [x] T3.2 Definir errores internos controlados.
- [x] T3.3 Crear builder/factory de TenantContext para tests.
- [x] T3.4 Tests unitarios TenantContext válido.
- [x] T3.5 Tests unitarios denegaciones.
- [x] T4.1 Crear policy.
- [x] T4.2 Regla PLATFORM_ADMIN.
- [x] T4.3 Regla COMPANY_ADMIN.
- [x] T4.4 Regla GROUP_MANAGER.
- [x] T4.5 Regla EMPLOYEE.
- [x] T4.6 Regla usuario/org disabled.
- [x] T4.7 Tests unitarios positivos.
- [x] T4.8 Tests unitarios negativos.
- [x] T5.1 Definir contrato repository.
- [x] T5.2 Implementar query base filtrada por `organization_id`.
- [x] T5.3 Implementar paginación.
- [x] T5.4 Implementar search parametrizado.
- [x] T5.5 Implementar sort allowlist.
- [x] T5.6 Tests repository multi-tenant.
- [x] T5.7 Tests search/sort security.
- [x] T6.1 Crear service.
- [x] T6.2 Invocar policy antes de repository.
- [x] T6.3 Integrar repository.
- [x] T6.4 Manejar errores controlados.
- [x] T6.5 Tests service allowed.
- [x] T6.6 Tests service denied.
- [x] T6.7 Tests orden policy antes que repository.
- [x] T6.8 Tests no campos sensibles.
- [x] T7.1 Dependency de query params.
- [x] T7.2 Dependency de TenantContext.
- [x] T7.3 Dependency de service.
- [x] T7.4 Tests unitarios/dependency si aplica.
- [x] T8.1 Crear router.
- [x] T8.2 Registrar router en API v1.
- [x] T8.3 Integrar dependencies y service.
- [x] T8.4 Definir responses HTTP.
- [x] T8.5 Tests API 200.
- [x] T8.6 Tests API 401/403/404.
- [x] T8.7 Tests API 422.
- [x] T8.8 Test API no `password_hash`.
- [x] T9.1 Definir evento/s IAM piloto.
- [x] T9.2 Implementar audit fake/real según estado backend.
- [x] T9.3 Auditar PLATFORM_ADMIN cross-tenant.
- [x] T9.4 Auditar denegaciones sensibles si procede.
- [x] T9.5 Tests audit.
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
- Tras sincronización/preparación del entorno backend, los bloqueos previos de pytest, Ruff y mypy quedaron resueltos para Task 1.
- `cd backend && uv run ruff check --fix tests/architecture/test_iam_users_structure.py`: OK. Ruff detectó un problema de ordenación de imports en el test de arquitectura de IAM/users y lo corrigió automáticamente.
- `cd backend && uv run ruff format tests/architecture/test_iam_users_structure.py`: OK. Formateo aplicado al test de arquitectura tras la corrección de Ruff.
- `cd backend && uv run pytest tests/architecture/test_iam_users_structure.py`: OK, `2 passed`.
- `make backend-test`: OK. Ruff OK, format OK, mypy OK y pytest OK con `218 passed`.

Validación real ejecutada durante Task 2:

- `git branch --show-current`: OK. Rama actual confirmada: `backend/BACK-ARCH-HEX-001-implantacion-hexagonal`.
- `git status --short`: OK al inicio de Task 2, sin cambios pendientes.
- `cd backend && uv run pytest tests/test_iam_user_list_schemas.py`: OK, `24 passed`.
- `cd backend && uv run ruff check --fix app/domain/iam/users/schemas.py tests/test_iam_user_list_schemas.py`: OK. Ruff corrigió la ordenación de imports en `schemas.py`.
- `cd backend && uv run ruff format app/domain/iam/users/schemas.py tests/test_iam_user_list_schemas.py`: OK, `2 files left unchanged`.
- `make backend-test`: primer intento FALLA en `mypy --strict` por tipos demasiado amplios (`str`) en tests parametrizados de `sort_by` y `sort_dir`; se corrigió usando `model_validate` para payloads dinámicos.
- `cd backend && uv run pytest tests/test_iam_user_list_schemas.py && uv run ruff check app/domain/iam/users/schemas.py tests/test_iam_user_list_schemas.py && uv run ruff format --check app/domain/iam/users/schemas.py tests/test_iam_user_list_schemas.py`: OK, `24 passed`, Ruff OK y formato OK.
- `make backend-test`: OK. Ruff OK, format OK, mypy OK y pytest OK con `242 passed`.

Revalidación real ejecutada tras cambios requeridos por QA en Task 2:

- `cd backend && uv run pytest tests/test_iam_user_list_schemas.py`: OK, `25 passed`.
- `make backend-test`: primer intento FALLA en `ruff check .` por ordenación de imports en `tests/test_iam_user_list_schemas.py` y regla `S106` al pasar un literal a `password_hash` en el stub de test. Se corrigió ordenando imports y evitando el literal sensible en el constructor del stub.
- `make backend-test`: OK. Ruff OK, format OK, mypy OK y pytest OK con `243 passed`.

Validación real ejecutada durante Task 3:

- `git branch --show-current`: OK. Rama actual confirmada: `backend/BACK-ARCH-HEX-001-implantacion-hexagonal`.
- `git status --short`: OK al inicio de Task 3, sin cambios pendientes.
- `cd backend && uv run pytest tests/test_iam_tenant_context.py`: primer intento FALLA con `5 passed, 1 failed` porque el test estático buscaba literales `fastapi`/`sqlalchemy` en todo el source y detectaba las menciones del docstring. Se corrigió para comprobar nombres importados en el módulo.
- `make backend-test`: primer intento FALLA en `ruff check .` por formato de imports en `backend/app/domain/iam/access/tenant_context.py`. Se corrigió con Ruff.
- `cd backend && uv run ruff check --fix app/domain/iam/access/tenant_context.py tests/test_iam_tenant_context.py`: OK. Ruff corrigió el formato de imports en `tenant_context.py`.
- `cd backend && uv run ruff format app/domain/iam/access/tenant_context.py tests/test_iam_tenant_context.py`: OK, `2 files left unchanged`.
- `cd backend && uv run pytest tests/test_iam_tenant_context.py`: OK inicial, `6 passed`.
- Revisión arquitectónica añade una protección adicional para impedir que `is_platform_admin=True` escale privilegios si `platform_role` no es `PLATFORM_ADMIN`.
- `cd backend && uv run pytest tests/test_iam_tenant_context.py`: OK final, `7 passed`.
- `make backend-test`: OK. Ruff OK, format OK, mypy OK y pytest OK con `250 passed`.

Validación real ejecutada durante Task 4:

- `git branch --show-current`: OK. Rama actual confirmada: `backend/BACK-ARCH-HEX-001-implantacion-hexagonal`.
- `git status --short`: OK al inicio de Task 4, sin cambios pendientes.
- `cd backend && uv run pytest tests/test_iam_list_users_policy.py`: OK inicial, `9 passed`.
- `make backend-test`: primer intento FALLA en `mypy --strict` porque el test accedía a un atributo importado no exportado explícitamente desde `policies.py`; se corrigió eliminando esa aserción innecesaria del test de límites.
- `cd backend && uv run pytest tests/test_iam_list_users_policy.py`: OK final, `9 passed`.
- `make backend-test`: OK. Ruff OK, format OK, mypy OK y pytest OK con `259 passed`.

Validación real ejecutada durante Task 5:

- `git branch --show-current`: OK. Rama actual confirmada: `backend/BACK-ARCH-HEX-001-implantacion-hexagonal`.
- `git status --short`: OK al inicio de Task 5, sin cambios pendientes.
- `cd backend && uv run pytest tests/test_iam_users_repository.py`: primer intento FALLA por creación incompleta de tablas referenciadas en SQLite de test; se corrige importando los modelos IAM necesarios y creando metadata completa en la base efímera.
- `cd backend && uv run pytest tests/test_iam_users_repository.py`: segundo intento FALLA al mapear filas SQLAlchemy `Row` directamente a `OrganizationUserRead`; se corrige usando `Session.scalars(...)` para obtener instancias `User`.
- `cd backend && uv run pytest tests/test_iam_users_repository.py`: OK final, `7 passed`.
- `make backend-test`: primer intento FALLA en `ruff check .` por línea demasiado larga y estilo de fixture; se corrige el formato.
- `make backend-test`: segundo intento FALLA en `mypy --strict` por tipos de columnas de ordenación; se corrige devolviendo expresiones tipadas por rama de allowlist.
- `make backend-test`: OK final. Ruff OK, format OK, mypy strict OK y pytest OK con `266 passed`.

Revalidación real ejecutada durante Task 5 tras decisión arquitectónica sobre PostgreSQL:

- `git status --short`: OK. Se observan cambios pendientes previos de Task 5 en `backend/app/domain/iam/users/repositories.py`, `backend/tests/test_iam_users_repository.py` y este documento.
- `git branch --show-current`: OK. Rama actual confirmada: `backend/BACK-ARCH-HEX-001-implantacion-hexagonal`.
- `cd backend && uv run pytest tests/test_iam_users_repository.py`: primer intento FALLA al eliminar SQLite porque SQLAlchemy no tenía registrados en metadata los modelos IAM referenciados por FKs; se corrige importando modelos de catálogos IAM reales en el test.
- `cd backend && uv run pytest tests/test_iam_users_repository.py`: segundo intento FALLA porque la base PostgreSQL local no contenía los registros de catálogo esperados por ID `1`; se corrige creando fixtures de datos de catálogo propios del test en PostgreSQL y limpiándolos tras cada caso.
- `cd backend && uv run pytest tests/test_iam_users_repository.py`: tercer intento FALLA por orden de inserción de catálogos geográficos con FKs; se corrige sembrando país, provincia/estado y ciudad de forma secuencial con commits explícitos antes de organizaciones y usuarios.
- `cd backend && uv run pytest tests/test_iam_users_repository.py`: OK final, `7 passed`.
- `make backend-test`: primer intento FALLA en `ruff check .` por orden de imports y línea larga en `tests/test_iam_users_repository.py`; se corrige el test.
- `make backend-test`: segundo intento FALLA en `ruff format --check .` porque `tests/test_iam_users_repository.py` necesitaba formateo; se ejecuta `cd backend && uv run ruff format tests/test_iam_users_repository.py`, OK, `1 file reformatted`.
- `cd backend && uv run pytest tests/test_iam_users_repository.py`: OK tras formateo, `7 passed`.
- `make backend-test`: OK final. Ruff OK, format OK, mypy strict OK y pytest OK con `266 passed`.

Revisión arquitectónica adicional de Task 5 sobre seguridad de URL de base de datos:

- Se corrige `backend/tests/test_iam_users_repository.py` para exigir explícitamente un dialecto PostgreSQL (`postgresql://`, `postgresql+psycopg://`, `postgresql+psycopg2://` o `postgres://`) antes de crear el engine SQLAlchemy.
- Se elimina el fallback a `.env.example`; los tests de repository ya no pueden pasar accidentalmente con configuración de ejemplo ni con SQLite.
- Si no existe `DATABASE_URL`, el helper solo acepta configuración real desde `.env` local y construye una URL PostgreSQL a partir de las variables `POSTGRES_*`; si no hay configuración suficiente o el dialecto no es PostgreSQL, falla con mensaje claro.
- Se añade un test unitario del helper que rechaza `sqlite:///...` sin abrir conexión a base de datos.
- `cd backend && uv run pytest tests/test_iam_users_repository.py`: FALLA inicialmente porque `.env` local contiene credenciales desalineadas con el contenedor PostgreSQL activo; se confirma que `make db-current` funciona con `.env.example` y que el contenedor `guakamole_postgres` está healthy con los valores esperados por Compose.
- `cd backend && DATABASE_URL='postgresql+psycopg://guakamole_user:***@localhost:5432/guakamole_db' uv run pytest tests/test_iam_users_repository.py`: OK final contra PostgreSQL real, `8 passed`. La contraseña se omite en documentación y logs de resumen.
- `DATABASE_URL='postgresql+psycopg://guakamole_user:***@localhost:5432/guakamole_db' make backend-test`: OK final. Ruff OK, format OK, mypy strict OK y pytest OK con `267 passed`.

Validación real ejecutada durante Task 6:

- `git branch --show-current`: OK. Rama actual confirmada: `backend/BACK-ARCH-HEX-001-implantacion-hexagonal`.
- `git status --short`: OK al inicio de Task 6, sin cambios pendientes.
- `cd backend && uv run pytest tests/test_iam_list_users_service.py`: OK inicial, `7 passed`.
- `make backend-test`: primer intento FALLA en `ruff check .` por argumento no usado en el fake de policy del test de service; se corrige usando explícitamente el parámetro sin cambiar comportamiento.
- `cd backend && uv run pytest tests/test_iam_list_users_service.py && uv run ruff check app/domain/iam/users/services.py tests/test_iam_list_users_service.py && uv run ruff format --check app/domain/iam/users/services.py tests/test_iam_list_users_service.py`: pytest y Ruff OK, pero `ruff format --check` detecta que `services.py` necesitaba formateo.
- `cd backend && uv run ruff format app/domain/iam/users/services.py tests/test_iam_list_users_service.py`: OK, `1 file reformatted, 1 file left unchanged`.
- `cd backend && uv run pytest tests/test_iam_list_users_service.py`: OK final del test específico, `7 passed`.
- `make backend-test`: FALLA inicialmente por los tests de repository al no poder conectar con PostgreSQL en `127.0.0.1:5432` (`Connection refused`). Antes del fallo de pytest, Ruff, format y mypy pasan; pytest reporta `268 passed, 6 errors`, todos en `tests/test_iam_users_repository.py` por indisponibilidad de PostgreSQL local.
- `make postgres-up`: OK. Se levanta el servicio PostgreSQL local usando `.env.example` sin modificar Docker ni ficheros de entorno.
- `DATABASE_URL=postgresql+psycopg://guakamole_user:***@localhost:5432/guakamole_db make backend-test`: OK final contra PostgreSQL real. Ruff OK, format OK, mypy strict OK y pytest OK con `274 passed`.

Validación real ejecutada durante Task 7:

- `git branch --show-current`: OK. Rama actual confirmada: `backend/BACK-ARCH-HEX-001-implantacion-hexagonal`.
- `git status --short`: OK al inicio de Task 7, sin cambios pendientes.
- `cd backend && uv run pytest tests/test_iam_users_dependencies.py`: OK inicial, `15 passed`.
- `make backend-test`: primer intento FALLA en `ruff format --check` porque `tests/test_iam_users_dependencies.py` requería formateo. Se corrige con `cd backend && uv run ruff format tests/test_iam_users_dependencies.py`.
- `make backend-test`: segundo intento FALLA en los tests de repository al usar el `.env` local desalineado con PostgreSQL (`password authentication failed`). Ruff, format y mypy habían pasado antes del fallo de pytest.
- `make postgres-up`: OK. PostgreSQL local queda levantado mediante `.env.example`, sin modificar Docker ni ficheros de entorno.
- `DATABASE_URL=postgresql+psycopg://guakamole_user:***@localhost:5432/guakamole_db make backend-test`: OK final contra PostgreSQL real. Ruff OK, format OK, mypy strict OK y pytest OK con `289 passed`.

Validación real ejecutada durante Task 8:

- `git branch --show-current`: OK. Rama actual confirmada: `backend/BACK-ARCH-HEX-001-implantacion-hexagonal`.
- `git status --short`: OK al inicio de Task 8, sin cambios pendientes.
- `cd backend && uv run pytest tests/test_iam_users_router.py`: OK inicial, `10 passed`. Se detectó un warning de Starlette por el uso de la constante de estado 422 y se corrigió usando el código HTTP literal `422` en la documentación OpenAPI del router.
- `make backend-test`: primer intento FALLA en `ruff check .` por uso de `getattr` con atributo constante y una línea larga en `tests/test_iam_users_router.py`; se corrige tipando el fake con `TenantContext` y dividiendo la llamada.
- `make backend-test`: segundo intento FALLA en `ruff format --check .` porque `backend/app/domain/iam/users/routers.py` y `backend/tests/test_iam_users_router.py` requerían formateo; se ejecuta `cd backend && uv run ruff format app/domain/iam/users/routers.py tests/test_iam_users_router.py`, OK, `2 files reformatted`.
- `make backend-test`: tercer intento FALLA en pytest por dos motivos: el test arquitectónico heredado de Task 1 aún esperaba que no existiera router funcional y los tests de repository no pudieron autenticar contra PostgreSQL local usando la configuración del `.env` local (`password authentication failed`). Ruff, format y mypy strict habían pasado antes del fallo de pytest. Se actualiza el test arquitectónico para reflejar que desde Task 8 el módulo IAM/users sí expone un `APIRouter`.
- `cd backend && uv run pytest tests/test_iam_users_router.py tests/architecture/test_iam_users_structure.py`: OK final de tests específicos de Task 8 y estructura afectada, `12 passed`.
- `make postgres-up`: OK. El contenedor `guakamole_postgres` ya estaba `Running` usando `.env.example`, sin modificar Docker ni ficheros de entorno.
- `DATABASE_URL=postgresql+psycopg://guakamole_user:***@localhost:5432/guakamole_db make backend-test`: FALLA en pytest por autenticación PostgreSQL local (`password authentication failed` para `guakamole_user`). Ruff OK, format OK, mypy strict OK y pytest reporta `293 passed, 6 errors`, todos en `tests/test_iam_users_repository.py` por entorno PostgreSQL/credenciales locales. La contraseña queda enmascarada.

Revalidación real posterior de Task 8 con `DATABASE_URL` PostgreSQL explícita válida:

- `git branch --show-current`: OK. Rama actual confirmada: `backend/BACK-ARCH-HEX-001-implantacion-hexagonal`.
- `git status --short`: OK. Se observan cambios pendientes propios de Task 8 y de este documento; no se observan cambios en frontend, migraciones, Docker, Makefile, `.env` ni `.env.example`.
- `make postgres-up`: OK. El contenedor `guakamole_postgres` permanece `Running` usando `.env.example`, sin modificar Docker ni ficheros de entorno.
- `DATABASE_URL='postgresql+psycopg://guakamole_user:***@localhost:5432/guakamole_db' make backend-test`: OK final contra PostgreSQL real con URL explícita. Ruff OK, format OK, mypy strict OK y pytest OK con `299 passed`.
- `cd backend && uv run pytest tests/test_iam_users_router.py`: OK final del test router específico, `10 passed`.

Validación real ejecutada durante Task 9:

- `git branch --show-current`: OK. Rama actual confirmada: `backend/BACK-ARCH-HEX-001-implantacion-hexagonal`.
- `git status --short`: OK al inicio de Task 9, sin cambios pendientes.
- Búsqueda de auditoría existente en `backend/app` y `backend/tests`: no se encuentra infraestructura `AuditEvent` usable; solo aparece un mixin de timestamps de auditoría en `backend/app/db/mixins.py`.
- `cd backend && uv run pytest tests/test_iam_users_audit.py tests/test_iam_list_users_service.py`: OK, `12 passed`.
- `cd backend && uv run ruff check app/domain/iam/users/services.py tests/test_iam_users_audit.py && uv run ruff format --check app/domain/iam/users/services.py tests/test_iam_users_audit.py && uv run mypy --strict app/domain/iam/users/services.py tests/test_iam_users_audit.py`: primer intento FALLA por orden de imports/línea larga/formato en el nuevo test; se corrige con Ruff y ajuste manual de línea.
- `cd backend && uv run ruff format tests/test_iam_users_audit.py`: OK, `1 file reformatted`.
- `cd backend && uv run ruff check app/domain/iam/users/services.py tests/test_iam_users_audit.py && uv run ruff format --check app/domain/iam/users/services.py tests/test_iam_users_audit.py && uv run mypy --strict app/domain/iam/users/services.py tests/test_iam_users_audit.py`: OK final. Ruff OK, formato OK y mypy strict OK en los ficheros afectados.
- `make postgres-up`: OK. El contenedor `guakamole_postgres` queda `Running` usando `.env.example`, sin modificar Docker ni ficheros de entorno.
- `DATABASE_URL='postgresql+psycopg://guakamole_user:***@localhost:5432/guakamole_db' make backend-test`: primer intento FALLA en pytest por autenticación PostgreSQL local (`password authentication failed` para `guakamole_user`) por entorno/credenciales locales desalineadas; Ruff OK, format OK y mypy strict OK antes del fallo.
- Revalidación arquitectónica con PostgreSQL levantado mediante `make postgres-up` y `DATABASE_URL` explícita válida: `DATABASE_URL='postgresql+psycopg://guakamole_user:***@localhost:5432/guakamole_db' make backend-test`: OK final. Ruff OK, format OK, mypy strict OK y pytest OK con `304 passed`.

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

Task 1 completada y validada en verde. Los bloqueos de entorno detectados inicialmente quedaron resueltos tras la sincronización/preparación del entorno backend y la corrección de Ruff sobre el test de arquitectura. El cierre confirma que no se han introducido cambios funcionales fuera del scaffolding mínimo previsto.

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
- **Comandos ejecutados:** `git branch --show-current`, `git status --short`, `cd backend && uv run ruff check --fix tests/architecture/test_iam_users_structure.py`, `cd backend && uv run ruff format tests/architecture/test_iam_users_structure.py`, `cd backend && uv run pytest tests/architecture/test_iam_users_structure.py` y `make backend-test`.
- **Resultados:** la rama esperada se confirma y el estado inicial estaba limpio. Ruff detectó ordenación incorrecta de imports en `backend/tests/architecture/test_iam_users_structure.py`; se corrigió con `ruff check --fix` y se normalizó el formato con `ruff format`. El test específico de Task 1 queda validado con `2 passed`. La validación completa `make backend-test` queda en verde: Ruff OK, format OK, mypy OK y pytest OK con `218 passed`.
- **Cierre QA:** aprobado y cerrado con validación completa. QA verifica que no hay endpoint real, router funcional expuesto, policies funcionales, repositories con queries, services con lógica de negocio ni dependencies funcionales. También confirma que `models.py` y `schemas.py` existentes no se han modificado, que no se han añadido secretos y que los cambios quedan limitados al alcance esperado.
- **Alcance respetado:** no se implementa endpoint funcional, no se crean schemas funcionales del piloto, no se introduce `TenantContext`, policies, repository ni service funcional, no se modifican migraciones, Docker, Makefile, `.env`, `.env.example` ni frontend, y no se mueven modelos SQLAlchemy existentes.
- **Riesgos/bloqueos:** los bloqueos de entorno documentados inicialmente para Task 1 quedan resueltos en esta validación. No quedan bloqueos conocidos de Task 1 tras `make backend-test` en verde. Cualquier riesgo posterior deberá documentarse en la task correspondiente si aparece durante nuevas implementaciones.

### Task 2 — Schemas Pydantic del piloto IAM

Task 2 completada y validada en verde. Se han añadido únicamente schemas Pydantic del piloto IAM y tests unitarios de schemas, sin implementar endpoint, router funcional, `TenantContext`, policy, repository, service ni auditoría.

- **Schemas añadidos/corregidos:**
  - `UserListQuery`, con `limit` por defecto `50`, máximo `100`, mínimo `1`, `offset >= 0`, `search` opcional con máximo `100` caracteres y normalización por `strip`, `sort_by` con allowlist y `sort_dir` limitado a `asc`/`desc`.
  - `OrganizationUserRead`, como schema explícito de salida para usuarios visibles dentro de organización, con identificadores internos actuales (`id_user`, `id_organization`, roles/estado actuales) y timestamps alineados con los atributos Python del modelo IAM vigente (`created_at`, `updated_at`, `last_login_at`). QA detectó una discrepancia previa entre `create_at`/`update_at` y los atributos ORM `created_at`/`updated_at`, relevante porque el schema usa `ConfigDict(from_attributes=True)`.
  - `OrganizationUserListResponse`, con `items`, `limit`, `offset` y `total` opcional.
- **Decisiones de campos:** se mantiene el criterio de IDs internos `BIGINT` representados como `int`, sin forzar UUID. La allowlist inicial de ordenación usa campos reales o seguros del modelo actual: `email`, `first_name`, `last_name`, `create_at`, `last_login_at` e `id_user`. El schema de salida del piloto no incluye `password_hash`, tokens, secretos, MFA, flags ni respuestas correctas.
- **Configuración Pydantic:** `UserListQuery` usa `ConfigDict(extra="forbid")` para evitar filtros/campos arbitrarios y reducir riesgo de mass assignment. `OrganizationUserRead` usa `ConfigDict(from_attributes=True)` siguiendo el patrón de lectura existente.
- **Tests añadidos/actualizados:** `backend/tests/test_iam_user_list_schemas.py` cubre defaults, límites válidos de paginación, ordenaciones permitidas, direcciones permitidas, normalización de búsqueda, serialización segura de `OrganizationUserRead`, validación `from_attributes=True` desde un objeto tipo ORM con `created_at`/`updated_at`, respuesta paginada y casos inválidos/security (`limit=0`, `limit=101`, `offset=-1`, `sort_by=password_hash`, sort arbitrario, `sort_dir` arbitrario, búsqueda demasiado larga, ausencia de `password_hash` en `model_fields` y rechazo de extra field sensible en query).
- **Archivos modificados/creados:**
  - `backend/app/domain/iam/users/schemas.py`.
  - `backend/tests/test_iam_user_list_schemas.py`.
  - `docs/backend/BACK-ARCH-HEX-001-implementation.md`.
- **Corrección QA aplicada:** se sustituyen `create_at` y `update_at` por `created_at` y `updated_at` en `OrganizationUserRead` para mantener coherencia con `UserRead` y con `TimestampMixin`, sin aliases adicionales.
- **Resultados:** el test específico queda en verde con `25 passed`. La validación completa `make backend-test` queda en verde: Ruff OK, format OK, mypy OK y pytest OK con `243 passed`. Durante esta revalidación hubo un primer intento fallido de `make backend-test` por Ruff en el propio test; se corrigió antes del resultado final en verde.
- **Cierre QA:** aprobado tras la corrección de timestamps en `OrganizationUserRead`. QA revalidó que el schema usa `created_at`/`updated_at`, mantiene compatibilidad `from_attributes=True` mediante un test con objeto tipo ORM, no expone `password_hash` ni secretos y deja Task 2 lista para commit.
- **Alcance respetado:** no se implementa endpoint, router funcional, `TenantContext`, policy, repository, service ni auditoría; no se modifican migraciones, Docker, Makefile, `.env`, `.env.example` ni frontend; no se mueven modelos SQLAlchemy existentes; no se introducen secretos.
- **Riesgos/limitaciones:** `OrganizationUserRead` refleja el modelo IAM simplificado actual, donde el usuario contiene directamente `id_organization`, `id_platform_role` e `id_org_role`; si en fases posteriores se introduce `OrganizationMembership`/roles múltiples, el contrato podrá necesitar una evolución controlada. La validación de `search` en esta task se limita a longitud y normalización; la protección frente a SQL injection deberá completarse en repository mediante queries parametrizadas y allowlists.

### Task 3 — TenantContext mínimo

Task 3 completada, validada en verde y aprobada por QA. Se ha introducido únicamente el contexto interno mínimo de tenant, errores controlados y tests unitarios, sin endpoint, router funcional, policy de listado, repository, service ni auditoría real.

- **Archivo creado:** `backend/app/domain/iam/access/tenant_context.py`.
- **Modelo interno añadido:** `TenantContext` como `dataclass(frozen=True, slots=True)` con los campos mínimos `actor_user_id`, `requested_organization_id`, `effective_organization_id`, `platform_role`, `organization_role`, `user_status`, `organization_status` e `is_platform_admin`.
- **Helpers mínimos añadidos:** propiedades `is_same_organization`, `is_active_user` e `is_active_organization`, sin lógica de policy compleja.
- **Errores internos controlados:** `TenantContextError`, `TenantAccessDeniedError`, `InactiveUserError` e `InactiveOrganizationError`, sin dependencia de HTTP/FastAPI.
- **Builder/validación:** `build_tenant_context(...)` y `validate_tenant_context(...)` construyen y validan el contexto sin consultar base de datos, sin importar modelos SQLAlchemy y sin conocer FastAPI. Validan usuario activo, organización activa, denegación cross-tenant para actores que no sean `PLATFORM_ADMIN` y una protección security-first anti-escalada: si `is_platform_admin=True` pero `platform_role != PLATFORM_ADMIN`, el contexto se deniega.
- **Compatibilidad con IAM simplificado:** el diseño recibe valores ya resueltos de usuario, organización y roles porque el backend actual todavía usa `User.id_organization`, `id_platform_role`, `id_org_role` e `id_status` directamente. No se fingen `OrganizationMembership`, `MembershipRole`, grupos ni scopes aún inexistentes.
- **Tests añadidos:** `backend/tests/test_iam_tenant_context.py` cubre contexto válido same-organization para `COMPANY_ADMIN`, contexto válido cross-tenant para `PLATFORM_ADMIN`, usuario inactivo, organización inactiva, denegación cross-tenant non-platform, prevención de escalada mediante `is_platform_admin=True` sin rol `PLATFORM_ADMIN` y ausencia de imports directos de FastAPI/SQLAlchemy en el módulo.
- **Resultados:** el test específico queda en verde con `7 passed`. La validación completa `make backend-test` queda en verde: Ruff OK, format OK, mypy OK y pytest OK con `250 passed`. Durante la implementación hubo fallos intermedios documentados y corregidos: un test estático demasiado amplio y correcciones de formato requeridas por Ruff.
- **Cierre QA:** aprobado. QA valida las reglas de usuario activo, organización activa, denegación cross-tenant para non-platform, autorización cross-tenant para `PLATFORM_ADMIN` y la mejora anti-escalada cuando `is_platform_admin=True` no está respaldado por `platform_role=PLATFORM_ADMIN`.
- **Alcance respetado:** no se implementa endpoint, router funcional, policy de listado, repository, service ni auditoría real; no se modifican migraciones, Docker, Makefile, `.env`, `.env.example` ni frontend; no se mueven modelos SQLAlchemy existentes; no se introducen secretos.
- **Riesgos/limitaciones:** `TenantContext` no sustituye a la futura policy RBAC. `GROUP_MANAGER`, memberships reales, scopes por grupo y estrategia 403/404 anti-enumeración quedan pendientes para tasks posteriores. El acceso cross-tenant de `PLATFORM_ADMIN` queda permitido a nivel de contexto cuando el rol de plataforma es coherente, pero deberá auditarse y limitarse por caso de uso cuando se implemente la policy/service.

### Task 4 — Policy IAM para listar usuarios

Task 4 completada, validada en verde y aprobada por QA. Se ha implementado únicamente la policy de autorización del caso de uso de listar usuarios de organización y sus tests unitarios, sin endpoint, router funcional, repository, service, dependencies FastAPI ni auditoría real.

- **Policy añadida:** `ListOrganizationUsersPolicy.ensure_allowed(context)` y helper `ensure_can_list_organization_users(context)` en `backend/app/domain/iam/users/policies.py`.
- **Reglas implementadas:** `PLATFORM_ADMIN` permitido con contexto válido, incluyendo acceso cross-tenant; `COMPANY_ADMIN` permitido solo en su propia organización; `GROUP_MANAGER` denegado explícitamente en el piloto inicial por falta de scope de grupo; `EMPLOYEE` denegado; roles desconocidos denegados; usuario y organización inactivos se revalidan mediante `validate_tenant_context` sin duplicar la lógica de `TenantContext`.
- **Tests añadidos:** `backend/tests/test_iam_list_users_policy.py` cubre casos positivos de `PLATFORM_ADMIN` cross-tenant y `COMPANY_ADMIN` own-org, denegación de `COMPANY_ADMIN` cross-tenant en construcción de `TenantContext`, denegación de `GROUP_MANAGER`, `EMPLOYEE` y rol desconocido, revalidación de usuario/organización inactivos y ausencia de imports directos de FastAPI/SQLAlchemy en la policy.
- **Archivos modificados/creados:**
  - `backend/app/domain/iam/users/policies.py`.
  - `backend/tests/test_iam_list_users_policy.py`.
  - `docs/backend/BACK-ARCH-HEX-001-implementation.md`.
- **Resultados:** el test específico queda en verde con `9 passed`. La validación completa `make backend-test` queda en verde: Ruff OK, format OK, mypy strict OK y pytest OK con `259 passed`. Hubo un primer intento fallido de `make backend-test` por mypy en el test de límites; se corrigió antes del resultado final.
- **Cierre QA:** aprobado. QA valida la matriz RBAC implementada para el piloto, la invocación de `validate_tenant_context(context)` antes de conceder permisos, la ausencia de secretos y que no se han añadido endpoint, router funcional, repository, service, dependencies FastAPI ni auditoría real. Como observación menor, el test de imports prohibidos es básico, pero la revisión directa confirma que `policies.py` no introduce dependencias de FastAPI, SQLAlchemy, ORM ni base de datos.
- **Alcance respetado:** no se implementa endpoint, router funcional, repository, service, dependencies FastAPI ni auditoría real; no se modifican migraciones, Docker, Makefile, `.env`, `.env.example` ni frontend; no se mueven modelos SQLAlchemy existentes; no se introducen secretos.
- **Riesgos/limitaciones:** `GROUP_MANAGER` queda denegado hasta definir memberships, grupos y scope real. La policy trabaja sobre el IAM simplificado actual y presupone que capas previas resuelven correctamente los valores del `TenantContext`. La auditoría de accesos `PLATFORM_ADMIN` cross-tenant queda pendiente de Task 9.

### Task 5 — Repository IAM users

Task 5 completada y validada en verde. Se ha implementado únicamente el repository de listado de usuarios de organización y sus tests de repository, sin endpoint, router funcional, service, dependencies FastAPI ni auditoría real.

- **Repository añadido:** `OrganizationUsersRepository` como contrato `Protocol` y `SqlAlchemyOrganizationUsersRepository` como implementación SQLAlchemy sync en `backend/app/domain/iam/users/repositories.py`.
- **Firma principal:** `list_by_organization(*, organization_id: int, query: UserListQuery) -> OrganizationUserListResponse`.
- **Aislamiento por tenant:** la query base aplica siempre `User.id_organization == organization_id`. El `organization_id` se recibe como parámetro controlado por la futura capa de caso de uso, no como filtro arbitrario de cliente.
- **Paginación y filtros:** se aplican `limit` y `offset` desde `UserListQuery`; `search` se limita a `email`, `first_name` y `last_name` con SQLAlchemy parametrizado; la ordenación usa allowlist explícita para `email`, `first_name`, `last_name`, `create_at`, `last_login_at` e `id_user`.
- **Campos sensibles excluidos:** el repository devuelve `OrganizationUserListResponse` con `OrganizationUserRead`; no expone `password_hash`, tokens, MFA secrets ni campos sensibles. Aunque el ORM interno contiene `password_hash`, no se serializa en la salida del repository.
- **Tests añadidos:** `backend/tests/test_iam_users_repository.py` cubre datos multi-org, aislamiento por `organization_id`, paginación, búsqueda permitida, ausencia de fuga cross-tenant con nombres/emails coincidentes, ordenación por allowlist, no exposición de `password_hash` y ausencia de imports FastAPI en el repository.
- **Corrección de riesgo SQLite:** se elimina el uso de SQLite efímero del test de repository. Los tests de `SqlAlchemyOrganizationUsersRepository` usan `create_engine(get_test_database_url(), hide_parameters=True)` contra PostgreSQL real mediante `DATABASE_URL` o configuración PostgreSQL explícita del `.env` local. Se elimina el fallback a `.env.example` para evitar ejecuciones accidentales con placeholders, SQLite u otro dialecto. No crean tablas manualmente ni usan `Base.metadata.create_all`; trabajan contra las tablas existentes del proyecto y siembran/limpian fixtures reales de catálogo, organización y usuario con IDs reservados para el test.
- **Resultados:** el test específico queda en verde contra PostgreSQL real con `8 passed` usando `cd backend && DATABASE_URL='postgresql+psycopg://guakamole_user:***@localhost:5432/guakamole_db' uv run pytest tests/test_iam_users_repository.py`. La validación completa `make backend-test` queda en verde contra PostgreSQL real con `DATABASE_URL='postgresql+psycopg://guakamole_user:***@localhost:5432/guakamole_db' make backend-test`: Ruff OK, format OK, mypy strict OK y pytest OK con `267 passed`. Hubo fallos intermedios documentados por setup SQLite inicial, mapping SQLAlchemy, Ruff, mypy, migración posterior a PostgreSQL y credenciales locales `.env` desalineadas; todos quedaron corregidos o acotados antes del resultado final usando una `DATABASE_URL` PostgreSQL válida y con contraseña enmascarada.
- **Cierre QA:** aprobado. QA valida que los tests de repository no usan SQLite, no usan `Base.metadata.create_all`, no tienen fallback a `.env.example`, rechazan SQLite explícitamente, usan PostgreSQL real mediante `DATABASE_URL` explícita, activan `hide_parameters=True`, limpian fixtures con IDs reservados antes/después y cubren multi-org, no fuga cross-tenant, paginación, search, sort allowlist, no exposición de `password_hash` y ausencia de imports FastAPI. El fallo de `cd backend && uv run pytest tests/test_iam_users_repository.py` con el `.env` local desalineado queda documentado como problema de entorno local, no como bloqueo de Task 5, porque la validación aprobada se ejecutó contra PostgreSQL real con `DATABASE_URL` explícita y contraseña enmascarada.
- **Alcance respetado:** no se implementa endpoint, router funcional, service, dependencies FastAPI ni auditoría real; no se modifican policies, migraciones, Docker, Makefile, `.env`, `.env.example` ni frontend; no se mueven modelos SQLAlchemy existentes; no se introducen secretos.
- **Riesgos/limitaciones:** el repository trabaja sobre el IAM simplificado actual (`User.id_organization`, roles/status directos en usuario). En fases posteriores, si se introducen `OrganizationMembership`, roles múltiples o scopes de grupo, el repository deberá evolucionar sin relajar el filtro tenant. El riesgo de divergencia por SQLite efímero queda corregido: los tests de repository validan queries SQLAlchemy contra PostgreSQL real del entorno de tests y fallan de forma explícita si se intenta usar SQLite, otro dialecto o configuración de ejemplo.

### Task 6 — Service del caso de uso

Task 6 completada y validada en verde. Se ha implementado únicamente el service/use case de listado de usuarios de organización y sus tests unitarios, sin endpoint/router funcional, dependencies FastAPI ni auditoría real.

- **Service añadido:** `ListOrganizationUsersService` en `backend/app/domain/iam/users/services.py`.
- **Firma principal:** `list_users(*, context: TenantContext, query: UserListQuery) -> OrganizationUserListResponse`.
- **Inyección de dependencias:** el service recibe un `OrganizationUsersRepository` y opcionalmente un authorizer compatible con `ListOrganizationUsersAuthorizer`; si no se inyecta policy, usa `ListOrganizationUsersPolicy`.
- **Orden security-first:** el service invoca `policy.ensure_allowed(context)` antes de llamar a `repository.list_by_organization(...)`. Si la policy deniega, el repository no se ejecuta.
- **Tenant controlado:** el repository recibe siempre `context.requested_organization_id`, no un `organization_id` arbitrario de cliente ni un valor de query/body.
- **Errores controlados:** `TenantAccessDeniedError`, `InactiveUserError`, `InactiveOrganizationError` y otros errores controlados derivados de la policy/`TenantContext` se propagan sin convertirlos a HTTP y sin depender de FastAPI.
- **Salida segura:** el service no construye modelos ORM ni serializa campos por su cuenta; devuelve el `OrganizationUserListResponse` del repository, basado en `OrganizationUserRead`, y los tests verifican que no aparece `password_hash`.
- **Tests añadidos:** `backend/tests/test_iam_list_users_service.py` usa fakes in-memory de repository y policy. Cubre caso permitido, uso de `context.requested_organization_id`, propagación de denegación, no llamada al repository si la policy deniega, orden policy antes de repository, ausencia de campos sensibles y ausencia de imports FastAPI/SQLAlchemy en el service.
- **Resultados:** `cd backend && uv run pytest tests/test_iam_list_users_service.py` queda en verde con `7 passed`. Tras levantar PostgreSQL local con `make postgres-up`, la validación completa `DATABASE_URL=postgresql+psycopg://guakamole_user:***@localhost:5432/guakamole_db make backend-test` queda en verde: Ruff OK, format OK, mypy strict OK y pytest OK con `274 passed`. La contraseña se mantiene enmascarada en la documentación.
- **Alcance respetado:** no se implementa endpoint/router funcional, dependencies FastAPI ni auditoría real; no se modifican migraciones, Docker, Makefile, `.env`, `.env.example` ni frontend; no se mueven modelos SQLAlchemy existentes; no se introducen secretos.
- **Riesgos/limitaciones:** Task 6 no implementa auditoría por decisión de alcance; Task 9 se ocupará de ello. La validación completa requiere un PostgreSQL real disponible para los tests de repository heredados de Task 5; en local se resolvió levantando el servicio con `make postgres-up` y usando `DATABASE_URL` explícita enmascarada.

### Task 7 — Dependencies FastAPI del piloto

Task 7 completada, validada en verde y aprobada por QA. Se han implementado únicamente dependencies FastAPI para el piloto IAM/users y sus tests, sin crear router/API funcional, sin registrar endpoint y sin auditoría real.

- **Dependency de query params:** `get_user_list_query(...) -> UserListQuery` construye el schema Pydantic seguro desde parámetros FastAPI `Query`, con límites de paginación, búsqueda acotada y allowlists de ordenación ya definidas por `UserListQuery`.
- **Dependency provisional de identidad:** `get_pilot_authenticated_user() -> PilotAuthenticatedUser` queda marcada explícitamente como provisional y devuelve `501` hasta integrar autenticación real. No acepta identidad, roles ni organización desde query/body; en tests o router futuro deberá sobrescribirse por auth real verificada.
- **Dependency de TenantContext:** `get_tenant_context(organization_id, actor) -> TenantContext` recibe la organización solicitada desde path validado por FastAPI y la identidad resuelta desde la dependency de auth. Construye `TenantContext` mediante `build_tenant_context` y convierte errores controlados de tenant en `403` genérico sin filtrar detalles internos. No acepta `organization_id` desde query/body.
- **Dependency de service:** `get_list_organization_users_service(session) -> ListOrganizationUsersService` construye `SqlAlchemyOrganizationUsersRepository` con una sesión SQLAlchemy real del proyecto y lo inyecta en el service sin ejecutar queries.
- **Sesión DB:** se añade `get_db_session()` con engine/factoría SQLAlchemy cacheados y `DATABASE_URL` obligatoria, usando `hide_parameters=True`. Esta solución es mínima para el piloto porque el proyecto todavía no tiene una dependency centralizada de sesión DB.
- **Tests añadidos:** `backend/tests/test_iam_users_dependencies.py` cubre defaults de query, valores válidos, validaciones Pydantic inválidas, factory de service con repository SQLAlchemy, dependency auth provisional, construcción de `TenantContext`, denegación cross-tenant non-platform, ausencia de `organization_id` por query/body en la firma, límite arquitectónico de imports FastAPI y ausencia de literales sensibles básicos en dependencies.
- **Resultados:** `cd backend && uv run pytest tests/test_iam_users_dependencies.py` queda en verde con `15 passed`. `make postgres-up` deja `guakamole_postgres` en estado `Running`. Tras formatear el test y levantar PostgreSQL local, la validación completa `DATABASE_URL='postgresql+psycopg://guakamole_user:***@localhost:5432/guakamole_db' make backend-test` queda en verde contra PostgreSQL real: Ruff OK, format OK, mypy strict OK y pytest OK con `289 passed`. La contraseña se mantiene enmascarada en la documentación.
- **Cierre QA:** aprobado. QA confirma que T7.1, T7.2, T7.3 y T7.4 quedan completadas; que los query params aplican límites server-side coherentes; que la auth provisional no acepta identidad, roles ni organización desde query/body; que `TenantContext` usa `organization_id` de path y actor resuelto por dependency; que los errores de tenant se traducen a `403` genérico; que la dependency de service construye `ListOrganizationUsersService` con `SqlAlchemyOrganizationUsersRepository` sin ejecutar queries; que `services.py`, `policies.py` y `repositories.py` siguen sin FastAPI; y que no se han añadido secretos.
- **Alcance respetado:** no se implementa router/API funcional, no se registra endpoint, no se implementa auditoría real, no se modifican migraciones, Docker, Makefile, `.env`, `.env.example` ni frontend, y no se mueven modelos SQLAlchemy existentes.
- **Riesgos/limitaciones aceptados:** la autenticación real sigue pendiente para Task 8+ y la dependency provisional debe ser sustituida/sobrescrita por un mecanismo que derive identidad y roles de credenciales verificadas. La dependency de base de datos queda definida localmente en `dependencies.py` por ausencia de infraestructura central actual; QA lo acepta para el piloto, con la deuda de migrarla a una infraestructura común cuando exista. La validación completa sigue dependiendo de PostgreSQL real para los tests de repository heredados.

### Task 8 — Router/API piloto

Task 8 completada, validada en verde y aprobada por QA. La suite completa queda revalidada contra PostgreSQL real con `DATABASE_URL` explícita válida y contraseña enmascarada en la documentación.

- **Router añadido:** `backend/app/domain/iam/users/routers.py` expone un `APIRouter` con `GET /organizations/{organization_id}/users` y `response_model=OrganizationUserListResponse`.
- **Ruta registrada:** `backend/app/api/v1/router.py` incluye el router IAM/users con `prefix="/iam"`, por lo que la ruta final queda disponible como `GET /api/v1/iam/organizations/{organization_id}/users`.
- **Integración de dependencies:** el endpoint usa `get_tenant_context`, `get_user_list_query` y `get_list_organization_users_service`. El router delega en `service.list_users(context=context, query=query)` sin RBAC inline y sin acceso directo a base de datos.
- **Contrato y errores:** `organization_id` se recibe por path con validación `gt=0`; `limit`, `offset`, `search`, `sort_by` y `sort_dir` se validan por las dependencies/schemas existentes. La auth provisional sin override devuelve `501`. Las denegaciones de tenant/RBAC controladas se mapean a `403` genérico y la validación FastAPI/Pydantic devuelve `422`.
- **Response model seguro:** la respuesta usa `OrganizationUserListResponse`/`OrganizationUserRead`, sin `password_hash` ni campos sensibles conocidos.
- **Tests añadidos:** `backend/tests/test_iam_users_router.py` cubre OpenAPI, comportamiento `501` sin override de auth, caso permitido `200`, uso de `context.requested_organization_id` desde path, normalización de query params, denegación cross-tenant `403`, validación `422`, ausencia de `password_hash` y ausencia de imports directos de SQLAlchemy/repository en el router.
- **Test arquitectónico actualizado:** `backend/tests/architecture/test_iam_users_structure.py` deja de exigir scaffolding sin router y ahora valida que el módulo expone un `APIRouter` tras Task 8.
- **Resultados:** los tests específicos quedan en verde con `cd backend && uv run pytest tests/test_iam_users_router.py tests/architecture/test_iam_users_structure.py` (`12 passed`) y con `cd backend && uv run pytest tests/test_iam_users_router.py` (`10 passed`). La validación completa queda finalmente en verde contra PostgreSQL real mediante `DATABASE_URL='postgresql+psycopg://guakamole_user:***@localhost:5432/guakamole_db' make backend-test`: Ruff OK, format OK, mypy strict OK y pytest OK con `299 passed`. El fallo previo de autenticación PostgreSQL local queda explicado por configuración de entorno desalineada cuando no se sobrescribe `DATABASE_URL`, no por el router de Task 8.
- **Cierre QA:** aprobado. QA confirma que T8.1-T8.8 quedan completadas; que el endpoint está registrado correctamente en `GET /api/v1/iam/organizations/{organization_id}/users`; que el router no contiene RBAC inline, consultas directas a base de datos, imports directos de SQLAlchemy ni imports directos de repository; que la auth provisional sin override devuelve `501`; que las denegaciones cross-tenant/RBAC devuelven `403`; que las requests inválidas devuelven `422`; que la respuesta no expone `password_hash`; y que no hay cambios fuera de alcance ni secretos añadidos.
- **Alcance respetado:** no se implementa auditoría real, no se implementa auth real completa, no se modifican migraciones, Docker, Makefile, `.env`, `.env.example` ni frontend, no se mueven modelos SQLAlchemy existentes y no se introducen secretos.
- **Riesgos/limitaciones aceptados:** Task 9 deberá integrar auditoría real porque Task 8 no la implementa por alcance. La dependency provisional de auth sigue devolviendo `501` si no se sobrescribe con autenticación real. IAM mantiene el modelo simplificado actual hasta evolucionar hacia memberships/RBAC completo. La suite completa depende de credenciales PostgreSQL locales coherentes para los tests de repository heredados; para esta revalidación se ha usado `DATABASE_URL` explícita válida y enmascarada.

### Task 9 — Auditoría mínima

Task 9 implementada, corregida tras revisión QA y aprobada en la revalidación final de QA. Se añade auditoría mínima del listado IAM/users sin migraciones, sin auth real completa y sin backend persistente de auditoría porque no existe infraestructura `AuditEvent` usable en `backend/app` más allá de mixins de timestamps.

- **Evento definido:** `IAM_ORGANIZATION_USERS_LISTED`.
- **Puerto de auditoría:** se añade `AuditLogger` como `Protocol`, `AuditEvent` como dataclass congelada y `NoopAuditLogger` como implementación segura por defecto. La integración real con PostgreSQL/observabilidad queda fuera de alcance hasta que exista infraestructura común de auditoría.
- **Corrección QA de inmutabilidad real:** `AuditEvent.metadata` se expone como `Mapping[str, AuditMetadataValue]` y se congela en `__post_init__` con `MappingProxyType(dict(...))`. Esto evita que el `dict` recibido en construcción pueda mutarse a través del evento y hace que asignaciones como `event.metadata["actor_user_id"] = 999` fallen con `TypeError`.
- **Emisión:** `ListOrganizationUsersService.list_users(...)` emite el evento después de autorizar con policy y después de obtener respuesta correcta del repository. Si la policy deniega antes del repository, no se emite evento de éxito y el repository no se ejecuta.
- **Metadata segura:** incluye `requested_organization_id`, `effective_organization_id`, `actor_user_id`, `actor_platform_role`, `actor_organization_role`, `cross_tenant`, `result_count`, `limit`, `offset`, `search_present`, `sort_by` y `sort_dir`. No incluye emails, nombres, `password_hash`, tokens, secretos, respuesta completa, items ni query SQL. El texto crudo de `search` no se audita; solo se registra `search_present`.
- **PLATFORM_ADMIN cross-tenant:** el evento marca `cross_tenant=True` cuando `requested_organization_id != effective_organization_id`, cubriendo el caso autorizado de `PLATFORM_ADMIN` entre organizaciones.
- **Tests añadidos:** `backend/tests/test_iam_users_audit.py` cubre emisión en caso permitido, acción esperada, IDs de actor/organización, `cross_tenant=False` same-org, `cross_tenant=True` para `PLATFORM_ADMIN`, no emisión de éxito cuando la policy deniega, ausencia de metadatos sensibles/personales, inmutabilidad real de `AuditEvent.metadata` con `TypeError` al intentar mutarla y uso de `NoopAuditLogger` por defecto sin romper el service.
- **Archivos modificados/creados:**
  - `backend/app/domain/iam/users/services.py`.
  - `backend/tests/test_iam_users_audit.py`.
  - `docs/backend/BACK-ARCH-HEX-001-implementation.md`.
- **Resultados actualizados tras corrección QA:** `cd backend && uv run pytest tests/test_iam_users_audit.py tests/test_iam_list_users_service.py` queda en verde con `13 passed`. `make postgres-up` confirma el contenedor PostgreSQL en `Running`. La primera ejecución de `DATABASE_URL='postgresql+psycopg://guakamole_user:***@localhost:5432/guakamole_db' make backend-test` detecta únicamente imports modernizables por Ruff (`Mapping`/`MutableMapping` desde `collections.abc`); se corrigen y se repite la validación. La revalidación completa con `DATABASE_URL='postgresql+psycopg://guakamole_user:***@localhost:5432/guakamole_db' make backend-test` queda en verde: Ruff OK, format OK (`81 files already formatted`), mypy strict OK (`80 source files`) y pytest OK con `305 passed`. La URL queda enmascarada.
- **Cierre QA:** aprobado. QA confirma que T9.1-T9.5 quedan completadas, que la corrección de inmutabilidad real de `AuditEvent.metadata` evita mutaciones posteriores del mapping, que se emite `IAM_ORGANIZATION_USERS_LISTED` solo tras policy OK y repository OK, que no se emite evento de éxito cuando la policy deniega, que el repository no se ejecuta si la policy deniega, que `cross_tenant=True` queda cubierto para `PLATFORM_ADMIN` cross-tenant autorizado y que la metadata auditada no contiene datos personales, secretos ni respuestas completas.
- **Alcance respetado:** no se implementa autenticación real, no se crean endpoints nuevos, no se modifican migraciones, Docker, Makefile, `.env`, `.env.example` ni frontend, no se mueven modelos SQLAlchemy existentes y no se introducen secretos en el repositorio.
- **Riesgos/limitaciones:** la auditoría actual es un puerto con `NoopAuditLogger` por defecto; no persiste eventos hasta que se implemente la infraestructura real de auditoría. La suite completa requiere PostgreSQL real para tests heredados de repository; queda revalidada usando `make postgres-up` y `DATABASE_URL` explícita válida con contraseña enmascarada.

### Task 10 — Tests de límites arquitectónicos

Pendiente.

### Task 11 — Documentación única de fase

Pendiente.

### Task 12 — QA final de fase

Pendiente.

## Riesgos o deuda técnica

- Tasks 0 a 9 están implementadas y Task 9 queda aprobada por QA tras revalidar la suite completa con PostgreSQL real mediante `DATABASE_URL` explícita válida y contraseña enmascarada. Quedan pendientes Task 10 en adelante para completar tests de límites arquitectónicos, documentación única de fase y cierre final.
- Riesgo residual aceptado de Task 9: la auditoría mínima queda integrada mediante el puerto `AuditLogger` y `NoopAuditLogger` por defecto, pero todavía no existe infraestructura audit real/persistente. La persistencia de eventos y su envío a observabilidad deberán abordarse en una fase posterior.
- La policy IAM y el `TenantContext` serán puntos críticos: un error puede afectar al aislamiento multiempresa.
- Los tests de límites arquitectónicos deberán equilibrar utilidad y mantenimiento para no bloquear refactors legítimos.
- El repository de Task 5 usa el IAM simplificado actual (`User.id_organization`, roles/status directos en usuario). Cuando existan `OrganizationMembership`, memberships/roles múltiples y scopes por grupo, deberá evolucionar manteniendo el filtro obligatorio por tenant y la ausencia de fugas cross-tenant.
- El `.env` local usado sin sobrescribir `DATABASE_URL` está desalineado con el PostgreSQL real del contenedor local; por ello `cd backend && uv run pytest tests/test_iam_users_repository.py` falla en ese entorno. No bloquea Task 5 porque la validación aprobada por QA se ejecutó contra PostgreSQL real mediante `DATABASE_URL` explícita y enmascarada.

## Relación con el backend

Esta fase afecta directamente al backend porque define el primer corte vertical de la arquitectura hexagonal pragmática security-first sobre IAM. El impacto esperado es establecer patrones reutilizables para routers, dependencies, services, policies, repositories, schemas, auditoría y tests de seguridad multi-tenant.
