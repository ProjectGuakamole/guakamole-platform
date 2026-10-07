# BACK-AUTH-OAUTH2-001 — Roadmap de fase OAuth2

**Estado:** Planificación cerrada para revisión  
**Ámbito:** `backend/`  
**Carpeta:** `docs/backend/oauth2/`  
**Referencia:** https://fastapi.tiangolo.com/es/tutorial/security/oauth2-jwt/

## 1. Objetivo

Planificar de forma estricta la fase OAuth2 de Project Guakamole antes de implementar código.

La fase debe habilitar:

1. registro inicial de empresa y primer usuario administrador;
2. login seguro para frontend mediante cookie HttpOnly;
3. endpoint OAuth2 Password Bearer para Swagger/desarrollo;
4. emisión de access token JWT mínimo;
5. logout, sesión actual y CSRF básico;
6. CORS backend controlado para frontend local.

Aunque OAuth2 estrictamente cubre el login, el registro entra en esta fase porque el sistema necesita crear usuarios con `password_hash` real antes de poder autenticarlos.

## 2. Contexto actual

El frontend dispone de:

- vista de login en `http://localhost:3000/login`;
- formulario de creación de cuenta con datos de empresa y usuario.

La decisión de seguridad principal es no almacenar tokens en `localStorage` ni `sessionStorage`. El flujo principal del frontend usará cookie HttpOnly.

## 3. Alcance de la fase

Incluye:

- documentación de roadmap, diseño técnico e implementación;
- registro inicial de organización y primer usuario;
- public IDs para usuario y organización;
- password hashing Argon2id mediante `pwdlib`;
- login frontend con cookie HttpOnly;
- endpoint OAuth2 `/auth/token` para Swagger/desarrollo;
- logout por borrado de cookie;
- endpoint `/auth/me` con datos mínimos no sensibles;
- endpoint `/auth/csrf` y validación CSRF básica para mutaciones autenticadas;
- CORS con credenciales y origins explícitos;
- auditoría de registro y login;
- tests unitarios, API, seguridad, CORS y CSRF.

## 4. Fuera de alcance

No incluye:

- integración frontend funcional;
- refresh tokens;
- revocación real/blacklist de `jti`;
- 2FA/TOTP;
- rate limiting, aunque queda documentado como obligatorio y bloqueante antes de staging/productivo expuesto;
- CurrentUser/TenantContext definitivos para proteger el resto de endpoints;
- RBAC completo;
- flujo multi-organización mediante `OrganizationMembership` definitivo;
- verificación email;
- workflow de aprobación manual de organizaciones;
- almacenamiento de tokens en cliente.

## 5. Decisiones cerradas

| Decisión | Resultado |
| --- | --- |
| Frontend auth | Cookie HttpOnly; no `localStorage`, no `sessionStorage` |
| Cookie access token | `guak_access_token` |
| Cookie path | `/api` |
| Cookie domain | No definido en local; configurable por entorno |
| Cookie HttpOnly | `true` siempre |
| Cookie Secure | `false` local, `true` staging/prod |
| Cookie SameSite | `lax` |
| Cookie Max-Age | Igual a expiración del token |
| Access token | 15 minutos iniciales, configurable con `ACCESS_TOKEN_EXPIRE_MINUTES` |
| Login frontend | `POST /api/v1/auth/login` setea cookie y no devuelve token |
| Login frontend response | `{ "authenticated": true, "expires_in": 900 }` |
| OAuth2 Swagger/dev | `POST /api/v1/auth/token` devuelve bearer token, no setea cookie y debe ser configurable por entorno |
| Logout | `POST /api/v1/auth/logout` borra cookie y devuelve `{ "authenticated": false }` |
| Sesión actual | `GET /api/v1/auth/me` devuelve datos mínimos sin roles ni token |
| Email en `/auth/me` | Enmascarado |
| Roles en `/auth/me` | No se exponen |
| IDs internos | No se exponen en responses públicas de auth |
| Public IDs | `tbl_users.public_id` y `tbl_organization.public_id` únicos |
| Public ID format | UUID v4 con prefijo `usr_` / `org_` |
| CSRF | Entra en esta fase |
| CSRF endpoint | `GET /api/v1/auth/csrf`, autenticado, emite token firmado ligado a sesión/JWT |
| CSRF scope | Métodos mutadores autenticados: `POST`, `PUT`, `PATCH`, `DELETE` |
| CSRF login/register | No requerido inicialmente |
| CORS credentials | `allow_credentials=True` |
| Origins CORS | `localhost` y `127.0.0.1` en puertos `3000` y `5173` |
| CORS headers dev | `Content-Type`, `X-CSRF-Token`, `Authorization` |
| CORS headers prod | `Content-Type`, `X-CSRF-Token`; `Authorization` configurable/desactivable |
| Mensaje login fallido | `No se ha podido iniciar sesión con las credenciales proporcionadas.` |
| Refresh token | No en esta fase |
| Rate limiting | Fuera de esta fase, pero obligatorio y bloqueante antes de staging/productivo expuesto |
| Frontend | No se modifica sin consulta previa |
| `/auth/token` auditoría | Debe auditarse como login por canal `oauth2_token` sin registrar token |

## 6. Contratos HTTP previstos

### 6.1 Registro inicial

```http
POST /api/v1/organizations/register
Content-Type: application/json
```

No devuelve token. Crea organización y primer usuario con password hasheada.

Response conceptual:

```json
{
  "organization_id": "org_550e8400-e29b-41d4-a716-446655440000",
  "user_id": "usr_1f7e9f1a-1c25-46a8-9f15-8f8d0f4d2f3",
  "organization_status": "ACTIVE",
  "user_status": "ACTIVE"
}
```

### 6.2 Login frontend con cookie HttpOnly

```http
POST /api/v1/auth/login
Content-Type: application/json
```

```json
{
  "email": "ana@empresa.com",
  "password": "PasswordSeguro123!"
}
```

Response:

```json
{
  "authenticated": true,
  "expires_in": 900
}
```

Set-Cookie conceptual:

```http
Set-Cookie: guak_access_token=<jwt>; HttpOnly; SameSite=Lax; Path=/api; Max-Age=900
```

`Secure` será configurable por entorno.

### 6.3 OAuth2 estándar para Swagger/dev

```http
POST /api/v1/auth/token
Content-Type: application/x-www-form-urlencoded

username=ana@empresa.com&password=PasswordSeguro123!
```

```json
{
  "access_token": "...",
  "token_type": "bearer",
  "expires_in": 900
}
```

No setea cookie.

### 6.4 CSRF

```http
GET /api/v1/auth/csrf
```

```json
{
  "csrf_token": "..."
}
```

El token CSRF será firmado por el servidor, no sensible, vinculado como mínimo al `sub`, `jti` y `exp` del access token actual, y expirará como máximo junto al access token. `/auth/csrf` requiere sesión autenticada.

El frontend enviará el token en mutaciones autenticadas:

```http
X-CSRF-Token: <csrf_token>
```

### 6.5 Sesión actual

```http
GET /api/v1/auth/me
```

```json
{
  "authenticated": true,
  "user": {
    "id": "usr_...",
    "display_name": "Ana García",
    "email_masked": "a***@empresa.com"
  },
  "organization": {
    "id": "org_...",
    "name": "ACME"
  }
}
```

No expone roles, token, email completo, IDs internos, CIF/NIF, dirección ni fecha de nacimiento.

### 6.6 Logout

```http
POST /api/v1/auth/logout
```

```json
{
  "authenticated": false
}
```

Borra `guak_access_token`.

## 7. Reglas de validación y seguridad

- No guardar password en claro.
- No devolver `password_hash`.
- No exponer access token al frontend principal.
- No exponer roles en `/auth/me`.
- No exponer IDs internos incrementales en responses públicas de auth.
- No confiar en ningún dato de rol, user u organización enviado por frontend.
- Login fallido usa siempre el mismo mensaje genérico.
- Usuario u organización inactiva no puede iniciar sesión.
- CSRF se valida en mutaciones autenticadas.
- CSRF ausente, inválido, expirado o perteneciente a otra sesión devuelve `403`.
- `/auth/login` y `/organizations/register` quedan excluidos de CSRF en esta fase por ser endpoints públicos de bootstrap; se compensan con cookie HttpOnly, errores genéricos y rate limiting posterior obligatorio.
- CORS nunca usa wildcard.
- Rate limiting queda como riesgo crítico y task posterior obligatoria.

## 8. Auditoría

Eventos mínimos:

| Evento | Cuándo |
| --- | --- |
| `ORGANIZATION_REGISTERED` | Se crea organización desde registro inicial |
| `USER_REGISTERED` | Se crea primer usuario administrador |
| `LOGIN_SUCCESS` | Login correcto por `/auth/login` o `/auth/token` |
| `LOGIN_FAILED` | Login fallido por `/auth/login` o `/auth/token` |
| `LOGOUT` | Logout solicitado |

Metadata permitida:

- `reason` interno para login fallido;
- `channel` interno: `cookie_login` u `oauth2_token`;
- `ip_address`;
- `user_agent`;
- `correlation_id`;
- `actor_user_id` interno si existe;
- `organization_id` interno si existe;
- `email_hash`.

Metadata prohibida:

- password;
- password hash;
- access token;
- CSRF token;
- JWT secret;
- email completo salvo decisión posterior explícita.

## 9. Diseño modular esperado

- `app/domain/auth/` para login, logout, csrf, sesión, password hashing y token.
- `app/domain/iam/organizations/` para registro inicial.
- Routers como adaptadores HTTP sin lógica de negocio.
- Servicios/casos de uso testeables sin FastAPI.
- Repositorios encapsulando SQLAlchemy.
- Puertos para password hasher, token issuer, auditoría y repositorios.

## 10. División por PRs/tickets

### BACK-AUTH-OAUTH2-001 — Documentación y diseño OAuth2

Incluye:

- roadmap;
- diseño técnico;
- plantilla de implementación.

No incluye código productivo.

### BACK-AUTH-OAUTH2-002 — Auth Core

Incluye:

- dependencias auth/JWT/password;
- flag de entorno para habilitar/deshabilitar `/auth/token` fuera de dev;
- configuración de cookie/token/CORS/CSRF;
- `PasswordHasher`;
- `TokenIssuer`;
- utilidades de public ID si procede;
- tests unitarios.

### BACK-AUTH-OAUTH2-003 — Registro inicial

Incluye:

- migración `public_id` para organización y usuario;
- `POST /api/v1/organizations/register`;
- hash de password;
- estado/roles configurables;
- geografía textual MVP;
- auditoría de registro;
- tests unitarios/API/seguridad.

### BACK-AUTH-OAUTH2-004 — Login, sesión y logout

Incluye:

- `POST /api/v1/auth/login` con cookie HttpOnly;
- `POST /api/v1/auth/token` para Swagger/dev;
- `GET /api/v1/auth/me`;
- `POST /api/v1/auth/logout`;
- `last_login_at`;
- auditoría login/logout;
- errores genéricos;
- tests unitarios/API/seguridad.

### BACK-AUTH-OAUTH2-005 — CORS, CSRF y cierre OAuth2

Incluye:

- CORS con credenciales;
- configuración dev/prod de headers;
- `GET /api/v1/auth/csrf`;
- validación CSRF en mutaciones autenticadas;
- tests CORS/CSRF;
- actualización final de implementation doc;
- QA final.

## 11. Roadmap de tasks y subtasks

### Task 1 — Completar documentación de fase

- [ ] Revisar roadmap y design.
- [ ] Alinear implementation doc como plantilla pendiente.
- [ ] Añadir notas explícitas de separación OAuth2/JWT.

### Task 2 — Auth Core

- [ ] Añadir dependencias `pwdlib[argon2]` y JWT seleccionada.
- [ ] Añadir configuración sin secretos reales.
- [ ] Implementar `PasswordHasher`.
- [ ] Implementar `TokenIssuer` con `jti`.
- [ ] Implementar configuración de cookies y security settings.
- [ ] Tests unitarios.

### Task 3 — Registro inicial

- [ ] Añadir migración `public_id` en users/organization.
- [ ] Crear schemas y servicio de registro.
- [ ] Resolver geografía textual contra catálogos existentes.
- [ ] Crear organización y usuario con estados configurables.
- [ ] Asignar rol funcional esperado configurable.
- [ ] Persistir `password_hash`.
- [ ] No devolver token ni IDs internos.
- [ ] Auditar registro.

### Task 4 — Login, sesión y logout

- [ ] Implementar `/auth/login` con cookie HttpOnly.
- [ ] Implementar `/auth/token` para Swagger/dev sin cookie.
- [ ] Implementar `/auth/me` sin roles y con email enmascarado.
- [ ] Implementar `/auth/logout` borrando cookie.
- [ ] Actualizar `last_login_at`.
- [ ] Auditar login/logout.
- [ ] Tests API/seguridad.

### Task 5 — CORS y CSRF

- [ ] Configurar CORS con `allow_credentials=True`.
- [ ] Permitir origins locales definidos.
- [ ] Configurar headers dev/prod.
- [ ] Implementar `/auth/csrf`.
- [ ] Validar `X-CSRF-Token` en mutaciones autenticadas.
- [ ] Tests CORS/CSRF.

### Task 6 — QA final y documentación de implementación

- [ ] Ejecutar `make backend-quality`.
- [ ] Ejecutar tests unitarios, integración, seguridad, CORS y CSRF.
- [ ] Actualizar `BACK-AUTH-OAUTH2-001-implementation.md`.
- [ ] Documentar riesgos pendientes para fase JWT/rate limiting.
- [ ] Confirmar CI verde.

## 12. Criterios de aceptación

La fase se considera aceptada cuando:

- registro crea organización y usuario sin exponer token ni IDs internos;
- frontend login usa cookie HttpOnly y no devuelve token;
- `/auth/token` permite Swagger/dev sin setear cookie y puede deshabilitarse por configuración fuera de dev;
- `/auth/me` devuelve datos mínimos, sin roles, sin token y sin IDs internos;
- `/auth/logout` borra cookie;
- CSRF firmado y ligado a sesión/JWT existe para mutaciones autenticadas;
- CORS permite credenciales solo para origins explícitos;
- passwords se almacenan como Argon2id;
- eventos de auditoría mínimos están implementados o integrados;
- tests unitarios, API, seguridad, CORS y CSRF pasan;
- CI está verde.

## 13. Riesgos y deuda técnica aceptada

- No hay rate limiting todavía; debe implementarse como requisito bloqueante antes de staging/productivo expuesto públicamente.
- No hay refresh token ni revocación real de `jti`.
- No hay 2FA/TOTP.
- Organización y usuario quedan `ACTIVE` automáticamente en MVP mediante configuración inicial.
- No hay verificación email todavía.
- La validación completa de JWT, `CurrentUser` y protección del resto de endpoints quedan para la fase JWT.
- Frontend no queda integrado en esta fase; cualquier cambio imprescindible requiere consulta previa.

## 14. Definition of Done

- [ ] Roadmap revisado y aceptado.
- [ ] Diseño técnico revisado y aceptado.
- [ ] PRs divididas según planificación.
- [ ] Documentación de implementación actualizada.
- [ ] Tests unitarios añadidos y pasando.
- [ ] Tests API/integración añadidos y pasando.
- [ ] Tests de seguridad, CORS y CSRF añadidos y pasando.
- [ ] Auditoría validada.
- [ ] Sin secretos reales en repositorio.
- [ ] Sin cambios en frontend salvo aprobación explícita.
- [ ] CI verde.
- [ ] PR revisado.
