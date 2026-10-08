# feature/BACK-AUTH-OAUTH2-004-login-cookie

## Objetivo

Documentar la Task 4 de OAuth2: implementación del login backend mediante el endpoint `POST /api/v1/auth/login`, autenticación por `email` y `password`, y entrega del JWT access token exclusivamente mediante cookie `HttpOnly`.

El objetivo de seguridad es evitar que el token quede expuesto en el cuerpo de la respuesta HTTP o accesible desde JavaScript, manteniendo un contrato de respuesta mínimo y explícito.

## Cambios realizados

- Se documenta el endpoint de login:

```http
POST /api/v1/auth/login
Content-Type: application/json
```

- Request esperado:

```json
{
  "email": "ana@empresa.com",
  "password": "PasswordSeguro123!"
}
```

- Response `200 OK` esperado:

```json
{
  "status": "authenticated"
}
```

- La respuesta no incluye token en el body.
- El JWT access token se emite únicamente en la cookie `guak_access_token`.
- La cookie se configura con:
  - `HttpOnly`.
  - `Path=/api`.
  - `SameSite` desde settings.
  - `Secure` desde settings.
  - `Max-Age` coherente con la expiración del access token.

### Organización de la implementación

- `auth/dependencies.py`: factory compartida `build_auth_settings`.
- `login_schemas.py`: request, response y DTO interno.
- `login_repositories.py`: consulta SQLAlchemy de usuario por email.
- `login_services.py`: validación de credenciales, auditoría conceptual y emisión del token.
- `login_routers.py`: endpoint HTTP y configuración de `set-cookie`.
- `login_exceptions.py`: error controlado para credenciales inválidas.
- `tokens.py`: ampliación retrocompatible de `issue_access_token(..., organization=...)`.

Además, el login ya no depende del router de registro. El registro también pasa a usar la dependency común de autenticación.

## Justificacion tecnica

El token se entrega mediante cookie `HttpOnly` para reducir la exposición frente a accesos desde JavaScript y evitar que el contrato HTTP devuelva credenciales reutilizables en el cuerpo de la respuesta.

La separación entre router, schemas, repositorio, servicio y excepciones mantiene el endpoint fino, permite probar la lógica de autenticación sin acoplarla a FastAPI y encapsula la consulta SQLAlchemy en una pieza específica.

La configuración compartida `build_auth_settings` evita duplicidad entre registro y login, y mantiene una política única para parámetros sensibles como `jwt_secret_key`, cookies y expiración del token.

## Decisiones tomadas

- No devolver el access token en el body.
- Devolver únicamente `{ "status": "authenticated" }` en login correcto.
- No exponer `password_hash`, IDs internos, roles ni claims sensibles.
- Usar errores genéricos `Credenciales inválidas.` para usuario inexistente, password incorrecto o usuario inactivo.
- Mantener request strict con `extra="forbid"`.
- No aceptar `organization_id` en la request de login.
- Mantener `jwt_secret_key` obligatorio y sin fallback inseguro.
- Emitir JWT con claims mínimos:
  - `sub`: public user ID `usr_...`.
  - `org`: public organization ID `org_...`.
  - `type`.
  - `jti`.
  - `iat`.
  - `exp`.
- No incluir IDs internos ni roles dentro del token.

## Tests ejecutados

- `make backend-quality` — PASS.
- `make backend-test-unit` — PASS (`325 passed, 59 deselected`).
- `make backend-test-db` — PASS (`37 passed, 347 deselected`).
- QA final — PASS.

No se han documentado pruebas de frontend dentro de esta task.

## Riesgos o deuda tecnica

- `NoOpLoginAuditAdapter`: la auditoría persistente queda pendiente.
- Rate limiting y protección anti fuerza bruta pendientes antes de exposición pública.
- `auth_cookie_secure=False` por defecto es aceptable en desarrollo, pero debe ser `true` en staging/producción con TLS.
- `/auth/me`, `/auth/logout`, `/auth/csrf` y `/auth/token` quedan fuera de esta task.
- Si en el futuro una cuenta puede pertenecer a múltiples organizaciones activas, habrá que rediseñar la selección de organización y el tenant context del login.

## Relacion con el backend

Este cambio afecta directamente al backend porque introduce el flujo de autenticación HTTP inicial. Completa la fase posterior al registro permitiendo que un usuario existente se autentique y reciba un access token de forma controlada, sin delegar lógica crítica al frontend y manteniendo el aislamiento conceptual mediante public IDs de usuario y organización.
