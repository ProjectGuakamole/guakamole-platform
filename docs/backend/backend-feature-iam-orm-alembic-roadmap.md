# Roadmap backend — IAM ORM/Pydantic/PostgreSQL/Alembic

Branch esperada: `backend/feature/iam-orm-alembic`

Schema PostgreSQL IAM: `sch_iam`

Estado: Task 2 completada y preparada para revisión QA.

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

## Task 3 — Modelado base de usuarios

- [ ] Definir modelos ORM de usuario sin autenticación JWT.
- [ ] Añadir migración incremental.
- [ ] Añadir schemas Pydantic internos.
- [ ] Añadir tests de unicidad y tipos.

## Task 4 — Modelado de departamentos y pertenencia organizativa

- [ ] Definir modelos ORM de departamentos y relaciones necesarias.
- [ ] Añadir migración incremental.
- [ ] Añadir tests de claves foráneas y constraints.

## Task 5 — Roles y permisos IAM

- [ ] Definir modelos ORM de roles y asignaciones.
- [ ] Mantener RBAC multi-rol por usuario.
- [ ] Añadir migración incremental.
- [ ] Añadir tests de constraints de autorización base.

## Task 6 — Repositorios IAM internos

- [ ] Añadir repositorios ORM sin endpoints públicos.
- [ ] Mantener consultas acotadas por tenant cuando aplique.
- [ ] Añadir tests unitarios.

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
