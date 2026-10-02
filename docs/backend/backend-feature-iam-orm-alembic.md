# backend/feature/iam-orm-alembic

## Objetivo

Documentar el estado final backend de la branch `backend/feature/iam-orm-alembic`, centrada en implementar la base ORM/Alembic de IAM sobre PostgreSQL.

## Resumen

La branch implementa la base de persistencia IAM en el schema PostgreSQL `sch_iam`. El trabajo define tablas con prefijo `tbl_*`, identificadores `BIGINT`, migraciones Alembic versionadas y schemas Pydantic v2 para validar la capa de datos expuesta por el dominio.

La implementación deja preparada la estructura backend para evolucionar hacia autenticación, autorización, RBAC y multi-tenancy, pero esta branch no incorpora endpoints CRUD ni lógica runtime de autenticación/RBAC.

## Cambios realizados

### Alcance implementado

Entidades/tablas implementadas en `sch_iam`:

- `tbl_country`
- `tbl_status`
- `tbl_platform_role`
- `tbl_organization_role`
- `tbl_state`
- `tbl_city`
- `tbl_organization`
- `tbl_users`
- `tbl_department`
- `tbl_department_relations`

Seeds iniciales incluidos en Task 11 mediante `0012_seed_initial_iam_catalogs`:

- Estados: `ACTIVE`, `INACTIVE`, `DISABLED`.
- Roles de plataforma: `PLATFORM_ADMIN`, `USER`.
- Roles de organización: `COMPANY_ADMIN`, `GROUP_MANAGER`, `EMPLOYEE`.
- Países: `España`, `Portugal`, `Francia`.
- Estados/regiones: `Catalunya`, `Madrid`, `Lisboa`.
- Ciudades: `Barcelona`, `Madrid`, `Lisboa`.

### Estructura de código

- `backend/app/db/`: infraestructura común de base de datos, `Base.metadata` y mixins reutilizables.
- `backend/app/domain/iam/`: dominio IAM organizado por subdominios funcionales.
- Modelos ORM por dominio en ficheros `models.py` dentro de `access`, `departments`, `geography`, `organizations` y `users`.
- Schemas Pydantic v2 en ficheros `schemas.py` dentro de los mismos subdominios.
- Migraciones Alembic en `backend/alembic/versions/`.

### Migraciones Alembic

- `0001_create_schema_iam`: crea el schema `sch_iam`, ajusta permisos iniciales y amplía `alembic_version.version_num` a `VARCHAR(255)`.
- `0002_create_tbl_country`: crea `sch_iam.tbl_country`.
- `0003_create_tbl_status`: crea `sch_iam.tbl_status`.
- `0004_create_tbl_platform_role`: crea `sch_iam.tbl_platform_role`.
- `0005_create_tbl_organization_role`: crea `sch_iam.tbl_organization_role`.
- `0006_create_tbl_state`: crea `sch_iam.tbl_state` con FK a país.
- `0007_create_tbl_city`: crea `sch_iam.tbl_city` con FK a estado/región.
- `0008_create_tbl_organization`: crea `sch_iam.tbl_organization` con relaciones a catálogos IAM.
- `0009_create_tbl_users`: crea `sch_iam.tbl_users` con email único y sin exponer `password_hash` en lectura.
- `0010_create_tbl_department`: crea `sch_iam.tbl_department`.
- `0011_create_tbl_department_relations`: crea `sch_iam.tbl_department_relations` con relaciones jerárquicas entre departamentos.
- `0012_seed_initial_iam_catalogs`: inserta seeds mínimos de catálogos IAM y es la `head` actual.

Las migraciones usan el literal `sch_iam` para mantener inmutabilidad histórica aunque exista la constante de aplicación `IAM_SCHEMA`. La tabla `alembic_version` usa `version_num VARCHAR(255)` para soportar revision IDs descriptivas sin truncado.

## Justificacion tecnica

PostgreSQL actúa como **Operational Source of Truth** para usuarios, organizaciones, roles, catálogos, departamentos y relaciones operativas. GitHub/Markdown no contiene secretos, respuestas correctas ni lógica sensible de evaluación.

La separación por schema `sch_iam` proporciona una frontera clara para el dominio IAM, facilita inspección y migraciones, y prepara el backend para futuras reglas de aislamiento multi-tenant. Esta separación no sustituye a RBAC ni a validaciones de tenant en APIs futuras.

## Decisiones tomadas

- Mantener seeds mínimos orientados a desarrollo y demo, no como catálogo completo de producción.
- No añadir endpoints CRUD en esta branch.
- No implementar todavía lógica runtime de autenticación, autorización ni RBAC; solo base ORM, catálogos y migraciones.
- Mantener migraciones Alembic con schema literal `sch_iam`.
- Usar Pydantic v2 para schemas de entrada/salida del dominio.
- El target `db-downgrade` respeta `REVISION` cuando se informa y usa `-1` como valor por defecto.

## Tests ejecutados

Validación final comunicada para Task 12:

- `211 passed`.
- Base de datos en `0012_seed_initial_iam_catalogs (head)`.

Para validar esta documentación no se han ejecutado tests adicionales, al tratarse exclusivamente de Task 13 documental.

## Comandos de validación

```bash
make backend-check
make docker-config
make db-history
make db-upgrade
make db-current
make db-downgrade REVISION=0011_create_tbl_department_relations
make db-upgrade
```

## Validación PostgreSQL esperada

Usando el entorno de desarrollo compartido definido en `.env.example`, sin credenciales reales en documentación, QA puede confirmar:

- Que existe el schema `sch_iam`.
- Que existen las tablas `tbl_country`, `tbl_status`, `tbl_platform_role`, `tbl_organization_role`, `tbl_state`, `tbl_city`, `tbl_organization`, `tbl_users`, `tbl_department` y `tbl_department_relations`.
- Que `alembic_version.version_num` queda en `0012_seed_initial_iam_catalogs` tras `make db-upgrade`.
- Que los seeds mínimos aparecen en tablas de catálogos tras aplicar la migración `0012`.
- Que al ejecutar `make db-downgrade REVISION=0011_create_tbl_department_relations` se revierten solo los seeds de Task 11 y se conserva la estructura hasta `0011`.

## Riesgos o deuda tecnica

- El aislamiento `sch_iam` es una base organizativa, no un control completo de autorización multi-tenant.
- Las futuras APIs no deberán confiar en un `organization_id` recibido desde el frontend sin validarlo contra la identidad autenticada y el tenant context.
- Falta implementar autenticación, RBAC runtime, repositorios, servicios y endpoints.
- Los seeds son mínimos y pueden requerir ampliación cuando el flujo funcional avance.

## Seguridad

- No se debe modificar ni documentar contenido sensible de `.env`.
- No se añaden secretos reales en la documentación.
- GitHub/Markdown no contiene secretos ni respuestas correctas.
- El aislamiento por `sch_iam` ayuda a separar IAM, pero no sustituye a RBAC, validaciones server-side ni aislamiento multi-tenant.
- Las futuras APIs deberán derivar la organización desde la sesión/JWT/membership y no desde datos confiados del navegador.

## Estado final

Task 12 fue validada con `211 passed` y la base de datos en `0012_seed_initial_iam_catalogs (head)`. Task 13 deja actualizada la documentación backend final de la branch para QA/PR.

## Relacion con el backend

Esta documentación describe la base de datos operativa IAM del backend y cómo validarla con Alembic, PostgreSQL y los comandos `make` disponibles. El impacto principal es dejar trazabilidad para QA y PR sobre el estado actual de modelos ORM, schemas Pydantic, migraciones y seeds del dominio IAM.
