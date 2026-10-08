# feature/BACK-AUTH-OAUTH2-007-csrf

## Objetivo

Implementar y documentar una protección CSRF básica para sesiones autenticadas mediante cookie HttpOnly `guak_access_token`, empezando por `POST /api/v1/auth/logout` como primera mutación autenticada protegida.

## Cambios realizados

- Añadido `GET /api/v1/auth/csrf` para emitir un token CSRF firmado ligado al access token actual.
- `POST /api/v1/auth/logout` ahora requiere cookie de acceso válida y header `X-CSRF-Token` válido.
- Login y registro siguen excluidos de CSRF por ser flujos públicos de bootstrap en esta fase.
- `GET /api/v1/auth/me` no requiere CSRF porque es una operación de lectura.
- No se ha añadido middleware global; la protección se aplica mediante una dependencia explícita reutilizable.
- Se han documentado los componentes backend implicados:
  - `csrf_schemas.py`: contrato de respuesta.
  - `csrf_services.py`: emisión y validación del token CSRF.
  - `csrf_dependencies.py`: dependencia `require_valid_csrf_token` y validación de la cookie de acceso.
  - `csrf_routers.py`: endpoint `/csrf`.
  - `csrf_exceptions.py`: excepción controlada.
  - `logout_routers.py`: protegido ahora con `require_valid_csrf_token`.

## Justificacion tecnica

La autenticación basada en cookie HttpOnly reduce la exposición del access token al JavaScript del navegador, pero introduce riesgo CSRF en mutaciones autenticadas porque el navegador adjunta la cookie automáticamente. Por ese motivo se añade un token CSRF separado que el cliente debe solicitar de forma autenticada y reenviar explícitamente en la cabecera `X-CSRF-Token`.

El token CSRF es un JWT firmado server-side con `type = "csrf"` y claims mínimos `sub`, `access_jti`, `iat` y `exp`. La expiración se toma del access token, por lo que el token CSRF no vive más que la sesión. La validación compara el `sub` y el `jti` del access token actual con los datos del token CSRF, evitando reutilización entre sesiones distintas.

## Decisiones tomadas

- No se persiste el token CSRF en base de datos en esta task.
- No se expone el access token en la respuesta de `/csrf`.
- No se exponen usuario, email, roles, IDs internos ni `organization_id`.
- No se acepta `organization_id` desde frontend.
- Los errores de autenticación se mantienen genéricos: `No autenticado.`.
- Los errores CSRF se mantienen genéricos: `CSRF inválido.`.
- Logout deja de ser idempotente sin cookie/header porque ahora es una mutación autenticada protegida.
- Futuras mutaciones autenticadas deben añadir explícitamente la dependencia CSRF.
- CORS, refresh tokens, `/auth/token`, RBAC/roles y rate limiting quedan fuera de esta tarea.

## Tests ejecutados

```bash
make backend-quality
make backend-test-unit
make backend-test-db
```

Resultados documentados:

- `make backend-quality` ✅ PASS.
- `make backend-test-unit` ✅ PASS: `347 passed, 63 deselected`.
- `make backend-test-db` ✅ PASS: `41 passed, 369 deselected`.
- QA final ✅ PASS.

Aviso conocido: warnings de PyJWT por secretos de test de 30 bytes. Se considera deuda no bloqueante para esta task.

## Riesgos o deuda tecnica

- La protección CSRF es manual por dependencia; futuras mutaciones autenticadas deben revisarse para no quedar sin protección.
- No hay revocación ni persistencia server-side de tokens CSRF.
- Faltan tests HTTP adicionales opcionales para cookie inválida/expirada, CSRF malformado y header vacío.
- No se ha implementado auditoría específica para fallos CSRF.
- CORS queda fuera si no está implementado en esta task.
- `/auth/token`, refresh tokens, RBAC/roles y rate limiting quedan fuera.

## Relacion con el backend

El cambio afecta directamente al módulo backend de autenticación OAuth2 con sesiones por cookie HttpOnly. Refuerza la seguridad de mutaciones autenticadas, mantiene la lógica crítica en servidor y deja una dependencia reutilizable para proteger endpoints futuros sin modificar frontend ni infraestructura.
