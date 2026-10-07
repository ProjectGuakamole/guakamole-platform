# BACK-AUTH-OAUTH2-001 — Diseño técnico OAuth2

**Estado:** Diseño definido para revisión  
**Ámbito:** `backend/`  
**Carpeta:** `docs/backend/oauth2/`  
**Referencia:** https://fastapi.tiangolo.com/es/tutorial/security/oauth2-jwt/

## 1. Objetivo técnico

Diseñar la fase backend de registro inicial, login OAuth2 y sesión segura de Project Guakamole con código modular, testeable y alineado con seguridad profesional para MVP.

La fase debe permitir:

1. registrar una organización y su primer usuario administrador;
2. almacenar passwords exclusivamente como hash Argon2id;
3. autenticar usuarios por email/password;
4. usar cookie HttpOnly como flujo principal del frontend;
5. mantener endpoint OAuth2 Password Bearer para Swagger/desarrollo;
6. exponer sesión mínima con `/auth/me` sin roles ni datos sensibles;
7. aplicar CORS con credenciales y CSRF básico;
8. evitar exposición de IDs internos mediante `public_id`.

## 2. Principios de seguridad

- El frontend no almacena access tokens en `localStorage` ni `sessionStorage`.
- El login principal setea cookie HttpOnly.
- El token no se devuelve al frontend principal.
- Los roles no se exponen en `/auth/me`.
- Los IDs internos incrementales no se exponen en responses públicas de auth.
- Toda autorización futura se resolverá en backend desde identidad validada/DB, nunca desde datos enviados por el cliente.
- CORS no usa wildcard.
- CSRF se valida en mutaciones autenticadas.
- No se loguean passwords, hashes, tokens, CSRF tokens ni secretos.

## 3. Integración con estructura actual

Estructura relevante:

```text
backend/app/
├── api/v1/router.py
├── main.py
├── domain/auth/                 # nuevo módulo auth
├── domain/iam/organizations/    # registro inicial
├── domain/iam/users/models.py
├── domain/iam/organizations/models.py
└── db/base.py
```

Modelos existentes a reutilizar:

- `Organization`;
- `User`;
- catálogos IAM de status, roles, país, provincia y ciudad;
- sesión SQLAlchemy existente.

Migraciones previstas:

- `tbl_users.public_id` único;
- `tbl_organization.public_id` único.

## 4. Módulos propuestos

### 4.1 Auth

```text
app/domain/auth/
├── __init__.py
├── audit.py
├── config.py
├── cookies.py
├── csrf.py
├── exceptions.py
├── password_hasher.py
├── repositories.py
├── routers.py
├── schemas.py
├── services.py
├── token_issuer.py
└── token_verifier.py
```

Responsabilidades:

- login frontend cookie;
- endpoint OAuth2 `/auth/token`;
- logout;
- `/auth/me`;
- CSRF;
- password verification;
- token issuing;
- token verification mínima para cookie, `/auth/me`, `/auth/logout` y CSRF;
- auditoría auth.

### 4.2 Registro de organización

```text
app/domain/iam/organizations/
├── registration_repositories.py
├── registration_routers.py
├── registration_schemas.py
└── registration_services.py
```

Responsabilidades:

- registro público de organización;
- primer usuario administrador;
- resolución de catálogos;
- public IDs;
- auditoría de registro.

## 5. Configuración prevista

Variables sin secretos reales en `.env.example`:

```text
ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_SECRET_KEY=
JWT_ALGORITHM=HS256
AUTH_COOKIE_NAME=guak_access_token
AUTH_COOKIE_PATH=/api
AUTH_COOKIE_DOMAIN=
AUTH_COOKIE_HTTPONLY=true
AUTH_COOKIE_SECURE=false
AUTH_COOKIE_SAMESITE=lax
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_AUTHORIZATION_HEADER=true
AUTH_ENABLE_PASSWORD_BEARER_TOKEN=true
DEFAULT_REGISTERED_ORGANIZATION_STATUS=ACTIVE
DEFAULT_REGISTERED_USER_STATUS=ACTIVE
DEFAULT_PLATFORM_ROLE=PLATFORM_USER
DEFAULT_ORGANIZATION_ROLE=COMPANY_ADMIN
```

Reglas:

- `JWT_SECRET_KEY` solo por entorno, nunca valor real en Git.
- `AUTH_COOKIE_SECURE=false` solo local; `true` en staging/prod con HTTPS.
- `CORS_ALLOW_AUTHORIZATION_HEADER=true` en dev; `false` recomendado en prod si el frontend solo usa cookie.

## 6. Contratos HTTP

### 6.1 Registro inicial

```http
POST /api/v1/organizations/register
Content-Type: application/json
```

Response `201 Created`:

```json
{
  "organization_id": "org_550e8400-e29b-41d4-a716-446655440000",
  "user_id": "usr_1f7e9f1a-1c25-46a8-9f15-8f8d0f4d2f3",
  "organization_status": "ACTIVE",
  "user_status": "ACTIVE"
}
```

No devuelve token ni IDs internos.

### 6.2 Login frontend seguro

```http
POST /api/v1/auth/login
Content-Type: application/json
```

Request:

```json
{
  "email": "ana@empresa.com",
  "password": "PasswordSeguro123!"
}
```

Response `200 OK`:

```json
{
  "authenticated": true,
  "expires_in": 900
}
```

Cookie:

```http
Set-Cookie: guak_access_token=<jwt>; HttpOnly; SameSite=Lax; Path=/api; Max-Age=900
```

En staging/prod debe incluir `Secure`.

### 6.3 OAuth2 para Swagger/desarrollo

```http
POST /api/v1/auth/token
Content-Type: application/x-www-form-urlencoded

username=ana@empresa.com&password=PasswordSeguro123!
```

Response:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 900
}
```

No setea cookie. Debe poder deshabilitarse por entorno mediante `AUTH_ENABLE_PASSWORD_BEARER_TOKEN=false` fuera de local/dev. Si está deshabilitado, debe responder `404` o `403` controlado y auditable.

### 6.4 CSRF

```http
GET /api/v1/auth/csrf
```

Response:

```json
{
  "csrf_token": "<random-token>"
}
```

El cliente lo enviará en mutaciones autenticadas:

```http
X-CSRF-Token: <random-token>
```

### 6.5 Sesión actual

```http
GET /api/v1/auth/me
Cookie: guak_access_token=<jwt>
```

Response autenticada:

```json
{
  "authenticated": true,
  "user": {
    "id": "usr_550e8400-e29b-41d4-a716-446655440000",
    "display_name": "Ana García",
    "email_masked": "a***@empresa.com"
  },
  "organization": {
    "id": "org_1f7e9f1a-1c25-46a8-9f15-8f8d0f4d2f3",
    "name": "ACME"
  }
}
```

No incluye roles.

Restricción MVP multi-organización: en esta fase `/auth/me` asume el modelo actual de una organización efectiva por usuario. Si en el futuro un usuario pertenece a varias organizaciones, la selección de tenant se resolverá en la fase `CurrentUser`/`TenantContext`, no aquí.

### 6.6 Logout

```http
POST /api/v1/auth/logout
Cookie: guak_access_token=<jwt>
X-CSRF-Token: <csrf-token>
```

Response:

```json
{
  "authenticated": false
}
```

Debe borrar la cookie `guak_access_token` con los mismos atributos de path/domain.

## 7. JWT mínimo

Claims mínimos:

```json
{
  "sub": "<internal_user_id>",
  "type": "access",
  "jti": "<uuid>",
  "iat": 1700000000,
  "exp": 1700000900
}
```

### 7.1 Fronteras OAuth2/JWT/CurrentUser

- `TokenIssuer` emite tokens.
- `TokenVerifier` valida firma, expiración, `type` y `jti` cuando sea necesario para cookie, `/auth/me`, logout y CSRF.
- `OAuth2PasswordRequestForm` solo vive en el router/adaptador HTTP.
- `AuthService` recibe email/password como DTO interno y no depende de FastAPI.
- `CurrentUserProvider` y `TenantContextProvider` definitivos quedan para fase JWT posterior.

No incluir:

- password;
- password hash;
- roles;
- permisos;
- `organization_id` en esta fase;
- datos personales;
- public IDs si no son necesarios para validación.

## 8. Public IDs

Formato:

```text
usr_<uuid-v4>
org_<uuid-v4>
```

Reglas:

- únicos en DB;
- generados en backend;
- usados en responses públicas de auth;
- nunca sustituyen validación de autorización/tenant en backend.

## 9. CSRF

Estrategia elegida: endpoint explícito `/auth/csrf` con token firmado por servidor.

### 9.1 Emisión

- `GET /api/v1/auth/csrf` requiere sesión autenticada mediante `guak_access_token`.
- El token CSRF no es secreto de larga vida, pero no debe loguearse.
- El token debe estar firmado con secreto de servidor o HMAC equivalente.
- El payload firmado debe vincularse como mínimo a:
  - `sub` del access token;
  - `jti` del access token;
  - `exp` igual o inferior al access token.
- El token expira como máximo al expirar el access token.

### 9.2 Validación

Aplicar a mutaciones autenticadas:

```text
POST
PUT
PATCH
DELETE
```

Reglas:

- no aplicar a `GET`;
- no exigir inicialmente en `/auth/login` ni `/organizations/register`;
- exigir `X-CSRF-Token` en mutaciones autenticadas;
- token ausente, inválido, expirado o de otra sesión devuelve `403 Forbidden`;
- logout requiere CSRF;
- no registrar el token CSRF en logs ni auditoría.

### 9.3 Tests esperados

- mutación autenticada sin CSRF → `403`;
- mutación autenticada con CSRF inválido → `403`;
- mutación autenticada con CSRF expirado → `403`;
- token CSRF generado para otro `jti` → `403`;
- `/auth/login` y `/organizations/register` no requieren CSRF en esta fase.

## 10. CORS

Origins permitidos local:

```text
http://localhost:3000
http://localhost:5173
http://127.0.0.1:3000
http://127.0.0.1:5173
```

Reglas:

- `allow_credentials=True`;
- no wildcard;
- headers dev: `Content-Type`, `X-CSRF-Token`, `Authorization`;
- headers prod recomendados: `Content-Type`, `X-CSRF-Token`;
- `Authorization` configurable por entorno.

## 11. Errores HTTP

### Login fallido

HTTP `401` con mensaje único:

```json
{
  "detail": "No se ha podido iniciar sesión con las credenciales proporcionadas."
}
```

Aplica a:

- usuario inexistente;
- password incorrecta;
- usuario inactivo;
- organización inactiva.

### Registro duplicado

HTTP `409` con mensaje genérico:

```json
{
  "detail": "No se puede completar el registro con los datos proporcionados."
}
```

## 12. Auditoría

Eventos:

```text
ORGANIZATION_REGISTERED
USER_REGISTERED
LOGIN_SUCCESS
LOGIN_FAILED
LOGOUT
```

`/auth/token` debe auditarse igual que login, con metadata interna `channel=oauth2_token`.

Metadata permitida:

- IDs internos si existen;
- `email_hash`;
- reason interno;
- channel interno (`cookie_login` u `oauth2_token`);
- IP;
- user agent;
- correlation id.

Metadata prohibida:

- password;
- hash;
- access token;
- CSRF token;
- JWT secret;
- email completo salvo decisión explícita posterior.

## 13. Tests mínimos

### Unitarios

- password hash/verify;
- token issuer con `jti` y expiración;
- cookie settings;
- email masking;
- public ID generation;
- CSRF token generation/validation;
- login service casos positivos/negativos;
- registration service duplicados.

### API/integración

- registro devuelve public IDs y no IDs internos;
- `/auth/login` setea cookie y no devuelve token;
- `/auth/token` devuelve bearer y no setea cookie;
- `/auth/token` deshabilitado por configuración responde error controlado;
- `/auth/me` no devuelve roles, token ni email completo;
- `/auth/logout` borra cookie;
- CSRF endpoint devuelve token;
- mutación autenticada sin CSRF falla;
- CORS permite origins configurados y credentials.

### Seguridad

- login fallido siempre mismo mensaje;
- no password/hash/token/CSRF en logs/responses;
- JWT no contiene `organization_id` ni roles;
- IDs internos no aparecen en responses públicas de auth;
- CORS no permite wildcard;
- prod puede desactivar `Authorization` header.

## 14. Migraciones y datos

Añadir:

- `tbl_users.public_id` único, no nulo;
- `tbl_organization.public_id` único, no nulo.

Si hay datos existentes, la migración debe poblar public IDs.

## 15. Riesgos y deuda técnica

- Sin rate limiting en esta fase: debe implementarse después como requisito bloqueante antes de staging/productivo expuesto públicamente.
- Sin revocación real de `jti`; logout borra cookie, pero un token robado vive hasta expirar.
- Sin refresh token.
- Sin 2FA/TOTP.
- Sin verificación email.
- Protección completa del resto de endpoints queda para fase JWT/CurrentUser.

## 16. Secuencia esperada de implementación

```text
1. Config y dependencias
2. Public IDs + migraciones
3. PasswordHasher
4. TokenIssuer
5. Cookie manager
6. Registro inicial
7. Login cookie + OAuth2 token
8. /auth/me
9. /auth/logout
10. CSRF
11. CORS
12. Tests
13. Documentación implementation
14. QA/CI
```

## 17. Criterios técnicos de aceptación

- No hay lógica de negocio en routers.
- Servicios testeables sin FastAPI.
- Repositorios encapsulan SQLAlchemy.
- Token no se expone al frontend principal.
- Cookies tienen atributos seguros configurables.
- CSRF está cubierto por tests.
- CORS está cubierto por tests.
- Responses públicas no exponen IDs internos ni roles.
- Auditoría no contiene secretos.
