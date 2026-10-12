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

### Cierre funcional Task 3

- El endpoint `POST /api/v1/organizations/register` ha sido validado manualmente desde Swagger tras la corrección de los problemas de entorno detectados después del merge del PR #29.
- El registro crea correctamente una organización y su primer usuario administrador.
- La request no envía IDs internos: únicamente incluye nombre de organización, email, contraseña y nombre visible del administrador.
- La base de datos genera los IDs internos automáticamente mediante secuencia.
- La respuesta devuelve identificadores públicos con formato `org_...` y `usr_...`.
- Los IDs internos observados empiezan en el rango alto `1000000000` por decisión explícita de migración, no por un error de autoincremento.
- El frontend o cualquier cliente HTTP no debe depender de IDs internos. Su contrato estable debe basarse en los public IDs devueltos por la API.

### Problemas encontrados durante testeo manual y solución

1. `/api/ready` devolvía `not_ready`.
   - Motivo: el readiness probe de base de datos todavía no implementa una comprobación real tipo `SELECT 1` y actualmente falla cerrado por diseño.
   - Impacto: no bloquea el endpoint de registro ni impide que `POST /api/v1/organizations/register` funcione.
   - Solución: se deja documentado como deuda técnica y se debe crear un ticket futuro para implementar readiness real contra PostgreSQL.

2. Swagger devolvía `500 Internal Server Error` al ejecutar `POST /api/v1/organizations/register`.
   - Primer problema detectado: `DATABASE_URL` no estaba disponible dentro del contenedor backend.
   - Solución aplicada: pasar `DATABASE_URL` y `JWT_SECRET_KEY` al servicio backend en `docker-compose.yml`.

3. Diferencia entre host y Docker para `DATABASE_URL`.
   - Para comandos Make ejecutados desde el host, como `make db-current` o `make backend-seed`, la URL debe usar `localhost`.
   - Para el backend ejecutándose dentro de Docker, la URL debe usar el nombre del servicio `postgres`.
   - Solución documentada:

```dotenv
DATABASE_URL=postgresql+psycopg://guakamole_user:postgre@localhost:5432/guakamole_db
```

```yaml
DATABASE_URL: postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
```

4. `backend-seed` fallaba tras la migración `0013`.
   - Motivo: `public_id` es ahora `NOT NULL` en `tbl_organization` y `tbl_users`, pero el seed demo insertaba registros sin `public_id`.
   - Solución aplicada: actualizar `backend/scripts/seed_demo_iam.py` para insertar `public_id` con prefijos `org_` / `usr_` y `gen_random_uuid()`.
   - Validación realizada:
     - `make backend-seed ENV_FILE=.env.example` — OK tras el fix.
     - `make backend-seed-clear ENV_FILE=.env.example` — OK tras el fix.
     - Nueva ejecución de `make backend-seed ENV_FILE=.env.example` — OK tras el fix.

5. `requirements.txt` y Docker.
   - Motivo: Docker instala dependencias desde `backend/requirements.txt`; inicialmente faltaban dependencias nuevas `pwdlib`/`pyjwt`.
   - Solución: regenerar/actualizar `backend/requirements.txt` para incluirlas.
   - Estado: quedó incluido en el PR #29.

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
- `make backend-test-db` — PASS (`34 passed, 335 deselected`).
- `make db-current ENV_FILE=.env.example` — PASS, revisión actual `0013_registration_public_ids (head)`.
- `curl /api/health` — PASS, `200 OK`.
- `POST /api/v1/organizations/register` desde Swagger — PASS, `201 Created`.
- `make backend-seed ENV_FILE=.env.example` — PASS tras corregir `public_id` en el seed demo.
- `make backend-seed-clear ENV_FILE=.env.example` — PASS tras corregir `public_id` en el seed demo.
- QA final — PASS.

No se han ejecutado ni documentado pruebas de frontend dentro de esta task.

## Riesgos o deuda tecnica

- Implementar readiness real contra PostgreSQL mediante una comprobación tipo `SELECT 1`.
- Implementar auditoría persistente para los eventos `ORGANIZATION_REGISTERED` y `USER_REGISTERED`.
- Añadir rate limiting del registro antes de exponerlo en un entorno público o staging real.
- Valorar renombrar la respuesta a `organization_public_id` / `user_public_id` si se quiere evitar ambigüedad futura.
- El registro no implementa login, emisión de token ni cookie de sesión.

## Relacion con el backend

Este cambio afecta directamente al backend porque introduce el primer flujo HTTP de registro de organización y usuario administrador. Refuerza la base de autenticación OAuth2 sin completar todavía el login, manteniendo decisiones de seguridad coherentes con el modelo de dominio: aislamiento por organización, public IDs, hashing server-side y ausencia de secretos o lógica crítica en cliente.
