# Roadmap backend — IAM ORM/Pydantic/PostgreSQL/Alembic

Branch esperada: `backend/feature/iam-orm-alembic`

Schema PostgreSQL IAM: `sch_iam`

Estado: Task 2 completada; Task 2b documental preparada para revisión QA.

## Task 0 — Preparación ORM/Alembic/schema `sch_iam`

- [x] 0.1 Crear estructura modular IAM.
- [x] 0.2 Crear constante compartida `IAM_SCHEMA = "sch_iam"`.
- [x] 0.3 Crear mixin reusable de timestamps (`create_at`/`update_at`) en `backend/app/db/mixins.py`.
- [x] 0.4 Preparar `Base.metadata` para Alembic desde `backend/app/db/base.py`.
- [x] 0.5 Crear migración Alembic `0001_create_schema_iam`.
- [x] 0.6 Crear schema `sch_iam`, revocar `CREATE` en `public` y no crear tablas IAM.
- [x] 0.7 Añadir tests mínimos de configuración ORM/Alembic.
- [x] 0.8 Ejecutar validación de backend y Docker Compose.
- [x] 0.9 Parametrizar `sqlalchemy.url` mediante entorno para evitar credenciales hardcodeadas.
- [x] 0.10 Hacer inmutable la migración inicial usando `sch_iam` literal en Alembic.
- [x] 0.11 Añadir `DATABASE_URL` de desarrollo en `.env.example` y constantes de configuración en Alembic.
- [x] 0.12 Centralizar selección de archivo de entorno mediante `ENV_FILE ?= .env.example` y targets DB Alembic.

> Nota: los puntos 0.11 y 0.12 quedan registrados como completados dentro de la
> preparación inicial, pero el detalle operativo completo se documenta en la
> **Task 2b — Anexo configuración dinámica de entorno y Alembic DEV** para evitar
> duplicidad y facilitar la revisión QA de los ajustes posteriores a Task 2.

### Estructura Task 0

```text
backend/app/db/
├── __init__.py
├── base.py
└── mixins.py

backend/app/domain/
├── __init__.py
└── iam/
    ├── __init__.py
    ├── constants.py
    ├── geography/
    │   └── __init__.py
    ├── access/
    │   └── __init__.py
    ├── organizations/
    │   └── __init__.py
    ├── users/
    │   └── __init__.py
    └── departments/
        └── __init__.py
```

### Reglas globales para futuras tasks IAM

- Todos los modelos, schemas, repositorios y servicios funcionales de IAM deben crearse bajo `backend/app/domain/iam/`.
- No se debe recuperar la estructura antigua raíz de IAM fuera de `domain`.
- La infraestructura DB común debe vivir en `backend/app/db/`.
- `Base` debe importarse desde `app.db.base`.
- Los mixins comunes de base de datos deben vivir en `backend/app/db/mixins.py`.
- `TimestampMixin` debe importarse desde `app.db.mixins`.
- `IAM_SCHEMA` debe importarse desde `app.domain.iam.constants`.
- `IAM_SCHEMA` queda reservado para modelos y código de aplicación; las migraciones Alembic ya publicadas deben usar literales inmutables.
- Alembic debe usar `Base.metadata` importado desde `app.db.base`.

### Criterios Task 0

- [x] Existe `sch_iam` definido como schema IAM.
- [x] Existe infraestructura común en `backend/app/db/`.
- [x] Existe estructura funcional IAM en `backend/app/domain/iam/`.
- [x] No se crean tablas todavía.
- [x] No se elimina `public`.
- [x] Alembic reconoce metadata.
- [x] Alembic obtiene la URL de base de datos desde `DATABASE_URL` y `alembic.ini` no almacena credenciales operativas.
- [x] La migración inicial usa el literal `sch_iam` y no depende de `IAM_SCHEMA`.
- [x] Docker Compose y targets DB usan `ENV_FILE` para alternar entre `.env.example` y `.env` sin duplicar configuración.
- [x] Tests pasan.

## Task 1 — Modelado base de catálogos geográficos

- [x] 1.1 Crear modelo ORM `Country`.
- [x] 1.2 Crear schemas Pydantic.
- [x] 1.3 Crear migración `0002_create_tbl_country`.
- [x] 1.4 Definir constraint `pk_tbl_country`.
- [x] 1.5 Añadir tests metadata.
- [x] 1.6 Ejecutar validación.

## Task 2 — Crear `tbl_status`

- [x] 2.1 Crear modelo ORM `Status`.
- [x] 2.2 Crear schemas `StatusBase`, `StatusCreate`, `StatusUpdate`, `StatusRead`.
- [x] 2.3 Crear migración `0003_create_tbl_status`.
- [x] 2.4 Definir constraint `pk_tbl_status`.
- [x] 2.5 Añadir tests metadata.
- [x] 2.6 Ejecutar validación.

# Task 2b — Anexo configuración dinámica de entorno y Alembic DEV

## Objetivo

Registrar los ajustes de configuración dinámica de entorno, Alembic y comandos de
desarrollo necesarios para continuar con las siguientes tasks IAM sin introducir
nuevas tablas, migraciones ni funcionalidad de dominio.

## Contexto

Durante la validación posterior a Task 2 fue necesario preparar un flujo de
desarrollo más cómodo para probar PostgreSQL, Alembic y pgAdmin en entornos DEV
compartidos. Estos cambios permiten usar `.env.example` como configuración local
por defecto y facilitan alternar en el futuro a `.env` mediante `ENV_FILE=.env`,
sin cargar automáticamente `.env` desde Alembic ni guardar credenciales
operativas en `alembic.ini`.

## Cambios incluidos

- [x] 2b.1 Añadir `DATABASE_URL` a `.env.example` para desarrollo local compartido.
- [x] 2b.2 Alinear `POSTGRES_PASSWORD` de `.env.example` con `DATABASE_URL`.
- [x] 2b.3 Añadir constantes de configuración en `backend/alembic/env.py`.
- [x] 2b.4 Mantener Alembic leyendo `DATABASE_URL` desde entorno, sin credenciales en `alembic.ini`.
- [x] 2b.5 Centralizar archivo de entorno en `Makefile` con `ENV_FILE ?= .env.example`.
- [x] 2b.6 Actualizar Docker Compose targets para usar `$(ENV_FILE)`.
- [x] 2b.7 Añadir targets DB/Alembic: `db-upgrade`, `db-current`, `db-history`, `db-downgrade`.
- [x] 2b.8 Añadir tests de configuración para `.env.example`, Alembic y Makefile.
- [x] 2b.9 Documentar uso DEV con `.env.example` y uso futuro con `.env` mediante `ENV_FILE=.env`.
- [x] 2b.10 Registrar notas de pgAdmin/WSL y recreación de volumen tras cambios de credenciales.

## Validación esperada

```bash
make help
make backend-check
make docker-config
make docker-config ENV_FILE=.env.example
make db-history
```

También debe poder usarse, cuando exista `.env` local privado:

```bash
make docker-up ENV_FILE=.env
make db-upgrade ENV_FILE=.env
```

## Notas operativas DEV

Para recrear la base de datos tras cambiar credenciales en el entorno de
desarrollo:

```bash
make docker-down
docker volume rm guakamole-platform_postgres_data
make postgres-up
```

Para aplicar migraciones usando la configuración DEV compartida por defecto:

```bash
make db-upgrade
```

Para producción/local privado futuro con `.env`:

```bash
make db-upgrade ENV_FILE=.env
```

pgAdmin debe configurarse manualmente con los valores del entorno; no lee
`.env.example` ni `.env` automáticamente. Si pgAdmin se ejecuta en Windows y
PostgreSQL en WSL/Docker, puede ser necesario usar la IP de WSL como host en vez
de `localhost`.

## Seguridad

- `.env` no se commitea.
- `.env.example` es solo DEV compartido.
- `alembic.ini` no contiene credenciales operativas.
- No se añaden secretos reales.

## Task 3 — Crear `tbl_platform_role`

- [x] 3.1 Crear modelo ORM `PlatformRole`.
- [x] 3.2 Crear schemas `PlatformRoleBase`, `PlatformRoleCreate`, `PlatformRoleUpdate`, `PlatformRoleRead`.
- [x] 3.3 Crear migración `0004_create_tbl_platform_role`.
- [x] 3.4 Definir constraint `pk_tbl_platform_role`.
- [x] 3.5 Añadir tests metadata.
- [x] 3.6 Ejecutar validación.

## Task 4 — Crear `tbl_organization_role`

- [x] 4.1 Crear modelo ORM `OrganizationRole`.
- [x] 4.2 Crear schemas `OrganizationRoleBase`, `OrganizationRoleCreate`, `OrganizationRoleUpdate`, `OrganizationRoleRead`.
- [x] 4.3 Crear migración `0005_create_tbl_organization_role`.
- [x] 4.4 Definir constraint `pk_tbl_organization_role`.
- [x] 4.5 Añadir tests metadata.
- [x] 4.6 Ejecutar validación.

# Task 4b — Anexo técnico Alembic version_num

## Objetivo

Resolver el límite por defecto de `alembic_version.version_num VARCHAR(32)` para permitir revision IDs descriptivas.

## Contexto

Durante `make db-upgrade`, la revisión `0005_create_tbl_organization_role` superó el límite de 32 caracteres.

## Cambios incluidos

- [x] 4b.1 Ampliar `alembic_version.version_num` a `VARCHAR(255)` desde `0001_create_schema_iam.py`.
- [x] 4b.2 Añadir test que valida la corrección.
- [x] 4b.3 Documentar que el downgrade no reduce la columna para evitar romper histórico Alembic.
- [x] 4b.4 Validar `make backend-check`, `make docker-config`, `make db-history`.

## Seguridad

- No se crean tablas IAM nuevas.
- No se crean migraciones nuevas.
- No se añaden seeds.
- No se modifican `.env`, `frontend/` ni `docker-compose.yml`.
- No se añaden secretos reales.

## Decisión de downgrade

El `downgrade()` no reduce `alembic_version.version_num` a `VARCHAR(32)`, porque
podría truncar revision IDs descriptivas ya registradas y dejar Alembic en un
estado inconsistente.

## Task 5 — Crear `tbl_state`

- [x] 5.1 Crear modelo ORM `State`.
- [x] 5.2 Crear schemas `StateBase`, `StateCreate`, `StateUpdate`, `StateRead`.
- [x] 5.3 Crear migración `0006_create_tbl_state`.
- [x] 5.4 Añadir FK `id_country → sch_iam.tbl_country.id_country`.
- [x] 5.5 Añadir índice `ix_tbl_state_id_country`.
- [x] 5.6 Añadir tests metadata.
- [x] 5.7 Ejecutar validación.

## Task 6 — Crear `tbl_city`

- [x] 6.1 Crear modelo ORM `City`.
- [x] 6.2 Crear schemas `CityBase`, `CityCreate`, `CityUpdate`, `CityRead`.
- [x] 6.3 Crear migración `0007_create_tbl_city`.
- [x] 6.4 Añadir FK `id_state → sch_iam.tbl_state.id_state`.
- [x] 6.5 Añadir índice `ix_tbl_city_id_state`.
- [x] 6.6 Añadir tests metadata.
- [x] 6.7 Ejecutar validación.

## Task 7 — Servicios de aplicación IAM

- [ ] Añadir servicios internos de casos de uso mínimos.
- [ ] Evitar lógica de endpoint en servicios.
- [ ] Añadir tests de reglas de negocio.

## Task 8 — Schemas Pydantic públicos/controlados

- [ ] Definir schemas de entrada/salida necesarios.
- [ ] Validar inputs server-side.
- [ ] Añadir tests de validación.

## Task 9 — Endpoints administrativos IAM mínimos

- [ ] Implementar endpoints acordados por arquitectura.
- [ ] Aplicar autorización y tenant context.
- [ ] Añadir tests HTTP.

## Task 10 — Auditoría IAM

- [ ] Registrar eventos auditables relevantes.
- [ ] Añadir tests de emisión de eventos.

## Task 11 — Integración con autenticación

- [ ] Conectar IAM con autenticación cuando el diseño esté aprobado.
- [ ] No introducir secretos en repositorio.
- [ ] Añadir tests de seguridad.

## Task 12 — Hardening multi-tenant

- [ ] Revisar queries por `organization_id`.
- [ ] Añadir tests de acceso cruzado denegado.
- [ ] Documentar decisiones de aislamiento.

## Task 13 — Documentación operativa IAM

- [ ] Documentar migraciones, rollback y criterios de QA.
- [ ] Documentar decisiones técnicas backend.

## Task 14 — Validación final de roadmap IAM

- [ ] Ejecutar checks completos.
- [ ] Revisar migraciones acumuladas.
- [ ] Preparar resumen para PR y QA.
