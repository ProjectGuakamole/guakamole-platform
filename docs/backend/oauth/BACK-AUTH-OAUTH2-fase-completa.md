# BACK-AUTH-OAUTH2 — Fase OAuth2 completa del backend

> [!NOTE]
> Documento único de la fase OAuth2 del backend de Project Guakamole. Está pensado para leerse de forma didáctica por el equipo junior: qué se hizo, por qué se hizo así, qué ganamos y qué límites aceptamos en cada task.

## Índice de la fase

1. BACK-AUTH-OAUTH2-002 — Auth Core
2. BACK-AUTH-OAUTH2-003 — Registro inicial organización + usuario
3. BACK-AUTH-OAUTH2-004 — Login cookie HttpOnly
4. BACK-AUTH-OAUTH2-005 — `/auth/me`
5. BACK-AUTH-OAUTH2-006 — Logout
6. BACK-AUTH-OAUTH2-007 — CSRF
7. BACK-AUTH-OAUTH2-008 — `/auth/token`
8. BACK-AUTH-OAUTH2-009 — CORS
9. BACK-AUTH-OAUTH2-010 — Hardening final
10. BACK-AUTH-OAUTH2-011 — Rate limiting
11. BACK-AUTH-OAUTH2-012 — Validación y cierre final

> [!WARNING]
> En esta primera iteración solo se desarrolla el punto 1. Los puntos 2-11 quedan como índice de trabajo para completar el documento en ejecuciones posteriores.

---

## 1. BACK-AUTH-OAUTH2-002 — Auth Core

### Qué problema resuelve

Antes de poder construir un login, un registro o un endpoint protegido, el backend necesitaba una base común de autenticación. Esa base es lo que llamamos **Auth Core**.

La idea era evitar empezar la casa por el tejado. Si primero hacemos un router `POST /auth/login` y metemos dentro la lógica de contraseñas, tokens, cookies y configuración, acabamos con un endpoint que funciona, pero que es difícil de probar, difícil de reutilizar y peligroso de tocar.

Esta task resolvió justo eso: crear las piezas pequeñas y reutilizables sobre las que luego se apoyarían las tareas siguientes de la fase OAuth2.

En concreto, el problema era:

- cómo leer configuración sensible sin defaults inseguros;
- cómo hashear contraseñas de forma moderna;
- cómo emitir y verificar access tokens JWT mínimos;
- cómo preparar cookies seguras sin depender todavía de FastAPI;
- cómo generar identificadores públicos para no exponer IDs internos;
- cómo dejar todo esto testeable sin levantar la API completa.

> [!NOTE]
> Esta task no buscaba que el usuario pudiera iniciar sesión todavía. Buscaba crear las herramientas internas que después permitirían hacerlo bien.

### Qué es el Auth Core

El **Auth Core** es el conjunto de primitivas internas de autenticación del backend. No es un flujo HTTP completo, no es un router y no es una pantalla de login. Es una capa base de dominio/infraestructura que permite al resto del backend decir:

```text
Necesito hashear una contraseña.
Necesito verificar un password.
Necesito emitir un access token.
Necesito verificar un access token.
Necesito saber cómo debe configurarse la cookie de auth.
Necesito generar un ID público usr_... u org_...
```

La clave está en que estas piezas se diseñaron **sin depender de routers concretos de FastAPI**. Eso permite probarlas en unitarios, reutilizarlas desde varios servicios y mantener la lógica crítica lejos de los adaptadores HTTP.

### Qué piezas se crearon

| Pieza | Responsabilidad | Impacto |
| --- | --- | --- |
| `AuthSettings` | Centralizar configuración de auth, JWT, cookies y valores relacionados. | Evita configuración dispersa y obliga a definir secretos sensibles. |
| `PwdlibPasswordHasher` | Hashear y verificar passwords con Argon2id mediante `pwdlib`. | Evita guardar contraseñas en claro o usar hashes débiles. |
| `JwtAccessTokenService` | Emitir y verificar access tokens JWT mínimos. | Define el contrato base de sesión autenticada. |
| `AuthCookieSettings` | Representar la configuración de cookie de auth como value object. | Permite reutilizar los mismos atributos al emitir y borrar cookies. |
| `public_ids` | Generar y validar IDs públicos `usr_...` y `org_...`. | Evita exponer IDs internos de base de datos en contratos públicos. |

### Por qué se escogió este enfoque

Se escogió un enfoque modular porque autenticación es una zona crítica del backend. En Project Guacamole no queremos que la seguridad dependa de “esto lo hace el frontend” o de “este router se acuerda de validar tal cosa”. La lógica sensible debe vivir en backend y debe ser fácil de testear.

Decisiones importantes:

- **Configuración tipada con `AuthSettings`**: toda la configuración de auth se carga de forma centralizada. Especialmente importante: `JWT_SECRET_KEY` no tiene fallback inseguro. Si no existe, la configuración falla. Esto es incómodo en local si se te olvida poner la variable, pero es exactamente lo que queremos: mejor fallar al arrancar que firmar tokens con un secreto de juguete.
- **Argon2id con `pwdlib`**: Argon2id es una opción moderna para hashing de contraseñas. `pwdlib` aporta una abstracción limpia y recomendaciones seguras por defecto.
- **JWT mínimo**: el access token contiene lo necesario para identificar la sesión, no un volcado de datos del usuario. En Auth Core se preparó la base con `sub`, `type`, `jti`, `iat` y `exp`. En tareas posteriores se añadió `org` para asociar la sesión a una organización efectiva.
- **Cookies como value object**: la configuración de cookie se calcula sin acoplarse a `Response` de FastAPI. Así el dominio no necesita saber cómo se setea una cookie HTTP concreta.
- **Public IDs**: se introducen prefijos `usr_...` y `org_...` para respuestas públicas. Los IDs internos pueden seguir existiendo en PostgreSQL, pero no se convierten en contrato externo.

> [!TIP]
> Pensad en el Auth Core como una caja de herramientas. Todavía no abre puertas por sí sola, pero nos da cerraduras, llaves y normas para que las puertas futuras no se improvisen.

### Cómo se implantó

La implantación se hizo dentro del dominio de autenticación del backend, manteniendo piezas pequeñas:

```text
backend/app/domain/auth/
├── config.py
├── cookies.py
├── password_hasher.py
├── public_ids.py
└── tokens.py
```

El diseño separa puertos e implementaciones donde tiene sentido. Por ejemplo, `PasswordHasher` y `TokenIssuer`/`TokenVerifier` funcionan como contratos internos. Esto nos permitiría cambiar detalles de implementación más adelante sin reescribir todos los servicios que los usan.

Flujo conceptual:

```text
AuthSettings
   ├── configura JwtAccessTokenService
   ├── configura AuthCookieSettings
   └── obliga a definir JWT_SECRET_KEY

PwdlibPasswordHasher
   ├── hash(password)
   └── verify(password, hash)

JwtAccessTokenService
   ├── issue_access_token(subject)
   └── verify_access_token(token)

public_ids
   ├── generate_public_id(USER)         → usr_<uuid-v4>
   └── generate_public_id(ORGANIZATION) → org_<uuid-v4>
```

### Ejemplo de configuración

Ejemplo orientativo de variables usadas por la fase de autenticación:

```dotenv
ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_SECRET_KEY=change-me-with-a-real-secret
JWT_ALGORITHM=HS256

AUTH_COOKIE_NAME=guak_access_token
AUTH_COOKIE_PATH=/api
AUTH_COOKIE_DOMAIN=
AUTH_COOKIE_HTTPONLY=true
AUTH_COOKIE_SECURE=false
AUTH_COOKIE_SAMESITE=lax
```

> [!WARNING]
> `JWT_SECRET_KEY` aparece aquí con un valor de ejemplo, no como secreto real. En el repositorio no debe guardarse nunca un secreto válido. En local, staging y producción debe venir del entorno.

Detalle importante: `AuthSettings` exige que exista `JWT_SECRET_KEY`. No hay un fallback tipo `dev-secret`, `changeme` o `secret`. Eso evita que un entorno mal configurado arranque firmando tokens con una clave predecible.

### Ejemplo conceptual de uso

Hashing de contraseña:

```python
hasher = PwdlibPasswordHasher()

password_hash = hasher.hash("PasswordSeguro123!")
is_valid = hasher.verify("PasswordSeguro123!", password_hash)
```

Emisión de access token mínimo:

```python
settings = AuthSettings()
tokens = JwtAccessTokenService(settings)

access_token = tokens.issue_access_token(subject="usr_550e8400-e29b-41d4-a716-446655440000")
verified = tokens.verify_access_token(access_token)
```

Payload conceptual del JWT en esta base:

```json
{
  "sub": "usr_550e8400-e29b-41d4-a716-446655440000",
  "type": "access",
  "jti": "7b6f4b3f-9f8a-41e8-9dd8-f6c2d1f9b123",
  "iat": 1760000000,
  "exp": 1760000900
}
```

En tareas posteriores, el token se amplió para incluir también `org`:

```json
{
  "sub": "usr_550e8400-e29b-41d4-a716-446655440000",
  "org": "org_1f7e9f1a-1c25-46a8-9f15-8f8d0f4d2f3",
  "type": "access",
  "jti": "7b6f4b3f-9f8a-41e8-9dd8-f6c2d1f9b123",
  "iat": 1760000000,
  "exp": 1760000900
}
```

Cookie settings conceptual:

```json
{
  "name": "guak_access_token",
  "path": "/api",
  "domain": null,
  "httponly": true,
  "secure": false,
  "samesite": "lax",
  "max_age": 900
}
```

Public IDs:

```text
usr_550e8400-e29b-41d4-a716-446655440000
org_1f7e9f1a-1c25-46a8-9f15-8f8d0f4d2f3
```

### Beneficios

- **Menos acoplamiento**: el core no depende de routers concretos, así que se puede usar desde login, registro, `/auth/token` o futuros servicios internos.
- **Mejor testabilidad**: se pueden probar tokens, hashing, cookies y public IDs sin levantar FastAPI ni tocar la base de datos.
- **Seguridad por defecto más razonable**: `JWT_SECRET_KEY` obligatorio, algoritmo JWT restringido a `HS256` en MVP y passwords con Argon2id.
- **Contratos más limpios**: el JWT mínimo evita meter roles, permisos o datos personales dentro del token antes de tener clara la autorización.
- **Preparación para cookie HttpOnly**: aunque esta task no emite cookies, deja preparada la configuración reutilizable para login y logout.
- **No exposición de IDs internos**: los public IDs preparan una frontera más segura entre API pública y modelo relacional interno.

### Limitaciones o prejuicios asumidos

También hubo decisiones con coste:

- **Sin refresh token**: se simplifica el MVP, pero el usuario tendrá que volver a autenticarse cuando expire el access token si no se añade otro mecanismo.
- **Sin revocación de `jti`**: el token tiene `jti`, pero en esta task no existe blacklist ni almacenamiento de tokens revocados. El `jti` queda preparado para auditoría/revocación futura.
- **Secreto obligatorio desde el principio**: mejora seguridad, pero puede hacer fallar comandos locales si el entorno no está bien configurado.
- **JWT mínimo**: obliga a consultar backend/DB para autorización real, pero eso es bueno para no fiarnos de claims de roles o tenant enviados al cliente.
- **Public IDs no sustituyen autorización**: que un ID sea público no significa que cualquiera pueda usarlo. La validación de permisos y tenant sigue siendo responsabilidad del backend.
- **Cookie `secure=false` por defecto en local**: permite desarrollo sin HTTPS, pero en staging/producción debe configurarse como `true` detrás de TLS.

> [!IMPORTANT]
> Un public ID evita exponer el ID interno, pero no es una medida de autorización. Si un usuario de ACME manda un `org_...` de CyberCorp, el backend debe denegarlo igualmente.

### Qué NO hace todavía

Esta task fue deliberadamente limitada. No implementa:

- endpoints HTTP;
- routers de FastAPI;
- login real;
- registro de organización o usuario;
- emisión de cookie en una respuesta HTTP;
- endpoint `/auth/me`;
- logout;
- CSRF;
- CORS;
- refresh tokens;
- revocación server-side de tokens;
- auditoría persistente;
- RBAC;
- tenant context definitivo.

Esto no es un fallo de la task. Es una decisión de alcance: primero se construye el núcleo, después se conectan los flujos HTTP.

### Resultado de la task

El resultado fue una base de autenticación pequeña, clara y reutilizable para el backend:

- `AuthSettings` centraliza configuración sensible y evita fallback inseguro para `JWT_SECRET_KEY`.
- Las contraseñas se hashean con Argon2id mediante `pwdlib`.
- Se pueden emitir y verificar access tokens JWT mínimos.
- Los claims base quedan definidos: `sub`, `type`, `jti`, `iat`, `exp`; y la arquitectura queda preparada para añadir `org` en los flujos posteriores.
- La configuración de cookie HttpOnly queda modelada para login/logout futuros.
- Se introducen public IDs `usr_...` y `org_...` para no exponer identificadores internos.
- El core queda separado de FastAPI y de routers concretos.

Validaciones documentadas para esta task:

```text
make backend-quality      ✅
make backend-test-unit    ✅ 291 passed, 56 deselected
```

En resumen: **BACK-AUTH-OAUTH2-002 no dio todavía un login usable, pero sí dejó los cimientos correctos para construirlo sin improvisar seguridad en cada endpoint**.

---

## 2. BACK-AUTH-OAUTH2-003 — Registro inicial organización + usuario

Pendiente de redactar en una ejecución posterior.

## 3. BACK-AUTH-OAUTH2-004 — Login cookie HttpOnly

Pendiente de redactar en una ejecución posterior.

## 4. BACK-AUTH-OAUTH2-005 — `/auth/me`

Pendiente de redactar en una ejecución posterior.

## 5. BACK-AUTH-OAUTH2-006 — Logout

Pendiente de redactar en una ejecución posterior.

## 6. BACK-AUTH-OAUTH2-007 — CSRF

Pendiente de redactar en una ejecución posterior.

## 7. BACK-AUTH-OAUTH2-008 — `/auth/token`

Pendiente de redactar en una ejecución posterior.

## 8. BACK-AUTH-OAUTH2-009 — CORS

Pendiente de redactar en una ejecución posterior.

## 9. BACK-AUTH-OAUTH2-010 — Hardening final

Pendiente de redactar en una ejecución posterior.

## 10. BACK-AUTH-OAUTH2-011 — Rate limiting

Pendiente de redactar en una ejecución posterior.

## 11. BACK-AUTH-OAUTH2-012 — Validación y cierre final

Pendiente de redactar en una ejecución posterior.
