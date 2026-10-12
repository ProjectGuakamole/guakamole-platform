# feature/BACK-AUTH-OAUTH2-008-token

## Objetivo

Documentar la Task 8 de OAuth2/Auth: incorporación del endpoint `POST /api/v1/auth/token` para permitir el flujo OAuth2 Password Bearer usado por Swagger y entornos de desarrollo.

El objetivo funcional es ofrecer un contrato compatible con `OAuth2PasswordBearer` sin cambiar el flujo principal de sesión basado en cookie `HttpOnly`.

## Cambios realizados

- Se añade el endpoint `POST /api/v1/auth/token` bajo `/api/v1/auth`.
- El endpoint acepta `application/x-www-form-urlencoded` con los campos `username` y `password`.
- Se transforma el formulario OAuth2 a `LoginRequest` y se reutiliza `LoginService`.
- La respuesta devuelve un bearer token en el body:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 900
}
```

- No se emite ni modifica ninguna cookie.
- No requiere CSRF porque no utiliza autenticación basada en cookie.
- Se puede deshabilitar mediante `AUTH_ENABLE_PASSWORD_BEARER_TOKEN=false`.
- Se añade la dependencia `python-multipart` necesaria para formularios FastAPI.

## Justificacion tecnica

Swagger/OpenAPI necesita un endpoint compatible con OAuth2 Password Bearer para facilitar pruebas de endpoints protegidos durante desarrollo. En lugar de crear una lógica de autenticación paralela, el endpoint reutiliza el caso de uso existente de login, manteniendo una única validación de credenciales y una única política de emisión de access tokens.

El uso de `application/x-www-form-urlencoded` responde al contrato estándar de `OAuth2PasswordRequestForm` en FastAPI. La transformación del formulario se mantiene en la capa HTTP para no contaminar el servicio de aplicación con detalles propios del adaptador web.

## Decisiones tomadas

- No emitir `Set-Cookie` desde `/auth/token`.
- No modificar cookies existentes.
- No exponer email, roles, `organization_id`, `user_id` ni `password_hash` en la respuesta.
- No aceptar `organization_id` ni tenant desde frontend.
- Mantener `OAuth2PasswordRequestForm` únicamente en el router/adaptador HTTP.
- Calcular `expires_in` a partir de `AuthSettings.access_token_expire_minutes`.
- Si `AUTH_ENABLE_PASSWORD_BEARER_TOKEN=false`, bloquear el endpoint antes de autenticar credenciales.
- Considerar el endpoint como herramienta para Swagger/desarrollo; fuera de desarrollo se recomienda deshabilitarlo.
- Mantener rate limiting como deuda pendiente antes de exposición pública.

## Tests ejecutados

- `make backend-quality` PASS.
- `make backend-test-unit` PASS: `352 passed, 63 deselected`.
- `make backend-test-db` PASS: `41 passed, 374 deselected`.
- QA final PASS.

Aviso conocido: warnings de PyJWT por secretos de test de 30 bytes. Se documenta como deuda no bloqueante y no introducida por esta task.

## Riesgos o deuda tecnica

- `AUTH_ENABLE_PASSWORD_BEARER_TOKEN=True` por defecto; en entornos no-dev debe configurarse explícitamente a `false` si no se desea exponer.
- Sin rate limiting todavía.
- Sin auditoría persistente real todavía; se reutiliza la auditoría conceptual de `LoginService`.
- Tests adicionales opcionales: JSON incorrecto `422`, campos extra `organization_id`/`tenant`, y `expires_in` con settings distinto.
- Refresh tokens, RBAC/roles, CORS y frontend quedan fuera del alcance.

## Relacion con el backend

El cambio añade un contrato HTTP backend orientado a desarrollo y documentación interactiva, sin alterar el modelo principal de sesión con cookie `HttpOnly`. Refuerza la reutilización de servicios internos de autenticación y mantiene separada la capa de transporte OAuth2 form del caso de uso de login.

### Contrato HTTP

Request:

```http
POST /api/v1/auth/token
Content-Type: application/x-www-form-urlencoded

username=ana@empresa.com&password=PasswordSeguro123!
```

Response `200 OK`:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 900
}
```

Response `401 Unauthorized`:

```json
{
  "detail": "Credenciales inválidas."
}
```

Response `403 Forbidden` si está deshabilitado:

```json
{
  "detail": "Endpoint OAuth2 deshabilitado."
}
```
