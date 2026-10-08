# feature/BACK-AUTH-OAUTH2-005-auth-me

## Objetivo

Documentar la Task 5 de OAuth2, centrada en exponer la consulta de identidad autenticada mediante el endpoint `GET /api/v1/auth/me` usando la cookie `HttpOnly` de sesión.

El objetivo funcional es permitir que el backend confirme si una petición corresponde a un usuario autenticado, activo y perteneciente a la organización indicada por el JWT, sin delegar esa validación en el frontend.

## Cambios realizados

- Se documenta el endpoint `GET /api/v1/auth/me`.
- El endpoint lee la cookie `HttpOnly` `guak_access_token` usando `AuthSettings.auth_cookie_name`.
- Se valida el JWT de tipo access token.
- Se verifica que el usuario existe, está activo y pertenece a la organización incluida en el claim `org`.
- Se devuelve una identidad pública mínima:

```json
{
  "authenticated": true,
  "user_id": "usr_<uuid-v4>",
  "organization_id": "org_<uuid-v4>"
}
```

- Se mapean a `401` los casos de ausencia de cookie, token inválido o expirado, token con `type` incorrecto, ausencia del claim `org`, usuario inexistente, usuario inactivo u organización no coincidente con la base de datos.
- Se amplía la documentación global de OAuth2 con el contrato y las decisiones de seguridad de esta tarea.

## Justificacion tecnica

`/auth/me` es el primer endpoint protegido que consume la cookie `HttpOnly` emitida por el login. La validación se realiza en backend para mantener la lógica crítica fuera del navegador y evitar que el cliente pueda decidir por sí mismo qué usuario u organización está autenticado.

La resolución de identidad exige la combinación `sub + org` contra PostgreSQL. Esto evita resolver un usuario únicamente por `sub` y refuerza el aislamiento multiempresa definido para el MVP.

## Decisiones tomadas

- No se expone el token en ninguna respuesta.
- No se expone el email completo.
- No se expone `password_hash`.
- No se exponen IDs internos de base de datos.
- No se exponen roles todavía.
- No se acepta `organization_id` ni ningún otro identificador enviado desde frontend.
- Se valida `sub + org` contra PostgreSQL.
- `JwtAccessTokenService.verify_access_token` devuelve ahora `organization` de forma opcional y retrocompatible.
- `/auth/me` exige que el claim `org` exista aunque la ampliación del servicio JWT sea opcional para no romper usos previos.

Arquitectura documentada:

- `me_schemas.py`: response público mínimo.
- `me_services.py`: validación del token y resolución de identidad.
- `me_repositories.py`: consulta SQLAlchemy por public IDs y estado activo.
- `me_routers.py`: lectura de cookie y mapeo HTTP `401`.
- `me_exceptions.py`: error controlado de autenticación.
- `tokens.py`: `VerifiedAccessToken` ampliado con `organization`.
- Router incluido bajo `/api/v1/auth`.

## Tests ejecutados

- `make backend-quality` ✅ PASS.
- `make backend-test-unit` ✅ PASS: `333 passed, 63 deselected`.
- `make backend-test-db` ✅ PASS: `41 passed, 355 deselected`.
- QA final ✅ PASS.

## Riesgos o deuda tecnica

- Auditoría `AUTH_ME_SUCCESS` / `AUTH_ME_FAILED` no implementada todavía.
- Los tests HTTP no cubren override de nombre de cookie, aunque la implementación usa settings.
- Las fixtures DB compartidas podrían extraerse a `conftest.py` en una futura limpieza.
- `/auth/logout`, `/auth/csrf`, `/auth/token`, RBAC/roles y rate limiting quedan fuera de esta task.

## Relacion con el backend

Este cambio consolida el flujo OAuth2 iniciado con registro y login, permitiendo al backend resolver la identidad autenticada desde una cookie `HttpOnly` sin exponer secretos al cliente. También prepara la base para rutas protegidas, tenant context y controles RBAC posteriores, manteniendo la validación de usuario y organización en PostgreSQL.
