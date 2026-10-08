# feature/BACK-AUTH-OAUTH2-006-logout

## Objetivo

Documentar la Task 6 de OAuth2/Auth: cierre de sesión mediante el endpoint `POST /api/v1/auth/logout`, eliminando la cookie `HttpOnly` `guak_access_token` del navegador.

El objetivo funcional es permitir que el cliente cierre la sesión local del navegador sin exponer tokens ni depender de datos enviados por el frontend.

## Cambios realizados

- Se documenta el endpoint `POST /api/v1/auth/logout` bajo `/api/v1/auth`.
- El endpoint no recibe body.
- La cookie `guak_access_token` es opcional.
- La respuesta esperada es siempre `200 OK` con cuerpo mínimo:

```json
{
  "status": "logged_out"
}
```

- El cierre de sesión se realiza mediante cabecera `Set-Cookie` para eliminar la cookie de autenticación.
- La cookie a borrar usa:
  - nombre desde `AuthSettings.auth_cookie_name`;
  - `path` desde settings, `/api` por defecto;
  - `domain` si aplica;
  - `SameSite` desde settings;
  - `Secure` desde settings;
  - `HttpOnly=true`;
  - `Max-Age=0` o expiración pasada.
- La arquitectura documentada queda separada en:
  - `logout_schemas.py`: response mínimo;
  - `logout_routers.py`: endpoint fino, idempotente y responsable de borrar la cookie.
- No se crea un servicio específico porque no existe lógica de dominio compleja en esta task.

## Justificacion tecnica

El logout se implementa como una operación idempotente porque su responsabilidad es limpiar el estado de sesión del navegador. Por ello devuelve `200 OK` aunque no exista la cookie, el token esté expirado o el token sea inválido.

No validar el JWT evita acoplar el cierre local de sesión a un estado de autenticación todavía válido. Un usuario debe poder pedir al backend que elimine la cookie aunque el token ya no sea usable.

Reutilizar los settings de cookie del login evita discrepancias entre la cookie emitida y la cookie borrada, especialmente en atributos como `path`, `domain`, `SameSite` y `Secure`.

## Decisiones tomadas

- El endpoint no devuelve token.
- El endpoint no devuelve usuario, email, roles, IDs internos ni `organization_id`.
- No acepta `organization_id` ni ningún dato procedente del frontend.
- No valida JWT porque su responsabilidad es borrar la cookie del navegador.
- Mantiene una respuesta mínima para reducir filtraciones de información.
- No revoca server-side el JWT en esta task.
- Se asume como limitación consciente que un token copiado fuera de la cookie seguiría siendo válido hasta su expiración.

## Tests ejecutados

- `make backend-quality` PASS.
- `make backend-test-unit` PASS: `337 passed, 63 deselected`.
- `make backend-test-db` PASS: `41 passed, 359 deselected`.
- QA final PASS.

## Riesgos o deuda tecnica

- Auditoría `LOGOUT` no implementada todavía.
- Sin blacklist ni revocación server-side de JWT.
- Podría añadirse un test de body arbitrario como mejora no bloqueante.
- Podría añadirse un test explícito sobre `expires` como mejora no bloqueante.
- `/auth/csrf`, `/auth/token`, refresh tokens, RBAC/roles y rate limiting quedan fuera de esta task.

## Relacion con el backend

Este cambio completa el flujo básico de sesión basado en cookie `HttpOnly` junto con login y consulta de identidad autenticada. El backend asume la responsabilidad de emitir y eliminar la cookie de autenticación, manteniendo fuera del frontend la gestión directa del access token.

La task no introduce revocación persistente ni lógica de autorización nueva, pero prepara una base coherente para futuras mejoras de auditoría, refresh tokens, CSRF, RBAC y políticas de sesión.
