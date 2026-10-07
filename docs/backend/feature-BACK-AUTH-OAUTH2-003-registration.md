# feature/BACK-AUTH-OAUTH2-003-registration

## Objetivo

Documentar la implementación del registro inicial OAuth2 mediante el endpoint `POST /api/v1/organizations/register`.

El objetivo funcional es permitir crear una organización y su primer usuario desde backend, dejando el sistema preparado para fases posteriores de login, emisión de sesión y cookies, sin entregar credenciales ni tokens en el registro.

## Cambios realizados

- Se documenta el contrato HTTP del endpoint de registro inicial:

```http
POST /api/v1/organizations/register
Content-Type: application/json
```

Request esperado:

```json
{
  "organization_name": "ACME SOC",
  "admin_email": "admin@acme.example",
  "admin_password": "ChangeMe123!",
  "admin_display_name": "Admin ACME"
}
```

Response esperado en alta correcta:

```json
{
  "organization": {
    "public_id": "org_...",
    "name": "ACME SOC"
  },
  "user": {
    "public_id": "usr_...",
    "email": "admin@acme.example",
    "display_name": "Admin ACME"
  }
}
```

- Se documenta la organización modular de la implementación backend:
  - `schemas` para validación y contrato HTTP.
  - `router` para exponer `POST /api/v1/organizations/register`.
  - `service` para la lógica de caso de uso, testable sin FastAPI.
  - `repository` para encapsular el acceso a SQLAlchemy.
  - `exceptions` para errores de dominio/aplicación traducibles a HTTP.
- Se documenta la migración asociada a identificadores públicos y secuencias internas.

## Justificacion tecnica

El registro se ha separado en capas para evitar que el router concentre lógica de negocio, persistencia y validación. Esta separación permite probar el servicio de registro de forma aislada, sin depender del framework HTTP, y mantiene SQLAlchemy encapsulado en el repositorio.

La respuesta usa identificadores públicos `org_...` y `usr_...` para no exponer IDs internos de base de datos. Esto reduce acoplamiento con la implementación de persistencia y evita filtrar información innecesaria sobre secuencias internas.

El password se hashea con el Auth Core existente, reutilizando el componente de autenticación ya validado en la fase anterior. La configuración `jwt_secret_key` sigue siendo obligatoria y no tiene fallback, aunque este endpoint no emita tokens, para mantener una política estricta de configuración de seguridad.

## Decisiones tomadas

- El endpoint de registro no devuelve token de acceso.
- El endpoint de registro no inicia sesión ni crea cookie.
- No se exponen IDs internos de `organization` ni `user`.
- Se devuelven únicamente public IDs con prefijos `org_...` y `usr_...`.
- Los errores de duplicado se presentan de forma genérica para no facilitar enumeración de organizaciones o usuarios.
- El hashing de contraseña se delega en Auth Core.
- `jwt_secret_key` continúa siendo obligatorio y sin fallback inseguro.
- La migración define `public_id` único y no nulo para `organization` y `user`.
- Los IDs internos usan secuencias de base de datos con rango alto reservado `1000000000`, evitando estrategias frágiles basadas en `MAX(id)+1`.

## Tests ejecutados

- `make backend-quality` — PASS.
- `make backend-test-unit` — PASS (`313 passed, 56 deselected`).
- `make backend-test-db` — PASS tras levantar PostgreSQL (`34 passed`), según ejecución previa del implementer.
- QA final — PASS.

No se han ejecutado ni documentado pruebas de frontend dentro de esta task.

## Riesgos o deuda tecnica

- La base de datos local del entorno quedó contaminada con una revisión antigua de Alembic: `0014_add_iam_registration_id_sequences`. Por ello, la validación de la migración debe repetirse en una base de datos limpia o en CI.
- El rate limiting del endpoint de registro queda pendiente fuera del alcance de esta task.
- El registro no implementa login, emisión de token ni cookie de sesión.

## Relacion con el backend

Este cambio afecta directamente al backend porque introduce el primer flujo HTTP de registro de organización y usuario administrador. Refuerza la base de autenticación OAuth2 sin completar todavía el login, manteniendo decisiones de seguridad coherentes con el modelo de dominio: aislamiento por organización, public IDs, hashing server-side y ausencia de secretos o lógica crítica en cliente.
