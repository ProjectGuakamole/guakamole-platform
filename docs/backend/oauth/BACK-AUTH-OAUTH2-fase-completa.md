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

> [!NOTE]
> En esta iteración quedan desarrollados los puntos 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 y 11. El documento recoge el cierre completo de la fase OAuth2 del backend.

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
backend/app/domains/auth/
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

En resumen: **BACK-AUTH-OAUTH2-002 no dio todavía un login usable, pero sí dejó los cimientos correctos para construirlo sin improvisar seguridad en cada endpoint**.

---

## 2. BACK-AUTH-OAUTH2-003 — Registro inicial organización + usuario

### Qué problema resuelve

Después de tener el Auth Core, el backend ya sabía hashear contraseñas, generar public IDs y preparar tokens, pero todavía faltaba algo muy práctico: **crear usuarios reales con una contraseña real**.

Sin este paso, el login posterior habría sido difícil de probar de forma honesta. Podríamos haber usado seeds, datos insertados a mano o usuarios inventados en tests, pero eso no representa el flujo mínimo que necesita una plataforma B2B: una empresa entra por primera vez, crea su organización y deja creado su primer usuario administrador.

Esta task resolvió ese arranque inicial, el bootstrap B2B del sistema:

```text
Crear organización
   +
Crear primer usuario administrador
   +
Guardar password con hash real
   +
Devolver solo identificadores públicos
```

La necesidad era sencilla de explicar: **si no podemos registrar una organización y un usuario inicial, Auth Core existe, pero todavía no es usable para una demo real**.

### Qué hace esta task

Se implementó el endpoint:

```http
POST /api/v1/organizations/register
```

Este endpoint crea una organización y su usuario inicial en una única operación de backend. No es un alta parcial ni un formulario decorativo: persiste datos reales en base de datos y deja al usuario preparado para que, en las siguientes tasks, pueda iniciar sesión con su email y contraseña.

Lo importante del comportamiento es:

- crea una organización nueva;
- crea el primer usuario asociado a esa organización;
- genera un hash real de password usando Argon2id a través del Auth Core;
- genera public IDs con formato `org_...` y `usr_...`;
- aplica estados iniciales configurables para organización y usuario;
- aplica roles iniciales configurables para el usuario registrado;
- no inicia sesión automáticamente;
- no devuelve ningún token;
- no crea cookie de sesión;
- no expone IDs internos de base de datos;
- no expone `password_hash`.

Esta separación es importante. Registrar una cuenta y autenticar una sesión son cosas relacionadas, pero no son la misma operación.

### Por qué se hizo así

La decisión principal fue **separar registro de autenticación**.

Cuando un usuario se registra, el backend crea datos. Cuando un usuario hace login, el backend verifica credenciales y crea una sesión. Si mezclamos ambos conceptos demasiado pronto, el registro acaba teniendo efectos secundarios difíciles de controlar: emisión de tokens, cookies, tenant context a medias o sesiones abiertas sin que el flujo de login haya sido diseñado todavía.

Por eso esta task no hace login automático. Puede parecer menos cómodo para la demo, pero es más limpio y más seguro. El flujo queda así:

```text
Registro
   │
   ├── crea organización
   ├── crea usuario
   └── guarda password_hash

Login posterior
   │
   ├── verifica email + password
   ├── emite token
   └── configura cookie HttpOnly
```

También se decidió que el backend fuese el dueño de los public IDs y de los estados iniciales. El cliente no manda `org_...`, no decide el estado de la organización y no decide qué rol interno se asigna. El cliente pide registrar unos datos; el backend aplica las reglas del sistema.

Esto nos ayuda en tres puntos:

- facilita la demo y las pruebas posteriores de login con usuarios creados por el propio sistema;
- evita que el frontend o un cliente HTTP invente identificadores o estados;
- mantiene una frontera clara entre contrato público de API y modelo interno de persistencia.

> [!TIP]
> El registro no está pensado como “ya tengo una sesión”. Está pensado como “ya existe una organización y un usuario válido para poder autenticarse después”.

### Cómo se implantó

La implementación se dividió en piezas pequeñas, siguiendo la misma filosofía del Auth Core: que el router no se convierta en un cajón desastre con validación, SQLAlchemy, hashing y reglas de negocio todo junto.

La estructura conceptual queda así:

```text
Router de registro
   │
   ▼
Schemas Pydantic
   │
   ▼
Servicio de registro
   │
   ├── valida duplicados
   ├── obtiene estados y roles por defecto desde settings
   ├── genera public IDs
   ├── hashea password
   └── coordina la operación
   │
   ▼
Repositorio SQLAlchemy
   │
   └── persiste organización y usuario
```

El router expone `POST /api/v1/organizations/register` y traduce errores de aplicación a respuestas HTTP. La validación de forma y contenido básico vive en schemas Pydantic: campos obligatorios, formato de email, formato de slug, confirmación de contraseña y política mínima de password.

El servicio de registro contiene el caso de uso. Es quien decide el orden de la operación: comprobar duplicados, resolver referencias necesarias, crear la organización, hacer `flush` para disponer del ID interno, crear el usuario asociado y confirmar la transacción.

El repositorio encapsula el acceso a SQLAlchemy. Esto permite que el servicio no tenga que saber todos los detalles de consulta, tablas auxiliares o referencias internas.

Además, la task reutiliza settings para valores por defecto como:

- estado inicial de organización registrada;
- estado inicial de usuario registrado;
- rol de plataforma por defecto;
- rol de organización por defecto.

En el MVP estos estados iniciales son activos por configuración. Es una decisión pragmática: permite avanzar con el golden path y probar login sin añadir todavía verificación de email, invitaciones o revisión manual de altas.

### Ejemplo de request

Ejemplo resumido de alta de organización y usuario inicial:

```json
{
  "organization": {
    "name": "ACME SOC",
    "slug": "acme-soc",
    "legal_name": "ACME Security Operations Center S.L.",
    "tax_id": "B12345678",
    "country": "España",
    "state": "Catalunya",
    "city": "Barcelona",
    "address": "Carrer de la Seguretat 10",
    "postal_code": "08001"
  },
  "user": {
    "first_name": "Ana",
    "last_name": "García",
    "email": "ana.admin@acme.example",
    "birth_date": "1990-05-14",
    "password": "PasswordSeguro123!",
    "password_confirm": "PasswordSeguro123!",
    "country": "España",
    "state": "Catalunya",
    "city": "Barcelona",
    "address": "Carrer de la Seguretat 10",
    "postal_code": "08001"
  }
}
```

La contraseña viaja en la request porque el backend necesita crear el hash, pero no se guarda en claro y no vuelve nunca en la respuesta.

### Ejemplo de response

Respuesta esperada en un registro correcto:

```json
{
  "organization_id": "org_1f7e9f1a-1c25-46a8-9f15-8f8d0f4d2f3",
  "user_id": "usr_550e8400-e29b-41d4-a716-446655440000",
  "organization_status": "ACTIVE",
  "user_status": "ACTIVE"
}
```

La respuesta es deliberadamente corta. Devuelve lo que el cliente necesita para saber que el alta se ha creado, pero no filtra detalles internos:

- no aparece `id_organization`;
- no aparece `id_user`;
- no aparece `password_hash`;
- no aparece ningún token;
- no aparece ninguna cookie.

### Beneficios

Esta task aportó un salto importante porque convirtió la autenticación de una base técnica en algo empezable desde producto.

Beneficios principales:

- **Bootstrap B2B reproducible**: podemos crear una organización y su primer usuario sin tocar la base de datos a mano.
- **Usuarios reales para login**: las siguientes tasks ya pueden probar autenticación con contraseñas hasheadas de verdad.
- **Menos exposición de secretos**: el password en claro no se persiste y el hash no se devuelve por API.
- **Contratos públicos más seguros**: el cliente trabaja con `org_...` y `usr_...`, no con IDs internos.
- **Base para multi-tenant**: cada usuario nace asociado a una organización, lo que prepara el terreno para tenant context, autorización y aislamiento posterior.
- **Reglas centralizadas en backend**: estados, roles iniciales y public IDs no dependen del frontend.

### Limitaciones o compromisos

La task no intentó resolver todo el onboarding B2B definitivo. Se aceptaron varios compromisos para avanzar de forma controlada:

- **No hay verificación de email todavía**: el usuario queda activo según configuración MVP, sin confirmación por correo.
- **No hay invitaciones todavía**: el flujo de invitación de empleados o managers se deja para fases posteriores.
- **No hay auditoría persistente real todavía**: el servicio deja preparada una abstracción de auditoría, pero no existe aún un `AuditEvent` persistido completo para este flujo.
- **No hay rate limiting en esta task concreta**: el registro nace sin esa protección específica en este punto de la fase, aunque se aborda más adelante en el hardening OAuth2.
- **Estados iniciales activos**: `ACTIVE` para organización y usuario es una decisión MVP configurable, útil para demo, pero no necesariamente la política final de producción.
- **Dependencia de referencias existentes**: estados, roles y geografía deben existir en base de datos; si faltan, el registro no puede completarse correctamente.

Estos límites no invalidan la task. Al contrario: dejan claro qué parte del problema se cerró y qué parte pertenece a tickets posteriores.

### Qué NO hace todavía

Esta task no implementa:

- creación de grupos;
- asignación RBAC avanzada completa;
- login automático;
- emisión de access token;
- creación de cookie HttpOnly;
- envío de emails;
- invitaciones;
- verificación de email;
- tenant context completo para peticiones autenticadas;
- alta de roadmaps o escenarios;
- onboarding completo de empleados.

La idea fue mantener el alcance pequeño: primero registrar organización y usuario inicial, después construir login, sesión y autorización encima.

### Resultado de la task

El resultado fue que Auth Core dejó de ser solo una caja de herramientas interna y empezó a ser útil para flujos reales.

A partir de esta task, el backend ya podía crear una empresa y un usuario con contraseña real, hash seguro y public IDs pensados para API. Eso preparó directamente el camino para la siguiente pieza de la fase: hacer login con ese usuario y empezar a trabajar con sesión de verdad.

En resumen: **BACK-AUTH-OAUTH2-003 convirtió la base de autenticación en un flujo usable para pruebas reales, sin mezclar todavía registro con sesión ni exponer datos sensibles**.

## 3. BACK-AUTH-OAUTH2-004 — Login cookie HttpOnly

### Qué problema resuelve

La task anterior ya permitía registrar una organización y un usuario con una contraseña real. Eso era un paso enorme, pero todavía faltaba la parte que cualquier persona espera después de registrarse: **poder iniciar sesión**.

Hasta este punto, el backend podía crear usuarios con `password_hash`, pero no existía todavía un flujo HTTP que recibiera `email` y `password`, comprobara esas credenciales y dejara al navegador autenticado para las siguientes peticiones.

El problema no era solo “hacer un login”. También había una decisión de seguridad importante: el frontend necesitaba una sesión usable desde navegador, pero no queríamos guardar el access token en `localStorage` ni en `sessionStorage`.

Guardar tokens ahí suele ser cómodo, pero tiene un coste: si aparece una vulnerabilidad XSS y JavaScript malicioso se ejecuta en la aplicación, ese JavaScript puede intentar leer esos almacenes y robar el token. Por eso esta task apostó por una sesión basada en cookie `HttpOnly`.

### Qué hace esta task

Se implementó el endpoint:

```http
POST /api/v1/auth/login
```

El flujo funcional es:

```text
Cliente envía email + password
   │
   ▼
Router HTTP recibe la petición
   │
   ▼
LoginService valida credenciales
   │
   ├── busca el usuario por email normalizado
   ├── verifica que el usuario está activo
   ├── comprueba la contraseña con Argon2id
   └── emite un access token JWT
   │
   ▼
Router guarda el token en cookie HttpOnly
   │
   ▼
Respuesta mínima: { "status": "authenticated" }
```

La respuesta pública es deliberadamente pequeña:

```json
{
  "status": "authenticated"
}
```

Lo importante es lo que **no** devuelve:

- no devuelve el JWT en el body;
- no devuelve `password_hash`;
- no devuelve IDs internos;
- no devuelve roles;
- no devuelve información completa del usuario.

El token se emite como JWT de acceso y se entrega mediante la cookie `guak_access_token`.

### Qué es una cookie HttpOnly y por qué se escogió

Una cookie es un pequeño dato que el servidor puede pedir al navegador que guarde. Después, el navegador la envía automáticamente en las peticiones que correspondan según su dominio, ruta y políticas de seguridad.

La parte importante aquí es el atributo `HttpOnly`. Cuando una cookie tiene `HttpOnly`, el navegador la sigue enviando en peticiones HTTP, pero **JavaScript no puede leerla directamente** con `document.cookie`.

Dicho de forma sencilla:

```text
localStorage/sessionStorage
   └── JavaScript puede leer el token

cookie HttpOnly
   └── JavaScript no puede leer directamente el token
```

Esto no elimina todos los riesgos, pero reduce mucho la exposición del access token ante XSS. Si un atacante consigue ejecutar JavaScript en la página, lo tendrá más difícil para robar el token y llevárselo fuera, porque el token no está disponible como valor legible desde el código cliente.

El compromiso de esta decisión es que, al usar cookies para autenticar peticiones de navegador, hay que pensar en CSRF para operaciones autenticadas que modifican estado. En esta task todavía no se resolvió CSRF; se aceptó como una pieza posterior de la fase OAuth2.

> [!TIP]
> La cookie `HttpOnly` no significa “seguridad mágica”. Significa que el token deja de estar al alcance directo de JavaScript. Es una buena base, pero necesita complementarse con CSRF, CORS, `Secure`, `SameSite`, rate limiting y validaciones de backend.

### Cómo se implantó

La implementación siguió la misma idea que las tasks anteriores: router fino, lógica de negocio en servicio y acceso a datos encapsulado en repositorio.

La estructura conceptual queda así:

```text
auth/login/router.py
   │
   ├── recibe POST /login
   ├── llama a LoginService
   ├── traduce errores a HTTP 401
   └── configura Set-Cookie

auth/login/schemas.py
   │
   ├── LoginRequest
   ├── LoginResponse
   └── LoginTokenData

auth/login/service.py
   │
   ├── valida credenciales
   ├── verifica usuario activo
   ├── usa PasswordHasher
   ├── usa TokenIssuer
   └── registra auditoría conceptual

login_repositories.py
   │
   └── busca usuario por email normalizado
```

`LoginRequest` define el contrato de entrada: `email` y `password`. El email se normaliza haciendo `strip()` y pasándolo a minúsculas. Además, el schema no acepta campos extra, lo que evita contratos ambiguos o payloads con datos que el backend no espera.

`LoginResponse` define el contrato de salida público. Solo contiene el estado `authenticated`. El access token no forma parte de la respuesta JSON.

`LoginService` contiene el caso de uso. Recibe la request ya validada, busca el usuario por email normalizado, comprueba que existe, verifica que está activo y valida la contraseña usando `PwdlibPasswordHasher`. Si algo falla, lanza un error de credenciales inválidas sin dar pistas sobre si el email existe, si el usuario está inactivo o si la contraseña es incorrecta.

El repositorio se encarga de consultar los datos mínimos necesarios para autenticar:

- public ID del usuario;
- public ID de la organización;
- `password_hash`;
- estado del usuario.

Con esos datos, `JwtAccessTokenService` emite un access token con claims mínimos. En este punto ya se incluye el usuario en `sub` y la organización en `org`, usando public IDs. No se meten roles ni permisos dentro del token.

Después, el router construye la configuración de cookie con `build_auth_cookie_settings`. Esta función centraliza atributos como nombre, ruta, `HttpOnly`, `Secure`, `SameSite` y `Max-Age`, en vez de repetirlos a mano en cada endpoint.

También se dejó `NoOpLoginAuditAdapter` como punto de extensión para auditoría. Conceptualmente ya existen eventos de login correcto y login fallido, pero en esta task todavía no se persisten como `AuditEvent` real.

### Ejemplo de request

```json
{
  "email": "ana@empresa.com",
  "password": "PasswordSeguro123!"
}
```

### Ejemplo de response

```json
{
  "status": "authenticated"
}
```

### Ejemplo conceptual de Set-Cookie

```http
Set-Cookie: guak_access_token=<jwt>; HttpOnly; Path=/api; SameSite=lax; Max-Age=900
```

En un entorno con HTTPS, la cookie debe configurarse también con `Secure`. En local puede estar desactivado por configuración para permitir desarrollo sin TLS, pero no debe entenderse como la política final de staging o producción.

### Beneficios

Esta task convirtió el registro en una experiencia de autenticación real para navegador.

Beneficios principales:

- **Token fuera del body**: el JWT no aparece en la respuesta JSON, así que no se obliga al frontend a almacenarlo manualmente.
- **Menor exposición ante XSS**: al usar cookie `HttpOnly`, JavaScript no puede leer directamente el access token.
- **Base para sesión browser segura**: el navegador puede mantener la sesión mediante cookie y enviar credenciales en peticiones posteriores dentro del ámbito configurado.
- **Reutilización del Auth Core**: el login usa el hasher Argon2id, el servicio JWT y la configuración de cookies ya preparados.
- **Router más limpio**: el endpoint HTTP no concentra toda la lógica; delega credenciales, tokens y acceso a datos en piezas específicas.
- **Errores genéricos**: ante credenciales inválidas se responde de forma uniforme, sin revelar si el usuario existe o qué parte ha fallado.
- **Token mínimo**: se usan public IDs para `sub` y `org`, sin meter roles, permisos ni datos personales en el JWT.

### Limitaciones o compromisos

Esta task cerró el primer login, pero no pretendía resolver toda la seguridad de sesión de golpe. Quedaron compromisos claros:

- **Sin CSRF todavía**: al usar cookies, las mutaciones autenticadas necesitaban una protección CSRF que se abordó después.
- **Sin logout todavía**: el backend aún no tenía endpoint para borrar la cookie de autenticación.
- **Sin refresh token**: solo se emite access token; cuando expire, el usuario necesitará volver a autenticarse o esperar a una solución posterior.
- **Sin auditoría persistente**: `NoOpLoginAuditAdapter` deja el puerto conceptual, pero no guarda eventos reales en base de datos.
- **Sin rate limiting en esta task concreta**: la protección específica contra fuerza bruta se resolvió más adelante en la fase.
- **Cookie `Secure` dependiente de configuración**: en local puede estar desactivada, pero en entornos con TLS debe activarse.
- **Selección de organización simplificada**: el login usa la organización asociada al usuario según el modelo disponible en ese momento. Si más adelante una cuenta pertenece a varias organizaciones activas, habrá que diseñar selección de tenant.

### Qué NO hace todavía

Esta task no implementa:

- perfil completo del usuario;
- devolución de roles;
- `CurrentUser` completo para endpoints protegidos;
- endpoint `/auth/me`;
- logout;
- CSRF;
- refresh tokens;
- integración con frontend;
- autorización RBAC completa;
- auditoría persistente;
- rate limiting como parte de esta task concreta.

La idea fue mantener el alcance claro: primero autenticar credenciales y establecer una sesión de navegador razonablemente segura; después construir encima el resto de piezas.

### Resultado de la task

El resultado fue que el backend ya podía cerrar el ciclo básico iniciado por el registro:

```text
Registrar organización y usuario
   │
   ▼
Iniciar sesión con email/password
   │
   ▼
Verificar password Argon2id
   │
   ▼
Emitir JWT de acceso
   │
   ▼
Guardar JWT en cookie HttpOnly
```

En resumen: **BACK-AUTH-OAUTH2-004 convirtió el usuario registrado en una sesión real de navegador, manteniendo el token fuera del alcance directo de JavaScript y sin exponerlo en el body de la respuesta**.

## 4. BACK-AUTH-OAUTH2-005 — `/auth/me`

### Qué problema resuelve

Después del login, el navegador ya tiene una cookie `HttpOnly` con el access token. Eso está bien desde el punto de vista de seguridad, porque JavaScript no puede leer directamente el JWT. Pero abre una pregunta práctica muy normal para el frontend:

```text
Vale, tengo una sesión en el navegador... ¿pero quién soy?
```

El frontend necesita hidratar su estado inicial: saber si hay usuario autenticado, mostrar una zona privada, decidir si debe redirigir al login o continuar dentro de la aplicación. Lo que no queremos es resolver eso leyendo el token desde JavaScript, porque precisamente la cookie `HttpOnly` se eligió para evitar esa exposición.

Esta task cubre ese hueco. El backend pasa a ser quien lee la cookie, valida el JWT, comprueba que el usuario existe y responde con una identidad pública mínima.

### Qué hace esta task

Se implementa el endpoint:

```http
GET /api/v1/auth/me
```

Su responsabilidad es sencilla, pero muy importante:

- lee la cookie `guak_access_token` desde la petición;
- valida que el token sea un access token JWT válido;
- comprueba que el token no esté expirado ni manipulado;
- exige que el token incluya organización en el claim `org`;
- busca en backend la combinación de usuario y organización;
- verifica que el usuario esté activo;
- devuelve un perfil mínimo de sesión autenticada;
- no devuelve el JWT;
- no devuelve `password_hash`;
- no devuelve secretos ni datos internos de base de datos.

La respuesta real de esta task es deliberadamente pequeña:

```json
{
  "authenticated": true,
  "user_id": "usr_550e8400-e29b-41d4-a716-446655440000",
  "organization_id": "org_1f7e9f1a-1c25-46a8-9f15-8f8d0f4d2f3"
}
```

Es decir, en esta implementación no se devuelve todavía email, nombre visible, roles ni permisos. La idea es confirmar identidad autenticada y organización efectiva, no convertir `/auth/me` en un endpoint de perfil completo.

### Por qué se hizo así

Este patrón es muy habitual cuando se trabaja con cookies `HttpOnly`: el frontend no lee el token, sino que pregunta al backend “¿quién soy?”. El navegador envía la cookie automáticamente y el backend decide si esa cookie representa una sesión válida.

La ventaja principal es que la validación de sesión queda centralizada en el backend. No dependemos de que el cliente decodifique un JWT, interprete claims o tome decisiones de seguridad. El frontend solo recibe una respuesta ya filtrada y segura.

También prepara una pieza clave para el resto de la API. A partir de aquí, otros endpoints autenticados pueden apoyarse en el mismo enfoque: extraer token de cookie, verificarlo, resolver usuario real y trabajar siempre desde una identidad validada por backend.

### Cómo se implantó

La implementación se repartió en piezas pequeñas dentro del dominio de autenticación:

```text
auth/me/router.py         → router HTTP y lectura de cookie
auth/me/schemas.py        → schema público de respuesta
auth/me/service.py        → caso de uso de identidad actual
auth/me/repository.py     → consulta a base de datos
auth/shared/config.py     → settings de autenticación
auth/shared/tokens.py     → verificación del JWT de acceso
```

El router obtiene el nombre real de la cookie desde la configuración de autenticación, por lo que no queda quemado como una constante suelta dentro del endpoint. Si no encuentra cookie, responde con `401 Unauthorized`.

El servicio utiliza `JwtAccessTokenService` para verificar el access token. Si el JWT es inválido, está expirado, tiene un tipo incorrecto o no contiene la organización esperada, el flujo se corta como no autenticado.

Después, el repository resuelve la identidad contra base de datos usando los public IDs del usuario y de la organización. Este punto es importante: no basta con que el token diga `sub=usr_...`; también se comprueba la organización `org=org_...` y que el usuario esté en estado `ACTIVE`.

Conceptualmente, el flujo queda así:

```text
Navegador
   │
   │ GET /api/v1/auth/me
   │ Cookie: guak_access_token=...
   ▼
Router /auth/me
   │
   ├── lee cookie HttpOnly
   ├── valida JWT con JwtAccessTokenService
   ├── extrae sub + org
   ├── consulta usuario activo en backend
   └── devuelve identidad pública mínima
```

### Errores esperados

El endpoint está pensado para no dar pistas innecesarias. En los casos de autenticación fallida responde de forma controlada con `401 Unauthorized` y un mensaje genérico.

Casos esperados:

- no hay cookie `guak_access_token`;
- la cookie existe, pero el token no es válido;
- el token ha expirado;
- el token no es de tipo access token;
- el token no incluye organización;
- el usuario indicado por el token no existe;
- el usuario existe, pero no está activo;
- la organización del token no coincide con la identidad persistida.

La decisión importante es no diferenciar detalles sensibles en la respuesta pública. Para el cliente, todos esos casos significan lo mismo: no hay una sesión válida usable.

### Beneficios

- Permite hidratar la sesión del frontend sin exponer el JWT a JavaScript.
- Mantiene la cookie `HttpOnly` como frontera de seguridad entre navegador y token.
- Refuerza que la identidad se resuelve en backend, no en el cliente.
- Introduce una base reutilizable para endpoints autenticados posteriores.
- Devuelve solo datos mínimos y seguros.
- Comprueba usuario y organización contra backend, preparando el camino hacia tenant context y RBAC.

### Limitaciones o compromisos

Esta task no intenta resolver todo el modelo de sesión definitivo. Sus límites principales son:

- no construye todavía un tenant context completo para toda la aplicación;
- no devuelve roles, memberships ni permisos detallados;
- no implementa refresh token;
- no añade protección CSRF para mutaciones, aunque `/auth/me` sea una operación de lectura;
- no registra auditoría persistente específica para éxito o fallo de `/auth/me`;
- no crea una sesión server-side persistente ni una tabla de sesiones revocables.

Son compromisos aceptables para este punto de la fase: primero necesitábamos cerrar el ciclo mínimo de sesión de navegador antes de añadir más capas.

### Qué NO hace todavía

Este endpoint no sirve para modificar nada del usuario. En concreto, no hace:

- cambio de contraseña;
- actualización de perfil;
- devolución de permisos completos;
- selección de organización activa;
- cambio de organización;
- logout;
- refresh de sesión;
- creación de una sesión server-side persistente.

Tampoco debe usarse como sustituto de autorización. Que `/auth/me` confirme una identidad no significa que esa identidad pueda acceder a cualquier recurso. Cada endpoint protegido seguirá necesitando sus comprobaciones de permisos, organización y alcance.

### Resultado de la task

Con esta task se completa el ciclo mínimo browser de autenticación:

```text
Login correcto
   │
   ▼
Backend emite JWT de acceso
   │
   ▼
Backend lo guarda en cookie HttpOnly
   │
   ▼
Frontend no puede leer el JWT
   │
   ▼
Frontend llama a /auth/me
   │
   ▼
Backend valida cookie + token + usuario activo
   │
   ▼
Frontend sabe quién está autenticado sin ver el token
```

En resumen: **BACK-AUTH-OAUTH2-005 permite al frontend saber si existe una sesión autenticada y a qué usuario/organización pertenece, manteniendo el JWT fuera de JavaScript y sin exponer datos sensibles en la respuesta**.

## 5. BACK-AUTH-OAUTH2-006 — Logout

### Qué problema resuelve

Después de implementar el login con cookie `HttpOnly` y el endpoint `/auth/me`, el backend ya podía abrir una sesión de navegador y comprobar quién estaba autenticado. Pero faltaba una pieza igual de importante para cerrar el ciclo: **permitir al usuario cerrar sesión limpiando la cookie de autenticación desde el backend**.

El problema concreto era este:

```text
Login correcto
   │
   ▼
Backend setea cookie HttpOnly guak_access_token
   │
   ▼
El navegador la envía automáticamente a /auth/me
   │
   ▼
Faltaba una forma backend de eliminar esa cookie
```

Como la cookie es `HttpOnly`, JavaScript no puede leerla ni manipular directamente su contenido. Eso es bueno para seguridad, porque reduce exposición frente a XSS, pero implica una consecuencia práctica: el logout no debe depender de que el frontend borre un token que ni siquiera puede leer. El backend tiene que responder con una cabecera `Set-Cookie` que indique al navegador que elimine la cookie.

Esta task añade esa capacidad mediante:

```http
POST /api/v1/auth/logout
```

### Qué hace el endpoint

El endpoint `POST /api/v1/auth/logout` cierra la sesión local del navegador eliminando la cookie de autenticación `guak_access_token`.

La respuesta pública es mínima:

```json
{
  "status": "logged_out"
}
```

Lo importante no es el body, sino la cabecera HTTP de respuesta. El backend devuelve una instrucción equivalente a:

```http
Set-Cookie: guak_access_token=; Max-Age=0; Path=/api; HttpOnly; SameSite=Lax
```

Con `Max-Age=0` o una expiración en el pasado, el navegador entiende que debe borrar la cookie. Para que el borrado funcione de forma fiable, la cookie se elimina con los mismos atributos relevantes con los que fue creada, especialmente `Path`, `Domain`, `SameSite` y `Secure`.

> [!IMPORTANT]
> Borrar una cookie no consiste solo en poner su valor vacío. El navegador identifica cookies por nombre y atributos como `path` y `domain`. Si se intenta borrar con un `Path` distinto al usado al crearla, puede quedar una cookie antigua viva.

### Por qué el logout no necesita devolver tokens

El logout no devuelve access token, refresh token, usuario, roles, email ni identificadores internos. Su contrato se mantiene deliberadamente pequeño.

La razón es doble:

- **seguridad**: cerrar sesión no debe ser un momento en el que el backend vuelva a exponer secretos o datos sensibles;
- **responsabilidad clara**: el objetivo del endpoint es indicar al navegador que elimine la cookie, no crear una nueva sesión ni describir el perfil del usuario.

En este modelo, el token ya fue emitido durante el login y almacenado en una cookie `HttpOnly`. En logout no hay nada útil que entregar al cliente. Devolver el token sería especialmente contradictorio: estaríamos intentando cerrar sesión mientras volvemos a entregar la credencial que permite autenticarse.

### Idempotencia del cierre de sesión

El logout se diseñó como una operación idempotente desde el punto de vista funcional: pedir cerrar sesión varias veces debe conducir al mismo estado final del navegador, que es **no conservar la cookie de autenticación**.

Conceptualmente:

```text
logout con cookie existente      → borra cookie → logged_out
logout con cookie ya eliminada   → sigue sin cookie → logged_out
logout con token expirado        → borra cookie si está presente → logged_out
logout repetido varias veces     → mismo resultado final
```

Por eso el endpoint no necesita leer el token para poder borrar la cookie. Para eliminar una cookie basta con conocer su nombre y los atributos con los que se emitió. Validar el JWT no aporta nada al acto de borrado y, además, podría generar una mala experiencia: si el token está expirado, el usuario seguiría necesitando poder limpiar la cookie del navegador.

> [!NOTE]
> En fases posteriores, al añadirse CSRF, el endpoint puede quedar protegido como mutación autenticada. Eso no cambia la idea base del logout: la eliminación de la cookie se hace desde backend y no requiere devolver ni regenerar tokens.

### Cómo se implantó

La implementación se mantuvo intencionadamente sencilla. No se creó un servicio de dominio complejo porque no había una regla de negocio persistente que coordinar: no se actualiza usuario, no se toca contraseña, no se modifica organización y no se registra una sesión server-side que haya que cerrar.

La estructura queda separada en dos piezas principales:

```text
auth/logout/schemas.py
   └── define la respuesta pública mínima

auth/logout/router.py
   └── expone POST /auth/logout y elimina la cookie en la Response
```

El router es fino: recibe la `Response`, obtiene la configuración de autenticación y construye los settings de cookie reutilizando el helper común. Después llama al mecanismo de FastAPI/Starlette para borrar la cookie en la respuesta HTTP.

El punto clave es que no se duplican atributos “a mano”. Se reutiliza la misma configuración de cookie que ya usa el login:

- nombre desde `AUTH_COOKIE_NAME`, por defecto `guak_access_token`;
- `Path` desde `AUTH_COOKIE_PATH`, por defecto `/api`;
- `Domain` si está configurado;
- `SameSite` desde settings;
- `Secure` desde settings;
- `HttpOnly=true`.

Esto evita una clase de errores muy habitual: login crea la cookie con unos atributos y logout intenta borrarla con otros. En ese caso el usuario ve “logout correcto”, pero el navegador puede seguir enviando la cookie antigua.

### Errores esperados y controlados

El comportamiento esperado del logout es ser conservador y no filtrar información.

En el alcance propio de esta task, el caso normal es responder con `200 OK` y cuerpo mínimo aunque el objetivo sea simplemente limpiar estado local del navegador. No hay motivo para devolver detalles como “token expirado”, “token inválido” o “usuario inexistente” durante un logout, porque esos mensajes no ayudan al cliente y pueden aportar señales innecesarias.

Con las protecciones añadidas en tareas posteriores, pueden aparecer errores controlados antes de llegar al borrado efectivo, por ejemplo:

- petición sin credenciales cuando el endpoint se trata como mutación autenticada;
- token CSRF ausente o inválido cuando la protección CSRF está activa;
- configuración de autenticación incorrecta en el entorno, que debe fallar de forma explícita y no silenciosa.

La regla de diseño sigue siendo la misma: si el backend acepta procesar el logout, la respuesta no debe revelar secretos ni datos de usuario, y debe intentar dejar al navegador sin cookie de sesión.

### Beneficios

Esta task aporta varios beneficios claros al backend:

- **Completa el ciclo básico de sesión de navegador**: `login → me → logout`.
- **Mantiene el token fuera de JavaScript**: el frontend no necesita leer ni borrar manualmente el JWT.
- **Reduce acoplamiento con el cliente**: el cierre de sesión depende de una respuesta HTTP del backend, no de lógica sensible en frontend.
- **Evita exposición de secretos**: logout no devuelve tokens ni datos internos.
- **Reutiliza configuración común de cookies**: login y logout comparten nombre, path, domain, SameSite y Secure.
- **Mejora la experiencia de usuario**: incluso si el token ya no sirve, el usuario debe poder limpiar el estado local de sesión.

### Limitaciones asumidas

El logout implementado es un cierre de sesión basado en eliminación de cookie. Eso es suficiente para el flujo básico del navegador, pero no equivale a una revocación completa de credenciales en servidor.

Limitaciones conscientes:

- **sin blacklist de JWT**: si alguien copió el token antes del logout, podría seguir siendo válido hasta su expiración;
- **sin revocación server-side por `jti`**: el claim `jti` existe como base futura, pero esta task no persiste tokens revocados;
- **sin refresh token**: no hay par access/refresh ni rotación de refresh tokens en esta fase;
- **sin sesión server-side persistente**: no existe una tabla de sesiones activas que marcar como cerrada;
- **sin cierre global de dispositivos**: cerrar sesión en este navegador no invalida automáticamente otros navegadores o equipos;
- **CSRF se aborda en una task posterior**: históricamente esta protección se incorpora después como parte del endurecimiento de mutaciones autenticadas.

Estas limitaciones no invalidan la task. Simplemente delimitan su alcance: **logout limpia la sesión local del navegador, no implementa todavía una plataforma completa de gestión y revocación de sesiones**.

### Qué NO hace

Para evitar confusiones, este endpoint no hace lo siguiente:

- no borra el usuario;
- no desactiva la cuenta;
- no cambia la contraseña;
- no elimina la organización;
- no invalida todos los dispositivos del usuario;
- no devuelve un token nuevo;
- no devuelve secretos;
- no devuelve roles ni permisos;
- no modifica el tenant efectivo;
- no audita todavía un evento persistente de `LOGOUT` si esa auditoría no se ha implementado en la fase correspondiente.

### Resultado de la task

El resultado es que el backend ya puede completar el ciclo básico de sesión para navegador:

```text
Usuario hace login
   │
   ▼
Backend emite JWT y setea cookie HttpOnly guak_access_token
   │
   ▼
Frontend consulta /auth/me sin leer el token
   │
   ▼
Usuario solicita logout
   │
   ▼
Backend responde con Set-Cookie expirado / Max-Age=0
   │
   ▼
El navegador deja de enviar guak_access_token
```

En resumen: **BACK-AUTH-OAUTH2-006 añade el cierre de sesión backend para cookies HttpOnly, manteniendo el token fuera del frontend y dejando preparado un flujo coherente de login → me → logout para el MVP**.

## 6. BACK-AUTH-OAUTH2-007 — CSRF

### Qué problema resuelve

Las tareas anteriores dejaron el backend con una sesión de navegador basada en cookie `HttpOnly`. Esa decisión es buena para proteger el access token frente a lectura directa desde JavaScript, pero tiene una consecuencia importante: **el navegador envía la cookie automáticamente** cuando hace peticiones al backend dentro de su ámbito.

Ese comportamiento es justo lo que permite que `/auth/me` o `/auth/logout` funcionen sin que el cliente tenga que leer el JWT. Pero también abre la puerta a CSRF en operaciones que modifican estado.

CSRF significa **Cross-Site Request Forgery**. Dicho de forma sencilla: un atacante intenta conseguir que el navegador de una víctima autenticada envíe una petición al backend sin que la víctima lo haya decidido conscientemente. Como el navegador adjunta las cookies por sí solo, el backend podría recibir una petición con una cookie válida aunque la petición haya sido provocada desde otro sitio.

Ejemplo conceptual:

```text
Ana está autenticada en Guakamole
   │
   ├── su navegador conserva guak_access_token como cookie HttpOnly
   │
   ▼
Ana visita una web maliciosa
   │
   ▼
La web intenta provocar una petición POST al backend
   │
   ▼
El navegador podría adjuntar la cookie automáticamente
```

Por eso, cuando se usan cookies para autenticar, no basta con decir “el token está en `HttpOnly`”. Para métodos mutantes hace falta una defensa adicional que demuestre que la petición no solo trae una cookie válida, sino que también viene de un cliente que conoce un token CSRF emitido por el backend.

> [!IMPORTANT]
> `HttpOnly` reduce la exposición del JWT ante XSS, pero no evita por sí solo que el navegador envíe cookies automáticamente. CSRF cubre esa parte del riesgo.

### Qué hace esta task

Esta task añade una primera protección CSRF para sesiones autenticadas con cookie `guak_access_token`.

Se implementa el endpoint:

```http
GET /api/v1/auth/csrf
```

Su función es emitir un token CSRF firmado y separado del access token. Para obtenerlo, la petición debe incluir una cookie de acceso válida. La respuesta contiene únicamente el token CSRF:

```json
{
  "csrf_token": "<signed-token>"
}
```

Ese token no sustituye al JWT de sesión. Es una credencial complementaria pensada para acompañar peticiones mutantes autenticadas mediante la cabecera:

```http
X-CSRF-Token: <signed-token>
```

En esta task, la primera mutación protegida es:

```http
POST /api/v1/auth/logout
```

A partir de este cambio, `POST /api/v1/auth/logout` requiere dos cosas:

- cookie `guak_access_token` válida;
- header `X-CSRF-Token` válido.

Si falta autenticación, el backend responde de forma controlada como no autenticado. Si el problema es el token CSRF, responde con error controlado de tipo `403 Forbidden` y mensaje genérico.

### Estrategia implementada

La estrategia aplicada no guarda el token CSRF en una cookie adicional. En esta implementación, el cliente obtiene el token llamando a `GET /api/v1/auth/csrf` y lo reenvía explícitamente en el header `X-CSRF-Token` cuando llama a endpoints mutantes protegidos.

El token CSRF es independiente del access token, pero queda ligado a él. Técnicamente se emite como un JWT firmado server-side con propósito específico de CSRF. Incluye claims mínimos:

- `type = "csrf"`;
- `sub`, asociado al usuario del access token;
- `access_jti`, asociado al identificador único del access token actual;
- `iat`, instante de emisión;
- `exp`, expiración.

La expiración se toma del access token, de modo que el token CSRF no vive más que la sesión autenticada a la que acompaña.

La validación compara el token CSRF recibido en `X-CSRF-Token` contra la cookie de acceso actual. En concreto, comprueba que el `sub` y el `access_jti` encajen con el access token que el navegador está enviando en ese momento. Esto evita que un token CSRF emitido para otra sesión pueda reutilizarse con un access token distinto.

Conceptualmente:

```text
Cookie guak_access_token
   ├── sub = usr_...
   └── jti = access-token-123

Header X-CSRF-Token
   ├── sub = usr_...
   └── access_jti = access-token-123

Validación backend
   └── ambos deben coincidir
```

### Qué requests se protegen

La regla de diseño para esta fase es:

- las mutaciones autenticadas con cookie deben protegerse con CSRF;
- los métodos seguros de lectura no deberían requerir CSRF.

En términos HTTP, las peticiones candidatas a protección son:

- `POST`;
- `PUT`;
- `PATCH`;
- `DELETE`.

No se exige CSRF para `GET`, porque `GET` debe ser una operación segura de lectura. Por eso `GET /api/v1/auth/me` no requiere token CSRF: valida sesión, pero no cambia estado.

En el estado de esta task:

| Endpoint | Método | CSRF | Motivo |
| --- | --- | --- | --- |
| `/api/v1/auth/csrf` | `GET` | No como header | Emite el token CSRF tras validar la cookie de sesión. |
| `/api/v1/auth/logout` | `POST` | Sí | Es una mutación autenticada que borra la cookie de sesión. |
| `/api/v1/auth/me` | `GET` | No | Es lectura de identidad autenticada. |
| `/api/v1/auth/login` | `POST` | No | Flujo público de autenticación inicial, sin sesión previa por cookie. |
| `/api/v1/organizations/register` | `POST` | No | Flujo público de bootstrap en esta fase. |

La decisión importante es que futuras mutaciones autenticadas deberán añadir explícitamente esta protección.

### Cómo se implantó

No se añadió un middleware global. Se eligió una dependencia explícita reutilizable para que cada endpoint mutante protegido declare claramente que necesita CSRF.

La estructura conceptual queda así:

```text
auth/csrf/router.py
   └── expone GET /auth/csrf

auth/csrf/service.py
   ├── emite token CSRF firmado
   └── valida token CSRF frente al access token actual

auth/csrf/dependencies.py
   ├── obtiene y valida la cookie de acceso
   └── define require_valid_csrf_token

auth/logout/router.py
   └── protege POST /auth/logout con require_valid_csrf_token
```

La dependencia `require_valid_csrf_token` lee el header `X-CSRF-Token`, verifica que exista y delega la validación criptográfica y de claims en el servicio CSRF. Si algo falla, la petición se corta en backend antes de ejecutar la lógica del endpoint protegido.

Este enfoque tiene una ventaja didáctica y de seguridad: la protección no queda escondida. Al leer un router, se puede ver si la mutación exige CSRF o no.

### Relación con login, logout y `/auth/me`

La relación con las piezas anteriores queda así:

- **Login**: emite el access token y lo guarda en la cookie `HttpOnly`. No requiere CSRF porque todavía no existe una sesión previa basada en cookie que proteger en ese flujo.
- **`/auth/me`**: lee la cookie, valida el access token y devuelve identidad mínima. No requiere CSRF porque es `GET` y no modifica estado.
- **`/auth/csrf`**: necesita una cookie válida y emite un token CSRF separado, ligado a esa sesión.
- **Logout**: pasa a requerir cookie válida y `X-CSRF-Token` válido antes de borrar la cookie de sesión.

Esto modifica ligeramente la idea inicial de logout idempotente sin credenciales. Con CSRF activado, logout se trata como una mutación autenticada protegida: si no hay cookie válida o no hay CSRF válido, el backend puede rechazar la petición antes de borrar la cookie.

### Beneficios

La protección CSRF aporta varios beneficios al backend:

- **Hace viables las cookies `HttpOnly` para mutaciones autenticadas**: ya no dependemos solo de que el navegador envíe la cookie.
- **Mantiene el JWT fuera del frontend**: el access token no se expone en body ni en JavaScript.
- **Separa responsabilidades**: access token para autenticación; token CSRF para demostrar intención en mutaciones con cookie.
- **Reduce riesgo CSRF**: un atacante no debería poder fabricar una mutación válida solo consiguiendo que el navegador adjunte cookies.
- **Liga el CSRF a la sesión real**: el token CSRF se valida contra `sub` y `jti` del access token actual.
- **Evita persistencia innecesaria en esta fase**: no se añade tabla de tokens CSRF ni estado server-side adicional.
- **Prepara endpoints futuros**: queda una dependencia reutilizable para proteger nuevas mutaciones autenticadas.

### Limitaciones o compromisos

La solución es suficiente como defensa inicial, pero tiene límites claros:

- **Protección manual por dependencia**: si en el futuro se crea una mutación autenticada y se olvida añadir `require_valid_csrf_token`, esa ruta podría quedar sin protección CSRF.
- **Sin persistencia server-side del token CSRF**: el token se valida criptográficamente y contra la sesión, pero no hay lista de tokens revocados.
- **Requiere que el cliente envíe el header**: las llamadas mutantes protegidas deben incluir `X-CSRF-Token`.
- **`SameSite` ayuda, pero no sustituye CSRF**: configurar cookies con `SameSite=Lax` o políticas similares reduce escenarios de riesgo, pero no debe ser la única defensa.
- **No protege frente a XSS por sí solo**: si un atacante ejecuta JavaScript dentro del propio origen legítimo, el problema pasa a ser XSS y necesita otras defensas.
- **Sin auditoría específica de fallos CSRF**: los errores se controlan, pero no se documenta todavía un evento persistente específico de auditoría para cada fallo.
- **CORS queda separado**: CORS controla qué orígenes pueden leer respuestas del backend desde navegador, pero no reemplaza la validación CSRF.

### Qué NO hace

Para evitar malentendidos, CSRF no sustituye otras capas de seguridad:

- no sustituye la autenticación;
- no sustituye la autorización RBAC;
- no valida permisos ni tenant por sí mismo;
- no es rate limiting;
- no cifra datos;
- no revoca JWT;
- no evita fuerza bruta;
- no convierte una request no autenticada en autenticada;
- no arregla vulnerabilidades XSS.

CSRF responde a una pregunta concreta: “esta petición mutante autenticada con cookie, ¿incluye además una prueba explícita emitida por el backend para esta sesión?”.

### Resultado de la task

El resultado es que la autenticación browser con cookie `HttpOnly` queda reforzada para operaciones mutantes.

El flujo conceptual pasa a ser:

```text
Login correcto
   │
   ▼
Backend setea guak_access_token como HttpOnly
   │
   ▼
Cliente pide GET /api/v1/auth/csrf
   │
   ▼
Backend emite csrf_token ligado al access token actual
   │
   ▼
Cliente llama a una mutación protegida
   │
   ├── Cookie: guak_access_token
   └── X-CSRF-Token: csrf_token
   │
   ▼
Backend valida access token + CSRF
```

En resumen: **BACK-AUTH-OAUTH2-007 hace que las cookies `HttpOnly` sean una base más viable para mutaciones autenticadas, porque añade una defensa CSRF server-side sin exponer el JWT al cliente y dejando una dependencia reutilizable para futuras rutas protegidas**.

## 7. BACK-AUTH-OAUTH2-008 — `/auth/token`

### Qué problema resuelve

Hasta este punto, el flujo principal de autenticación del backend estaba pensado para navegador: el usuario hacía login en `POST /api/v1/auth/login`, el backend verificaba credenciales y guardaba el access token en una cookie `HttpOnly`. Esa estrategia es la adecuada para el browser principal porque evita que JavaScript tenga que leer o almacenar el JWT.

Pero había otro caso de uso distinto: **Swagger/OpenAPI y clientes técnicos**.

Herramientas como la documentación interactiva de FastAPI esperan poder trabajar con un flujo OAuth2 compatible con password/form. En ese flujo, el cliente envía credenciales como formulario `application/x-www-form-urlencoded` y recibe un bearer token en el body para usarlo después en la cabecera `Authorization`.

El problema era, por tanto, doble:

- mantener la estrategia segura de navegador basada en cookie `HttpOnly`;
- ofrecer a Swagger, tests y clientes técnicos un endpoint compatible con OAuth2 Password Bearer.

La solución fue añadir un endpoint específico para este segundo caso, sin cambiar el comportamiento de `/auth/login`.

### Endpoint real

Se implementa el endpoint:

```http
POST /api/v1/auth/token
```

Este endpoint vive bajo el router de autenticación y está pensado para emitir un access token bearer en formato compatible con OAuth2/OpenAPI.

No es el login principal para el frontend browser. Es una entrada técnica para herramientas que necesitan recibir el token explícitamente y enviarlo después como:

```http
Authorization: Bearer <jwt>
```

### Formato de la request

El endpoint usa `OAuth2PasswordRequestForm` de FastAPI. Eso significa que no espera JSON, sino formulario codificado como:

```http
Content-Type: application/x-www-form-urlencoded
```

Los campos relevantes son los estándar del flujo OAuth2 password:

```text
username=<email-del-usuario>
password=<password-del-usuario>
```

Ejemplo conceptual:

```http
POST /api/v1/auth/token
Content-Type: application/x-www-form-urlencoded

username=ana@empresa.com&password=PasswordSeguro123!
```

Aunque el campo se llame `username`, en Project Guakamole se interpreta como el email de login del usuario. El router transforma ese formulario en un `LoginRequest` interno:

```text
OAuth2PasswordRequestForm
   ├── username → LoginRequest.email
   └── password → LoginRequest.password
```

Esta traducción se queda en la capa HTTP. El servicio de login no necesita saber si las credenciales llegaron como JSON desde `/auth/login` o como formulario OAuth2 desde `/auth/token`.

### Respuesta del endpoint

Si las credenciales son válidas, el endpoint devuelve el access token en el body:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 900
}
```

`token_type` se devuelve como `bearer`, que es el valor esperado por clientes OAuth2 y por Swagger UI. `expires_in` indica la vida del access token en segundos cuando aplica; en esta implementación se calcula a partir de la configuración `ACCESS_TOKEN_EXPIRE_MINUTES`.

> [!WARNING]
> Que el token se devuelva en el body no lo hace menos sensible. `access_token` debe tratarse como un secreto: quien lo tenga podrá intentar autenticarse como ese usuario hasta que expire.

### Diferencia entre `/auth/login` y `/auth/token`

Los dos endpoints autentican credenciales, pero tienen propósitos distintos.

| Endpoint | Entrada | Salida | Uso principal |
| --- | --- | --- | --- |
| `POST /api/v1/auth/login` | JSON con `email` y `password` | Cookie `HttpOnly` + body mínimo | Navegador principal |
| `POST /api/v1/auth/token` | Formulario OAuth2 con `username` y `password` | Bearer token en body | Swagger, tests y clientes técnicos |

La diferencia importante es dónde queda el token:

```text
/auth/login
   └── JWT en cookie HttpOnly
       └── JavaScript no lo lee directamente

/auth/token
   └── JWT en body JSON
       └── el cliente técnico debe custodiarlo como secreto
```

Por eso `/auth/token` no debe convertirse en el flujo principal del frontend browser. Si una aplicación web recibe este token y lo guarda en `localStorage`, vuelve a abrir el riesgo que se quiso evitar con las cookies `HttpOnly`: un XSS podría leerlo y exfiltrarlo.

La recomendación de uso es clara:

- navegador principal: `/auth/login` con cookie `HttpOnly`;
- Swagger/OpenAPI: `/auth/token` para poder autorizar llamadas desde la documentación interactiva;
- tests y clientes técnicos: `/auth/token` cuando necesiten bearer explícito;
- no guardar el bearer token en `localStorage` como estrategia de sesión browser.

### Reutilización de `LoginService`

Una decisión importante fue no duplicar la lógica de autenticación.

`/auth/token` reutiliza el mismo `LoginService` que el login con cookie. Eso significa que comparte:

- búsqueda del usuario por email normalizado;
- comprobación de estado activo;
- verificación de password con el hasher configurado;
- emisión del access token JWT con los mismos claims mínimos;
- errores genéricos ante credenciales inválidas;
- auditoría conceptual de login, si está configurada por el servicio.

El flujo queda así:

```text
Cliente técnico / Swagger
   │
   │ POST /api/v1/auth/token
   │ username + password form-urlencoded
   ▼
Router /auth/token
   │
   ├── recibe OAuth2PasswordRequestForm
   ├── crea LoginRequest(email=username, password=password)
   └── llama a LoginService
           │
           ├── verifica usuario y password
           ├── emite access token JWT
           └── devuelve token al router
   │
   ▼
Response JSON con access_token bearer
```

Esto evita dos sistemas paralelos de credenciales. Si en el futuro cambia la política de verificación de contraseña, estado de usuario o emisión de JWT, ambos flujos se benefician del mismo cambio.

### Errores esperados

Ante credenciales inválidas, el endpoint responde con un `401 Unauthorized` genérico:

```json
{
  "detail": "Credenciales inválidas."
}
```

La respuesta no debe distinguir si:

- el email no existe;
- el usuario no está activo;
- la contraseña es incorrecta.

Esa decisión evita dar pistas útiles para enumeración de usuarios o ataques de fuerza bruta.

En la implementación existe además la posibilidad de deshabilitar este endpoint mediante configuración. Si está deshabilitado, el backend lo bloquea antes de autenticar credenciales y responde con un error controlado. Esta capacidad encaja con la idea de tratar `/auth/token` como herramienta técnica, no como requisito obligatorio para todos los entornos.

### Relación con CSRF

`/auth/token` no crea cookie y no se autentica usando una cookie previa. Por eso no utiliza la protección CSRF diseñada para mutaciones autenticadas con cookie.

Esto no contradice la task anterior. CSRF protege el caso en el que el navegador envía automáticamente una cookie de sesión. Aquí el cliente está pidiendo explícitamente un bearer token mediante credenciales de formulario y el resultado se devuelve en el body.

La separación queda así:

| Flujo | Usa cookie de sesión | Necesita CSRF en esta task |
| --- | --- | --- |
| `/auth/login` | Crea cookie | No, es autenticación inicial |
| `/auth/csrf` | Lee cookie | No como header, emite token CSRF |
| `/auth/logout` | Usa cookie | Sí, al ser mutación autenticada con cookie |
| `/auth/token` | No crea ni usa cookie | No, devuelve bearer técnico |

### Riesgos y precauciones

El riesgo principal de `/auth/token` es que entrega el JWT en el body. Esto es correcto para OAuth2 Password Bearer y útil para Swagger, pero obliga a tratar el token como secreto.

Precauciones importantes:

- no registrar el `access_token` en logs;
- no pegar tokens reales en documentación, tickets o capturas compartidas;
- no guardarlo en `localStorage` ni convertirlo en sesión browser principal;
- limitar su uso a Swagger, tests, automatizaciones controladas y clientes técnicos;
- deshabilitarlo por configuración en entornos donde no se quiera exponer este flujo;
- recordar que, sin revocación server-side, el token seguirá siendo válido hasta su expiración si alguien lo copia.

En la task histórica, el endpoint nació sin rate limiting específico. Esa protección pertenece a tareas posteriores de endurecimiento, por lo que no debe asumirse como parte de este punto concreto aunque el código haya evolucionado después.

### Limitaciones o compromisos

Esta task se mantuvo deliberadamente acotada. Sus límites principales son:

- **sin refresh token**: solo se emite access token;
- **sin scopes avanzados OAuth2**: no se modelan permisos por scope en este punto;
- **sin MFA**: no añade segundo factor ni step-up authentication;
- **sin rate limiting en esta task histórica**: la protección contra abuso se deja para hardening posterior;
- **sin revocación server-side**: no se añade blacklist ni tabla de sesiones revocables;
- **sin gestión avanzada de clientes OAuth2**: no hay client IDs, client secrets ni consent screen;
- **sin selección de tenant**: no acepta `organization_id` ni permite cambiar de organización activa desde este endpoint.

Estas limitaciones son coherentes con el objetivo: compatibilidad OAuth2/OpenAPI para desarrollo y clientes técnicos, no un servidor OAuth2 completo.

### Qué NO hace

Para evitar confusiones, `POST /api/v1/auth/token` no hace lo siguiente:

- no crea usuarios;
- no registra organizaciones;
- no crea cookie `HttpOnly`;
- no borra cookies;
- no emite token CSRF;
- no valida CSRF;
- no cambia el tenant efectivo;
- no acepta `organization_id` enviado por el cliente como selector de organización;
- no devuelve roles, permisos, email, perfil ni `password_hash`;
- no sustituye al flujo browser seguro basado en `/auth/login`.

### Resultado de la task

El resultado es que el backend gana compatibilidad OAuth2/OpenAPI sin romper la estrategia de navegador basada en cookies `HttpOnly`.

El mapa queda así:

```text
Navegador principal
   └── POST /api/v1/auth/login
       └── JWT en cookie HttpOnly

Swagger / cliente técnico
   └── POST /api/v1/auth/token
       └── JWT en body como bearer
```

En resumen: **BACK-AUTH-OAUTH2-008 añade `POST /api/v1/auth/token` para que Swagger, tests y clientes técnicos puedan usar un bearer token compatible con OAuth2 password/form, reutilizando `LoginService` y manteniendo separado el flujo browser seguro basado en cookie `HttpOnly`**.

## 8. BACK-AUTH-OAUTH2-009 — CORS

### Qué problema resuelve

Hasta este punto, el backend ya tenía un flujo de autenticación para navegador basado en cookie `HttpOnly`, un endpoint `/auth/me`, logout protegido con CSRF y un endpoint técnico `/auth/token` para Swagger y clientes controlados.

Pero había una pieza necesaria para que un frontend ejecutado en navegador pudiera llamar a la API desde otro origen durante desarrollo o staging: **CORS**.

CORS significa **Cross-Origin Resource Sharing**. Es una política aplicada por los navegadores para decidir si una página cargada desde un origen puede leer respuestas de otro origen.

Ejemplo conceptual:

```text
Frontend local
http://localhost:5173

Backend API
http://localhost:8000
```

Aunque ambos estén en la misma máquina, para el navegador son orígenes distintos porque cambia el puerto. Si el backend no responde con las cabeceras CORS adecuadas, el navegador bloquea la llamada desde el frontend.

El problema es más delicado cuando usamos cookies. Para que el navegador pueda enviar cookies en una llamada cross-origin controlada, no basta con “activar CORS”. Hay que configurar CORS de forma explícita y permitir credenciales. Además, cuando hay credenciales, no se debe usar `*` como origin permitido en producción.

> [!IMPORTANT]
> CORS no es autenticación ni autorización. CORS no decide quién es el usuario ni qué puede hacer. CORS solo indica al navegador desde qué orígenes se permite interactuar con la API y leer sus respuestas.

### Qué hace esta task

Esta task centraliza la configuración CORS del backend usando `CORSMiddleware` de FastAPI/Starlette.

La configuración queda encapsulada en:

```text
backend/app/core/cors.py
```

con dos responsabilidades principales:

```text
configure_cors(app, settings)
   └── registra CORSMiddleware en la aplicación FastAPI

build_allowed_cors_headers(settings)
   └── construye la lista explícita de headers permitidos
```

La idea es que el arranque de la aplicación no tenga reglas CORS dispersas por varios routers. CORS es una política transversal de la API, por eso se configura en el core de la aplicación.

En términos prácticos, esta task define:

- orígenes permitidos desde settings/entorno;
- credenciales habilitadas cuando aplica el flujo con cookies;
- métodos HTTP permitidos de forma explícita;
- headers permitidos de forma explícita;
- rechazo de wildcard `*` como origin permitido;
- separación entre configuración CORS y configuración sensible de autenticación.

### Orígenes permitidos

Los orígenes permitidos se cargan desde `CorsSettings`, no se escriben directamente dentro del middleware.

Por defecto, para desarrollo local, se contemplan los orígenes habituales del frontend:

```text
http://localhost:3000
http://localhost:5173
http://127.0.0.1:3000
http://127.0.0.1:5173
```

Esto permite trabajar con servidores locales típicos sin abrir la API a cualquier web.

En un entorno de staging, el mismo concepto se aplicaría con el dominio real correspondiente:

```text
https://staging.guakamole.example
```

La regla importante es que los orígenes deben ser **explícitos**. No se acepta:

```text
*
```

Usar wildcard con cookies y credenciales es una mala práctica porque convierte la política CORS en demasiado permisiva y dificulta razonar sobre qué aplicaciones de navegador pueden interactuar con la API.

> [!WARNING]
> `allow_credentials=True` y origins abiertos no deben combinarse. Si el backend trabaja con cookies de sesión, los origins deben estar controlados desde configuración.

### Credenciales y cookies

Como el flujo principal de navegador usa cookie `HttpOnly`, CORS debe permitir credenciales cuando el frontend autorizado necesite llamar al backend con sesión.

La configuración contempla:

```text
cors_allow_credentials = true
```

Conceptualmente, esto permite que el navegador incluya credenciales, como cookies, en las llamadas cross-origin permitidas.

La relación con las tasks anteriores es directa:

- `POST /api/v1/auth/login` crea la cookie `guak_access_token` como `HttpOnly`;
- el navegador debe poder enviar esa cookie a endpoints como `/auth/me` cuando el frontend autorizado llama a la API;
- las mutaciones protegidas deben enviar también `X-CSRF-Token`;
- CORS debe permitir ese header para que el navegador no bloquee la petición antes de llegar al backend.

Esto no significa que CORS autentique la petición. La autenticación sigue dependiendo de la cookie/JWT y la autorización seguirá dependiendo de validaciones backend, tenant context y RBAC.

### Métodos y headers permitidos

La configuración no usa comodines para métodos y headers. Se declaran de forma explícita.

Métodos permitidos:

```text
GET
POST
PUT
PATCH
DELETE
OPTIONS
```

Headers base permitidos:

```text
Content-Type
X-CSRF-Token
```

`X-CSRF-Token` es especialmente importante por la task anterior. Si el navegador va a llamar a una mutación protegida con CSRF, necesita poder enviar ese header. Si CORS no lo permite, la petición puede fallar en el navegador antes de que el backend tenga oportunidad de validar el token CSRF.

Además, el header:

```text
Authorization
```

se permite de forma configurable mediante `cors_allow_authorization_header`. Esto mantiene compatibilidad con Swagger, pruebas o clientes técnicos que usen bearer tokens, sin convertir todos los headers posibles en permitidos por defecto.

### Cómo se implantó

La implementación queda concentrada en `backend/app/core/cors.py`.

El flujo conceptual es:

```text
create_app()
   │
   ▼
CorsSettings()
   │
   ├── cors_allowed_origins
   ├── cors_allow_credentials
   └── cors_allow_authorization_header
   │
   ▼
configure_cors(app, settings)
   │
   ├── rechaza origin "*"
   ├── registra CORSMiddleware
   ├── allow_origins explícitos
   ├── allow_credentials según settings
   ├── allow_methods explícitos
   └── allow_headers explícitos
```

`CorsSettings` permite cargar `cors_allowed_origins` como lista o como cadena separada por comas. Esto facilita configurarlo desde variables de entorno sin cambiar código.

Ejemplo conceptual de configuración local:

```dotenv
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_AUTHORIZATION_HEADER=true
```

El detalle relevante es que `CorsSettings` está separado de `AuthSettings`. Así, configurar CORS y arrancar la aplicación no obliga a cargar secretos de autenticación como `JWT_SECRET_KEY` si solo se está construyendo la app y registrando middleware.

### Relación con cookie HttpOnly, CSRF y entornos

CORS encaja con el resto de la fase OAuth2 como una pieza de integración segura para navegador.

La cookie `HttpOnly` protege el access token frente a lectura directa desde JavaScript, pero el navegador necesita permiso CORS para enviar y recibir respuestas cuando frontend y backend están en orígenes distintos.

CSRF cubre otro problema: que una mutación con cookie automática demuestre también intención mediante `X-CSRF-Token`. Por eso CORS debe permitir ese header, pero no lo valida. La validación CSRF sigue siendo responsabilidad del backend.

En local, los origins suelen ser `localhost` o `127.0.0.1` con puertos de desarrollo. En staging, deben configurarse los dominios reales. En producción, la lista debe ser todavía más estricta y no debe depender de comodines.

Resumen de responsabilidades:

| Pieza | Responsabilidad |
| --- | --- |
| Cookie `HttpOnly` | Guardar el access token sin exponerlo directamente a JavaScript. |
| CORS | Permitir al navegador llamar a la API desde origins autorizados. |
| CSRF | Proteger mutaciones autenticadas con cookie mediante `X-CSRF-Token`. |
| Auth/RBAC/Tenant | Validar usuario, permisos y aislamiento de organización en backend. |

### Beneficios

Esta task aporta varios beneficios claros:

- **Integración browser controlada**: el frontend local o de staging puede llamar a la API sin desactivar protecciones del navegador.
- **Origins explícitos**: se evita abrir la API con `*`.
- **Credenciales configuradas correctamente**: el flujo con cookie `HttpOnly` puede funcionar desde origins permitidos.
- **Compatibilidad con CSRF**: se permite `X-CSRF-Token` para mutaciones protegidas.
- **Headers acotados**: no se permite cualquier header por comodidad.
- **Configuración centralizada**: CORS se aplica en un punto común del arranque de FastAPI.
- **Menos acoplamiento**: la configuración CORS puede cargarse sin depender de secretos JWT.

### Limitaciones y riesgos

CORS tiene límites importantes que conviene entender bien:

- **No protege contra requests server-to-server**: CORS lo aplican los navegadores. Un cliente backend, script o herramienta HTTP puede enviar requests sin estar limitado por CORS.
- **No sustituye CSRF**: aunque el origin esté permitido, una mutación con cookie debe seguir validando `X-CSRF-Token` cuando corresponda.
- **No sustituye RBAC ni tenant isolation**: que una petición pase CORS no significa que el usuario tenga permiso para acceder al recurso.
- **No autentica usuarios**: CORS no valida cookies, JWT ni bearer tokens.
- **Mala configuración puede abrir riesgos**: permitir origins de más o usar comodines en entornos con credenciales reduce el control sobre qué frontends pueden interactuar con la API desde navegador.
- **Requiere mantenimiento por entorno**: local, staging y producción deben tener listas de origins coherentes con sus dominios reales.

### Qué NO hace

Para evitar confusiones, esta task no hace lo siguiente:

- no valida usuario;
- no crea sesión;
- no emite JWT;
- no crea ni borra cookies;
- no valida CSRF;
- no protege endpoints por sí sola;
- no aplica RBAC;
- no filtra tenant;
- no decide si un usuario de ACME puede acceder a datos de CyberCorp;
- no convierte `/auth/token` en flujo principal de navegador;
- no evita ataques desde clientes server-to-server.

CORS responde a una pregunta concreta del navegador: “¿puede una página cargada desde este origin llamar a esta API y leer la respuesta?”. El resto de decisiones de seguridad siguen viviendo en backend.

### Resultado de la task

El resultado es que el backend queda preparado para integrarse con un frontend de navegador usando cookies `HttpOnly` sin abrir CORS de forma insegura.

El flujo conceptual queda así:

```text
Frontend en origin permitido
   │
   ├── llama a la API con credentials
   ├── puede enviar cookie HttpOnly si corresponde
   ├── puede enviar X-CSRF-Token en mutaciones protegidas
   ▼
Backend FastAPI
   │
   ├── CORSMiddleware valida origin/header/método a nivel navegador
   ├── auth valida cookie/JWT o bearer según endpoint
   ├── CSRF valida mutaciones con cookie
   └── RBAC/tenant deberán validar permisos y aislamiento
```

En resumen: **BACK-AUTH-OAUTH2-009 configura CORS de forma centralizada, explícita y compatible con cookies, evitando wildcard y dejando el backend listo para frontend browser local/staging sin confundir CORS con autenticación, CSRF, RBAC ni aislamiento multi-tenant**.

## 9. BACK-AUTH-OAUTH2-010 — Hardening final

### Qué problema resuelve

Antes de cerrar la fase OAuth2 no bastaba con que los endpoints funcionasen. Había que revisar si la configuración de autenticación, cookies, JWT, CORS y CSRF estaba suficientemente endurecida para no depender de defaults inseguros ni de decisiones dispersas.

El problema principal era evitar situaciones como estas:

- arrancar un entorno real con un secreto JWT ausente, vacío o gestionado de forma accidental;
- emitir cookies con atributos distintos entre login y logout;
- dejar CORS demasiado abierto por comodidad;
- aceptar parámetros de autenticación no previstos;
- devolver errores demasiado informativos ante credenciales o tokens inválidos;
- mezclar configuración de desarrollo con configuración esperada para staging o producción.

Esta task actúa como cierre de seguridad de la fase: revisa lo ya construido y consolida las reglas que deben mantenerse en los siguientes módulos.

> [!IMPORTANT]
> Hardening no significa añadir muchas funcionalidades nuevas. Significa reducir superficie de ataque, eliminar ambigüedades y asegurarse de que las piezas críticas fallan de forma segura cuando la configuración no es válida.

### Qué hace esta task

El hardening final revisa y centraliza la configuración real de:

- autenticación;
- cookies de sesión;
- JWT de acceso;
- CORS;
- CSRF;
- errores de credenciales y tokens;
- diferencias entre entorno local, test, staging y producción.

No cambia el objetivo funcional de la fase. El flujo principal sigue siendo:

```text
POST /api/v1/auth/login
   └── JWT en cookie HttpOnly

GET /api/v1/auth/me
   └── identidad pública mínima

POST /api/v1/auth/logout
   └── borrado de cookie

POST /api/v1/auth/token
   └── bearer token para Swagger/clientes técnicos
```

Por tanto, cuando se habla de mantener el token fuera del body se refiere al flujo browser principal con `POST /api/v1/auth/login`: ese endpoint autentica al navegador mediante cookie `HttpOnly` y no devuelve el JWT en la respuesta JSON. En cambio, `POST /api/v1/auth/token` sí devuelve un bearer token de forma intencionada para Swagger y clientes técnicos; ese token debe tratarse como un secreto y no almacenarse ni registrarse de forma insegura.

Lo que hace esta task es reforzar que esos flujos usen configuración coherente y no se degraden por defaults cómodos pero peligrosos.

### Secretos y configuración sensible

La regla principal es que los secretos no deben estar hardcodeados en el código ni guardados como valores reales en el repositorio.

En la implementación actual, `AuthSettings` exige `JWT_SECRET_KEY` para poder construir la configuración completa de autenticación. También acepta el alias legado `JWT_SECRET`, pero da prioridad a `JWT_SECRET_KEY`. Esto permite compatibilidad durante la fase sin convertir un nombre antiguo en la referencia principal.

La decisión importante implementada es esta:

```text
Sin `JWT_SECRET_KEY` configurado de forma suficiente para pasar la validación actual
   └── la configuración de auth debe fallar
```

La implementación actual exige que `JWT_SECRET_KEY` exista y cumpla la validación básica configurada, pero no debe interpretarse como un control completo de calidad criptográfica del secreto. En concreto, no se documenta como enforcement implementado el rechazo específico de valores débiles conocidos como `secret`, `changeme` o `dev-secret`. Evitar esos valores sigue siendo una responsabilidad de configuración del entorno y queda como recomendación/deuda de hardening adicional si se quiere automatizar con una denylist o una política de entropía más estricta.

Es preferible que un entorno mal configurado no arranque a firmar tokens sin un secreto explícito, y que staging/producción utilicen secretos reales gestionados fuera del repositorio.

Separación esperada por entorno:

| Entorno | Criterio |
| --- | --- |
| Test | Puede usar secretos de prueba, explícitos y no reutilizables fuera de tests. |
| Desarrollo local | Puede relajar TLS/cookie `Secure`, pero debe seguir usando configuración explícita. |
| Staging | Debe parecerse a producción: secretos reales, origins concretos y cookies seguras si hay HTTPS. |
| Producción | Debe usar secretos gestionados fuera del repositorio, TLS y configuración estricta. |

> [!WARNING]
> Los valores de ejemplo sirven para documentar variables, no para operar entornos reales. Un secreto de test o local no debe promocionarse a staging o producción.

### Cookies de autenticación

El flujo browser usa una cookie de autenticación para transportar el access token. Por eso la configuración de cookies es una parte crítica del hardening.

La cookie se construye de forma centralizada mediante `build_auth_cookie_settings`, a partir de `AuthSettings`. Esto evita que cada endpoint decida atributos por su cuenta.

Atributos relevantes:

| Atributo | Decisión |
| --- | --- |
| `HttpOnly` | Activado para que JavaScript no pueda leer directamente el token. |
| `SameSite` | Configurable y restringido a valores válidos: `lax`, `strict` o `none`. |
| `Secure` | Configurable: puede relajarse en local, debe activarse con HTTPS en entornos reales. |
| `Path` | Por defecto `/api`, coherente con la API backend. |
| `Domain` | Opcional, solo si el despliegue lo necesita. |
| `Max-Age` | Derivado de la expiración del access token. |

Esta centralización es importante por dos motivos:

- login y logout usan los mismos atributos relevantes;
- la expiración de cookie acompaña a la expiración del token y no queda como un valor suelto.

Ejemplo conceptual:

```text
ACCESS_TOKEN_EXPIRE_MINUTES=15
   └── Max-Age cookie = 900 segundos
```

La cookie `HttpOnly` reduce exposición ante XSS porque el token no queda accesible mediante `document.cookie`. Aun así, al usar cookies, el backend necesita CSRF en mutaciones autenticadas y CORS bien acotado.

### JWT de acceso

El JWT de la fase OAuth2 se mantiene deliberadamente pequeño. No se usa como contenedor de perfil, permisos o datos personales.

Claims usados en el token:

```json
{
  "sub": "usr_...",
  "org": "org_...",
  "type": "access",
  "jti": "...",
  "iat": 1760000000,
  "exp": 1760000900
}
```

La task refuerza estas reglas:

- expiración corta, controlada por `ACCESS_TOKEN_EXPIRE_MINUTES`;
- tipo de token obligatorio mediante `type=access`;
- `sub` como usuario público, no ID interno;
- `org` como organización pública cuando el flujo autenticado lo requiere;
- `jti` preparado para trazabilidad o revocación futura;
- `iat` y `exp` obligatorios;
- algoritmo restringido a los permitidos por configuración del MVP;
- sin contraseñas, emails, roles completos, permisos detallados ni datos sensibles en el payload.

> [!NOTE]
> Un JWT firmado permite confiar en que el backend lo emitió, pero no sustituye la autorización. Cada endpoint debe seguir validando usuario, organización, permisos y alcance real en backend.

En esta fase no se documenta `issuer` o `audience` como requisito implementado. Si el sistema evoluciona hacia múltiples emisores, clientes o servicios consumidores, esos claims deberían añadirse como parte de un diseño posterior de tokens.

### CORS y CSRF

El hardening confirma que CORS y CSRF trabajan juntos, pero resuelven problemas distintos.

CORS:

- se configura en `backend/app/core/cors.py`;
- usa origins explícitos;
- rechaza `*` como origin permitido;
- permite credenciales cuando el flujo browser necesita cookies;
- acota métodos y headers;
- permite `X-CSRF-Token` para mutaciones protegidas;
- permite `Authorization` de forma configurable para Swagger/clientes técnicos.

CSRF:

- protege mutaciones autenticadas con cookie;
- exige intención explícita mediante header `X-CSRF-Token` cuando aplica;
- no sustituye autenticación, autorización ni validación de tenant.

La regla de seguridad es sencilla:

```text
Cookie automática del navegador
   +
Mutación autenticada
   └── requiere protección CSRF

Frontend en otro origin
   └── requiere CORS explícito, no wildcard
```

En local se permiten origins de desarrollo como `localhost` o `127.0.0.1` con puertos habituales. En staging y producción deben configurarse dominios concretos. No debe usarse una lista abierta para ahorrar configuración.

### Errores y respuestas públicas

El hardening mantiene la regla de no dar pistas innecesarias cuando fallan credenciales o tokens.

Ejemplos de errores que deben parecer genéricos desde fuera:

- email inexistente;
- contraseña incorrecta;
- usuario inactivo;
- cookie ausente;
- token expirado;
- token manipulado;
- token con tipo incorrecto;
- token sin claims obligatorios.

Para el cliente, todos esos casos significan algo parecido:

```text
No hay una sesión válida usable.
```

El backend puede registrar internamente más detalle cuando exista auditoría completa, pero la respuesta pública no debe ayudar a enumerar usuarios, distinguir estados de cuenta o descubrir reglas internas de validación.

### Configuración por entorno

La configuración no debe ser idéntica en todos los entornos, pero sí debe ser explícita y razonada.

En desarrollo local se aceptan algunas concesiones:

- `AUTH_COOKIE_SECURE=false` si no hay HTTPS local;
- origins locales concretos para Vite u otros servidores de desarrollo;
- secretos de desarrollo no reales y no compartidos con entornos superiores.

En staging y producción se espera endurecimiento:

- `AUTH_COOKIE_SECURE=true` detrás de TLS;
- origins CORS exactos;
- secretos externos al repositorio;
- expiraciones coherentes con el riesgo de sesión;
- ningún wildcard en CORS;
- ningún secreto de ejemplo;
- configuración revisable y reproducible.

Esto permite que el equipo trabaje en local sin bloquearse, pero deja clara la diferencia entre comodidad de desarrollo y política segura para entornos expuestos.

### Beneficios

El hardening final aporta beneficios concretos al backend:

- reduce el riesgo de firmar tokens sin un secreto explícito, aunque la detección automática de secretos débiles concretos queda pendiente como hardening adicional;
- evita atributos de cookie inconsistentes entre endpoints;
- mantiene el access token fuera del body en el flujo browser principal;
- reduce exposición del token frente a JavaScript mediante `HttpOnly`;
- limita CORS a origins explícitos;
- evita aceptar comodines peligrosos con credenciales;
- mantiene respuestas genéricas ante credenciales o tokens inválidos;
- conserva un JWT mínimo y sin datos sensibles;
- separa configuración de test, desarrollo y entornos reales;
- deja la fase OAuth2 preparada para módulos posteriores de autorización, tenant context y auditoría.

### Limitaciones o deuda técnica

Este cierre mejora la seguridad de la fase OAuth2, pero no convierte la autenticación en un sistema completo de seguridad empresarial.

Limitaciones asumidas:

- no sustituye MFA/TOTP;
- no implementa rotación de claves JWT;
- no añade refresh tokens;
- no añade revocación server-side de tokens;
- no completa auditoría persistente de todos los eventos;
- no implementa gestión avanzada de secretos si la infraestructura todavía no la aporta;
- no rechaza de forma específica valores débiles conocidos para `JWT_SECRET_KEY` como `secret`, `changeme` o `dev-secret`; esa política debe aplicarse por configuración del entorno o añadirse en una validación futura;
- no resuelve por sí solo rate limiting, que queda como punto específico posterior;
- no sustituye revisiones de seguridad de despliegue, TLS, proxy o cabeceras HTTP globales.

También queda pendiente evolucionar el modelo si aparecen necesidades como `issuer`, `audience`, múltiples clientes OAuth2, sesiones revocables o rotación automática de secretos.

### Qué NO hace

Para evitar confusiones, esta task no hace lo siguiente:

- no implementa RBAC completo;
- no cambia el modelo multi-tenant;
- no añade frontend;
- no cambia el contrato principal de login, logout, `/auth/me` o `/auth/token`;
- no introduce MFA;
- no añade refresh tokens;
- no implementa blacklist de JWT;
- no convierte CORS en autorización;
- no sustituye CSRF;
- no añade auditoría completa si todavía no existe;
- no implementa rate limiting, que se documenta como punto separado de la fase.

### Resultado de la task

El resultado es que la fase OAuth2 queda más segura y configurable para los siguientes módulos del backend.

La fase mantiene una estrategia clara:

```text
Secretos
   └── no hardcodeados y obligatorios para auth real

Cookies
   └── HttpOnly, Path coherente, SameSite validado, Secure configurable, Max-Age derivado

JWT
   └── expiración corta, claims mínimos, sin datos sensibles

CORS
   └── origins explícitos, sin wildcard, compatible con credenciales

CSRF
   └── protección para mutaciones con cookie

Errores
   └── respuestas genéricas ante credenciales o tokens inválidos
```

En resumen: **BACK-AUTH-OAUTH2-010 cierra la fase OAuth2 desde el punto de vista de hardening, evitando defaults inseguros y dejando autenticación, cookies, JWT, CORS y CSRF con una configuración centralizada y revisable. El flujo browser principal con `/auth/login` mantiene el token fuera del body, mientras que `/auth/token` expone un bearer token de forma intencionada para clientes técnicos y debe tratarse como secreto**.

## 10. BACK-AUTH-OAUTH2-011 — Rate limiting

### Qué problema resuelve

Los endpoints públicos de autenticación y registro son una de las superficies más sensibles del backend. Aunque las contraseñas estén hasheadas, los tokens estén bien firmados y los errores sean genéricos, un atacante puede intentar abusar de esos endpoints enviando muchas peticiones seguidas.

El problema principal es el abuso básico contra operaciones como:

- probar muchas combinaciones de email y contraseña contra el login;
- solicitar repetidamente tokens bearer en el endpoint OAuth2;
- automatizar altas de organizaciones para hacer scraping, spam o consumo innecesario de recursos;
- forzar trabajo caro del backend, como verificación de contraseñas o creación de entidades.

Sin rate limiting, cada petición llegaría directamente al caso de uso correspondiente. Eso significa que el backend tendría que procesar intentos abusivos igual que procesa intentos legítimos.

> [!IMPORTANT]
> El rate limiting no convierte un endpoint inseguro en seguro por sí solo. Su función es reducir la exposición ante abuso repetitivo y fuerza bruta básica. Sigue siendo necesario mantener contraseñas seguras, errores genéricos, MFA cuando exista, auditoría, CSRF, CORS correcto y validación server-side.

### Qué hace esta task

Esta task añade un rate limiting backend básico, implementado en memoria, para endpoints públicos sensibles de la fase OAuth2.

La pieza central es:

```text
backend/app/core/rate_limit.py
```

Desde ahí se definen:

- `RateLimitSettings`, con la configuración del rate limiter;
- `RateLimitRule`, que representa una regla de límite y ventana temporal;
- `InMemoryRateLimiter`, que guarda contadores en memoria;
- dependencias específicas para aplicar límites a login, token y registro.

La protección se integra como dependencia de FastAPI en los routers. Esto es importante porque el límite se evalúa antes de ejecutar los servicios de negocio. Si una petición supera el límite, no llega a validar credenciales, no ejecuta hashing de contraseña, no emite tokens y no crea entidades de registro.

Conceptualmente:

```text
Request HTTP
   │
   ▼
Dependencia de rate limit
   │
   ├── permitido → continúa al router y al servicio
   │
   └── excedido  → responde 429 Too Many Requests
```

### Endpoints protegidos

La implementación protege estos endpoints:

| Endpoint | Motivo | Límite por defecto |
| --- | --- | --- |
| `POST /api/v1/auth/login` | Reducir fuerza bruta contra email/password. | 5 peticiones cada 60 segundos. |
| `POST /api/v1/auth/token` | Reducir abuso del flujo bearer OAuth2 para clientes técnicos. | 5 peticiones cada 60 segundos. |
| `POST /api/v1/organizations/register` | Reducir registros automatizados, spam o scraping de alta. | 3 peticiones cada 300 segundos. |

Quedan fuera de esta task:

- `GET /api/v1/auth/me`;
- `GET /api/v1/auth/csrf`;
- `POST /api/v1/auth/logout`.

La decisión es práctica: se priorizan los endpoints públicos que reciben credenciales o crean datos nuevos. `/auth/me`, `/auth/csrf` y `/auth/logout` tienen otros perfiles de riesgo y no forman parte del alcance concreto de esta protección inicial.

### Clave de rate limit

La clave usada por el limiter es simple y explícita:

```text
scope:path:client_host
```

En la implementación real se construye con:

- el `scope` de la regla, por ejemplo `auth_login`, `auth_token` o `registration`;
- la ruta HTTP real, por ejemplo `/api/v1/auth/login`;
- `request.client.host`, es decir, la IP cliente vista directamente por FastAPI.

Ejemplo conceptual:

```text
auth_login:/api/v1/auth/login:127.0.0.1
```

No se usan como parte de la clave:

- email;
- username;
- password;
- token;
- payload completo;
- `organization_id`.

Esto evita que el rate limiter dependa de datos sensibles o de campos enviados por el cliente. También mantiene los errores genéricos: el backend no debe dar pistas sobre si un email existe o no existe.

> [!WARNING]
> La implementación no confía todavía en cabeceras como `X-Forwarded-For`. Eso queda pendiente de una estrategia segura con reverse proxy y proxies de confianza. Confiar en esa cabecera sin control puede permitir que un cliente falsee su IP.

### Respuesta cuando se supera el límite

Cuando una petición excede el límite configurado, el backend responde con:

```http
429 Too Many Requests
```

El cuerpo de respuesta es genérico:

```json
{
  "detail": "Demasiadas solicitudes. Inténtalo más tarde."
}
```

Esta respuesta no incluye email, usuario, organización, token ni ningún dato que ayude a enumerar cuentas.

Si el tiempo restante de espera es calculable, se devuelve también la cabecera:

```http
Retry-After: <segundos>
```

No se documentan otros headers de rate limit porque la implementación no los emite. En este punto no existen cabeceras tipo límite total, peticiones restantes o reset de ventana.

### Configuración por settings y entorno

La configuración se carga desde `RateLimitSettings`, separada de la configuración JWT. Esto evita mezclar secretos de autenticación con política de limitación de tráfico.

Variables principales:

```dotenv
RATE_LIMIT_ENABLED=true

AUTH_LOGIN_RATE_LIMIT_REQUESTS=5
AUTH_LOGIN_RATE_LIMIT_WINDOW_SECONDS=60

AUTH_TOKEN_RATE_LIMIT_REQUESTS=5
AUTH_TOKEN_RATE_LIMIT_WINDOW_SECONDS=60

REGISTRATION_RATE_LIMIT_REQUESTS=3
REGISTRATION_RATE_LIMIT_WINDOW_SECONDS=300
```

`RATE_LIMIT_ENABLED` permite activar o desactivar la protección. En la implementación real su valor por defecto es `true`. En entornos de desarrollo o pruebas puede desactivarse de forma explícita si hace falta aislar un caso concreto, pero la política segura para staging y producción debe ser mantenerlo activado y ajustar los límites con cuidado.

La diferencia importante entre entornos no está en que el código cambie, sino en la configuración:

- en desarrollo puede interesar relajar o desactivar temporalmente el límite para depuración;
- en tests se puede limpiar el estado del limiter para aislar casos;
- en staging y producción debe estar activo y revisado según tráfico real;
- en producción futura debería migrarse a una solución distribuida si hay múltiples workers o instancias.

### Por qué se implementó in-memory

El limiter actual es deliberadamente sencillo: guarda los contadores en memoria dentro del proceso del backend y usa una ventana fija.

Esto encaja con el objetivo de la fase MVP porque:

- reduce riesgo básico sin introducir todavía Redis como dependencia obligatoria;
- mantiene la implementación fácil de entender para el equipo;
- permite proteger login, token y registro sin rediseñar la arquitectura;
- evita acoplar los servicios de dominio a una herramienta externa.

Además, se añadió protección de concurrencia mediante `threading.Lock` para que el contador in-memory no quede expuesto a condiciones de carrera dentro del mismo proceso.

### Beneficios

El cambio aporta una capa defensiva útil sobre la fase OAuth2:

- reduce la fuerza bruta básica contra `POST /api/v1/auth/login`;
- reduce el abuso del endpoint `POST /api/v1/auth/token`;
- dificulta el scraping o spam de `POST /api/v1/organizations/register`;
- evita ejecutar lógica cara cuando una IP ya ha superado el límite;
- mantiene respuestas genéricas que no filtran existencia de usuarios;
- centraliza la política de límites en `backend/app/core/rate_limit.py`;
- deja los endpoints OAuth2 públicos menos expuestos ante abuso automatizado simple.

### Limitaciones asumidas

La solución tiene límites claros y deben entenderse como deuda técnica aceptada para MVP/desarrollo:

- **In-memory**: el estado se pierde al reiniciar el proceso.
- **No distribuido**: no comparte contadores entre varios procesos, workers o instancias.
- **No usa Redis**: por tanto no es todavía la solución adecuada para una arquitectura escalada.
- **Clave por IP vista por FastAPI**: si hay proxy delante, hace falta una estrategia segura para obtener la IP real.
- **Bypass con IP rotativas**: un atacante con muchas IPs puede repartir el tráfico.
- **Ventana fija simple**: puede permitir ráfagas cerca del borde de una ventana temporal.
- **No es adaptativo**: no cambia límites según reputación, comportamiento o riesgo.
- **No limita por cuenta concreta**: la clave no incluye email ni usuario para no introducir filtrado de datos sensibles en esta fase.

Estas limitaciones no hacen inútil la protección. Simplemente delimitan qué problema resuelve: abuso básico y repetitivo contra endpoints públicos sensibles.

### Relación con otras medidas de seguridad

El rate limiting complementa, pero no sustituye, otras defensas.

Sigue siendo importante:

- mantener errores genéricos en login y token;
- no revelar si un email existe;
- hashear contraseñas con Argon2id;
- mantener cookies `HttpOnly` para el flujo browser;
- proteger mutaciones con CSRF cuando usen cookie;
- configurar CORS de forma explícita;
- añadir MFA cuando la fase lo contemple;
- evaluar lockout temporal de cuentas si se diseña con cuidado;
- registrar auditoría de eventos relevantes;
- usar WAF, reverse proxy y controles perimetrales cuando existan.

> [!NOTE]
> Bloquear demasiadas peticiones desde una IP ayuda, pero no debe convertirse en la única defensa. Un sistema de autenticación robusto combina varias capas.

### Qué NO hace

Para evitar sobreinterpretar el alcance, esta task no hace lo siguiente:

- no bloquea cuentas permanentemente;
- no implementa lockout por usuario;
- no detecta bots avanzados;
- no implementa captcha;
- no sustituye MFA;
- no sustituye auditoría de seguridad;
- no sustituye un WAF;
- no sustituye controles del reverse proxy;
- no resuelve por sí sola ataques distribuidos;
- no añade cabeceras avanzadas de cuota aparte de `Retry-After` cuando aplica;
- no cambia la semántica funcional de login, token o registro salvo por la posible respuesta `429`.

### Resultado de la task

El resultado es que los endpoints públicos más sensibles de OAuth2 y registro quedan menos expuestos a abuso básico.

La fase pasa de tener endpoints funcionales y endurecidos a tener también una primera barrera de volumen:

```text
Login
   └── limitado por IP/ruta/scope antes de validar credenciales

Token OAuth2
   └── limitado por IP/ruta/scope antes de emitir bearer token

Registro
   └── limitado por IP/ruta/scope antes de crear organización y usuario
```

En resumen: **BACK-AUTH-OAUTH2-011 añade rate limiting backend configurable para login, token y registro. Es una protección in-memory inicial, útil para MVP y desarrollo, que reduce fuerza bruta y abuso básico sin sustituir MFA, lockout, auditoría, WAF ni una futura solución distribuida con Redis**.

## 11. BACK-AUTH-OAUTH2-012 — Validación y cierre final

### Objetivo del cierre

El objetivo de esta última task no fue añadir otro endpoint ni cambiar el comportamiento de autenticación, sino **cerrar la fase OAuth2 verificando que las piezas ya construidas encajan como un flujo completo de backend**.

Hasta este punto se habían desarrollado componentes importantes por separado: registro, login, cookie `HttpOnly`, identidad actual, logout, CSRF, token OAuth2 para Swagger/clientes técnicos, CORS, hardening y rate limiting. La validación final sirve para mirar el conjunto y responder a una pregunta sencilla:

```text
¿Tenemos una base de autenticación coherente, reutilizable y razonable para el MVP?
```

La respuesta de cierre es que sí: la fase deja una base sólida para seguir construyendo IAM, endpoints autenticados y aislamiento multiempresa. Pero no debe interpretarse como un sistema IAM completo ni como una garantía absoluta de producción lista sin más trabajo.

> [!IMPORTANT]
> El resultado de esta fase es una base OAuth2/Auth razonable para el MVP. No es todavía RBAC completo, MFA, gestión avanzada de sesiones, auditoría persistente total ni hardening productivo definitivo.

### Recap del flujo completo

El flujo principal de navegador queda ordenado así:

```text
register
   │
   ▼
login con cookie HttpOnly
   │
   ▼
me
   │
   ▼
csrf
   │
   ▼
logout
```

Traducido a responsabilidades de backend:

- `POST /api/v1/organizations/register` crea la organización inicial y el primer usuario administrador, sin iniciar sesión automáticamente y sin devolver tokens.
- `POST /api/v1/auth/login` valida credenciales, emite un access token JWT mínimo y lo entrega mediante cookie `HttpOnly`.
- `GET /api/v1/auth/me` permite resolver la identidad autenticada desde la cookie, sin que el cliente tenga que leer el JWT.
- `GET /api/v1/auth/csrf` emite un token CSRF ligado a la sesión actual para proteger mutaciones autenticadas basadas en cookie.
- `POST /api/v1/auth/logout` borra la cookie de sesión desde backend y queda protegido por CSRF.

En paralelo, la fase incluye:

- `POST /api/v1/auth/token` como endpoint OAuth2 Password Bearer separado para Swagger y clientes técnicos;
- CORS configurado con origins explícitos, no con wildcard abierto;
- hardening de respuestas, contratos y configuración;
- rate limiting alrededor de endpoints sensibles de autenticación y registro.

La idea importante es que el flujo browser y el flujo técnico no se mezclan. El navegador trabaja con cookie `HttpOnly`; Swagger y determinados clientes técnicos pueden usar bearer token mediante `/auth/token` si la configuración lo permite.

### Qué se revisó conceptualmente

La validación final revisó la fase como un sistema, no como una suma de endpoints aislados.

Se revisaron especialmente estos puntos:

- **Contratos HTTP**: rutas, métodos, respuestas mínimas y separación entre flujo browser y flujo bearer.
- **Respuestas seguras**: ausencia de `password_hash`, secretos, IDs internos, access token en body del login o datos innecesarios en respuestas públicas.
- **Cookies**: uso de cookie `HttpOnly`, atributos comunes para emisión y borrado, `Path`, `SameSite`, `Secure` configurable y vida ligada a la configuración de auth.
- **JWT**: access token mínimo, claims controlados, expiración, tipo de token y uso de public IDs `usr_...` y `org_...`.
- **CSRF**: protección de mutaciones autenticadas que dependen de cookie, empezando por logout, y separación respecto a endpoints que no deben requerirlo.
- **CORS**: origins explícitos y comportamiento coherente con credenciales de navegador.
- **Errores**: mensajes controlados, sin revelar si un email existe, si una contraseña concreta falló o si un usuario interno está presente.
- **Rate limit**: defensa básica alrededor de login, token y registro para reducir fuerza bruta y abuso accidental.
- **Ausencia de datos sensibles**: no exposición de secretos, respuestas correctas, hashes, tokens innecesarios o detalles internos que faciliten enumeración.

Esta revisión confirma que las decisiones tomadas en las tasks previas no se contradicen entre sí. Por ejemplo, usar cookie `HttpOnly` implicaba añadir CSRF; separar `/auth/token` evita debilitar el contrato del login browser; y mantener respuestas pequeñas reduce el acoplamiento de futuros módulos con detalles internos de auth.

### Qué queda preparado

El cierre de OAuth2 deja preparadas varias bases para el resto del backend:

- **Endpoints autenticados futuros**: ya existe una forma de resolver identidad desde cookie/JWT y de construir contratos protegidos encima.
- **`CurrentUser` y tenant context**: `/auth/me` y los claims `sub`/`org` preparan el camino para resolver usuario efectivo y organización activa en cada petición.
- **RBAC**: la fase no implementa autorización completa, pero deja una identidad autenticada sobre la que se podrán evaluar roles, permisos y scopes.
- **Auditoría real**: login, logout, token, CSRF y accesos protegidos ya tienen puntos naturales donde emitir `AuditEvent` persistente en fases posteriores.
- **MFA**: el flujo de login queda suficientemente separado como para introducir un segundo factor sin rediseñar todo el registro o `/auth/me`.
- **Refresh token si se decide**: el sistema actual funciona con access token, pero la separación de responsabilidades permite añadir refresh token y rotación si el MVP lo necesita.
- **Invitaciones**: el registro inicial no resuelve onboarding completo, pero deja usuarios, organizaciones y sesión como base para flujos de invitación posteriores.

En otras palabras: OAuth2/Auth queda como cimiento para IAM y multi-tenant, no como el sistema IAM entero.

### Beneficios de cerrar la fase

Cerrar esta fase aporta beneficios prácticos al proyecto:

- **Autenticación reutilizable**: los siguientes módulos no tienen que improvisar cómo identificar al usuario.
- **Demo backend más sólida**: ya existe un recorrido mínimo de registro, login, consulta de sesión, CSRF y logout.
- **Menos improvisación**: RBAC, organizaciones, invitaciones, auditoría y escenarios pueden apoyarse en una base común.
- **Contratos más claros**: el equipo sabe qué endpoints existen, qué devuelve cada uno y qué no debe esperar de ellos.
- **Mejor postura de seguridad inicial**: tokens fuera del body del login, cookie `HttpOnly`, CSRF, CORS explícito y rate limiting básico.

Esto reduce el riesgo de que cada módulo futuro cree su propia manera de autenticar, validar sesión o manejar errores.

### Limitaciones y deuda pendiente

La fase queda cerrada, pero no pretende cubrir todo lo que necesitará Project Guacamole a medio plazo. Quedan pendientes de forma clara:

- **RBAC completo**: todavía no existe una autorización avanzada por roles, permisos y ámbitos.
- **Tenant context definitivo**: la organización aparece en el flujo de auth, pero falta convertirla en contexto obligatorio para todos los endpoints protegidos.
- **MFA**: no hay TOTP, segundo factor ni recovery codes.
- **Refresh token**: no se ha implementado par access/refresh ni rotación.
- **Revocación JWT server-side**: no hay blacklist, tabla de sesiones ni invalidación persistente por `jti`.
- **Auditoría persistente completa**: existen puntos conceptuales, pero falta persistir eventos reales de auditoría de forma transversal.
- **Lockout avanzado**: el rate limiting reduce abuso básico, pero no sustituye bloqueo de cuentas, detección de ataques o políticas adaptativas.
- **Gestión avanzada de secretos**: la configuración exige secretos, pero queda pendiente una estrategia madura para staging/producción.

Estas limitaciones no bloquean el MVP, pero deben estar visibles para no vender la fase como una solución final de identidad empresarial.

### Riesgos residuales

Además de la deuda funcional, hay riesgos operativos que deberán tratarse antes de entornos más exigentes:

- **Configuración de producción**: `Secure`, `SameSite`, dominios de cookie, CORS y expiraciones deben revisarse con el despliegue real.
- **Secretos fuertes**: `JWT_SECRET_KEY` y secretos asociados deben ser largos, aleatorios y gestionados fuera del repositorio.
- **Trusted headers y proxy**: si la API queda detrás de Nginx u otro reverse proxy, hay que tratar correctamente IP real y cabeceras confiables.
- **CSRF en futuras mutaciones**: cualquier endpoint autenticado con cookie que modifique estado deberá integrarse con la protección CSRF.
- **Rate limit in-memory**: la solución actual es suficiente como primera defensa MVP/dev, pero no es distribuida ni adecuada como límite definitivo si hay varios procesos o instancias.

> [!WARNING]
> El cierre de la fase no elimina la necesidad de revisar configuración por entorno. Una autenticación bien diseñada puede degradarse si se despliega con secretos débiles, CORS demasiado abierto o cookies mal configuradas.

### Resultado final

El resultado final de la fase OAuth2 es una base de autenticación backend coherente para el MVP:

```text
Registro B2B inicial
   │
   ▼
Login browser con cookie HttpOnly
   │
   ▼
Identidad actual desde backend
   │
   ▼
CSRF para mutaciones con cookie
   │
   ▼
Logout backend
   │
   ▼
Token endpoint separado para Swagger/clientes técnicos
   │
   ▼
CORS + hardening + rate limiting alrededor
```

La fase deja a Project Guacamole en una posición mejor para construir el resto del backend: IAM, multi-tenant, RBAC, auditoría, invitaciones, roadmaps, escenarios y laboratorios ya no parten de cero en autenticación.

En resumen: **BACK-AUTH-OAUTH2-012 cierra la fase OAuth2 validando que las piezas encajan como cimiento de autenticación para el MVP. El sistema queda preparado para crecer hacia IAM y aislamiento multiempresa, pero todavía no debe considerarse un IAM completo ni una solución productiva definitiva sin las fases pendientes de RBAC, auditoría, MFA, gestión de secretos y endurecimiento operativo**.

## Auditoría BACK-AUTH-OAUTH-001

### 1. Estado inicial, inventario y modelo de amenazas

#### Objetivo y estado inicial

Este punto delimita la superficie de autenticación y las amenazas que deberán contrastarse antes de valorar la eficacia de sus controles. Es un inventario de lectura, no una certificación de seguridad ni una repetición del desarrollo histórico de la fase OAuth2.

La rama de trabajo es `backend/audit/BACK-AUTH-OAUTH-001`, creada desde `main` limpio y actualizado en `ea473a2`, con la baseline hex de la PR #51 ya mergeada. La convención acordada para futuras auditorías es `backend/audit/`. Esta referencia identifica el estado de partida: **en este punto no se crea una nueva baseline**.

La propuesta del punto 1 está aprobada por arquitectura y QA. El alcance es exclusivamente documental y de lectura: no se han ejecutado tests, aplicado cambios funcionales, cargado seeds, ejecutado migraciones ni realizado operaciones destructivas. Las comprobaciones de entorno comunicadas por QA se registran por separado y no se presentan como tests de autenticación.

#### Inventario estático de la superficie HTTP

Las seis rutas inventariadas tienen el prefijo `/api/v1`. La evidencia de este apartado procede de la lectura inicial; sus contratos y controles siguen pendientes de comprobación funcional en la auditoría.

| Método y ruta | Entrada y credencial | Contrato observado | Dependencias principales |
| --- | --- | --- | --- |
| `POST /api/v1/organizations/register` | JSON con organización y usuario. | Respuesta `201` con IDs públicos y estados; no abre sesión. | Servicio de registro, repositorio SQLAlchemy, Argon2, settings y adaptador de auditoría. |
| `POST /api/v1/auth/login` | Email y contraseña. | Estado `authenticated` y emisión de cookie de autenticación. | Servicio de login, repositorio SQLAlchemy, verificación Argon2, settings, JWT y auditoría. |
| `GET /api/v1/auth/me` | Cookie de autenticación. | Identidad mínima con IDs públicos de usuario y organización. | Servicio de identidad, verificador JWT y repositorio SQLAlchemy. |
| `GET /api/v1/auth/csrf` | Cookie de autenticación. | Token CSRF ligado a `sub` y `jti` de la sesión. | Verificación JWT, mecanismo CSRF y settings; sin consulta a DB. |
| `POST /api/v1/auth/logout` | Cookie y cabecera `X-CSRF-Token`. | Borrado de cookie y estado `logged_out`. | Verificación JWT/CSRF y configuración de cookie; sin consulta a DB ni revocación observada. |
| `POST /api/v1/auth/token` | Formulario `username` y `password`. | Ruta publicada; operación rechazada con `403` por defecto (`False`). Mediante opt-in devuelve JWT bearer, sin cookie. | Adaptador de credenciales, servicio de login, repositorio SQLAlchemy, Argon2, settings, JWT y auditoría. |

El recorrido de credenciales separa adaptador HTTP, servicio de aplicación y repositorio SQLAlchemy. Argon2 interviene en el hash y la comprobación de contraseñas; los settings gobiernan configuración de tokens, cookies y activación del adaptador; el servicio JWT emite/verifica credenciales; los adaptadores de auditoría producen logging saneado, **no una auditoría durable**.

El JWT utiliza `HS256` y exige los claims `sub`, `type`, `jti`, `iat` y `exp`. El claim `org` se emite cuando está disponible y es exigido por `/me`, no por el verificador JWT global. La cookie tiene por defecto `Secure`, `HttpOnly` y `SameSite=lax`; configurar `SameSite=none` exige `Secure`. Estos son hechos estáticos del estado inventariado, no resultados de una prueba de navegador ni una modificación de los valores descritos en etapas históricas anteriores.

Hay configuración CORS explícita, pero CORS regula interacciones del navegador entre orígenes: **no autentica ni autoriza**. El rate limiting se aplica por ruta/IP con estado en memoria del proceso, sin garantía de coordinación entre procesos. IAM/users no está publicado en esta superficie y no se certifica RBAC de extremo a extremo. El adaptador password de `/auth/token` tampoco convierte la aplicación en un servidor OAuth completo.

#### Evidencia de pruebas existente y comprobaciones del entorno

El inventario identifica tests HTTP de login, me, register y token con overrides de servicios. Permiten aislar el contrato HTTP, pero sustituyen parte del recorrido real. También existen tests de integración de repositorios con PostgreSQL: **su existencia no equivale a un flujo HTTP E2E** que conecte router, servicio, hashing, JWT y persistencia reales. Ninguno de esos tests se ha ejecutado en el punto 1.

Comprobaciones de entorno **confirmadas por QA**, distintas de la lectura estática:

- El daemon Docker es accesible y se observaron cuatro contenedores en estado running. No se registran sus nombres.
- PostgreSQL respondió `1` a `SELECT 1` dentro de una transacción `READ ONLY`, terminada con rollback. No se escribieron datos ni se incluyen credenciales.
- Esa comprobación acredita conectividad SQL básica, no el vínculo entre la base de datos consultada y un contenedor específico, ni la validez del esquema o del flujo de autenticación.

Las fixtures de DB disponen de un fallback que selecciona `DATABASE_URL` del `.env.example` de la raíz, coincidente con el destino local loopback identificado. No se reproduce la URL. El usuario ha autorizado la destrucción de datos seed/demo **locales para pruebas futuras**; esa autorización no implica que se hayan destruido datos en este punto ni permite actuar sobre otros entornos. Antes de ejecutar fixtures o pruebas destructivas deberá verificarse de nuevo el destino efectivo, incluido cualquier override del entorno: loopback por sí solo no demuestra que la base sea desechable.

#### Modelo de amenazas

**Activos que se deben proteger:** credenciales en tránsito y hashes persistidos; JWT y clave de firma; tokens CSRF; identidad de usuario y tenant; datos de cada organización; disponibilidad de la API y PostgreSQL; integridad y confidencialidad de la evidencia de auditoría.

**Actores considerados:** cliente anónimo; usuario autenticado adversario que intenta salir de su ámbito; poseedor de un token robado; sitio externo que intenta CSRF; operador que introduce una configuración incorrecta, especialmente al seleccionar la base de pruebas. No se presupone que todo usuario autenticado sea confiable.

**Fronteras de confianza:**

```text
Cliente → API → resolución de identidad en DB → autorización → logging
Entorno/configuración de pruebas → selección de DB de pruebas
```

En la primera frontera, el backend debe validar entradas y credenciales sin confiar en el cliente. Una firma JWT válida no basta para autorizar recursos: se debe contrastar la identidad y el tenant, y aplicar permisos donde corresponda. En logging, la necesidad de trazabilidad no justifica registrar secretos. En la segunda frontera, la configuración debe impedir que una prueba con limpieza de datos alcance una base no autorizada.

#### Matriz de controles y verificaciones pendientes

`NO VERIFICADO` significa que se ha identificado un control o comportamiento por lectura, pero **no se ha demostrado su eficacia funcional en esta auditoría**. No significa automáticamente que el control falle. Las comprobaciones de entorno confirmadas anteriormente no cambian este estado.

| Control | Amenaza | Evidencia disponible | Tests pendientes | Resultado | Deuda |
| --- | --- | --- | --- | --- | --- |
| Validación y Argon2 en registro/login | Contraseñas inválidas, enumeración de cuentas y fallos de hash. | Schemas, servicios y hasher inventariados; tests HTTP con overrides. | Contrastar espacios en contraseñas entre registro/login, entradas límite, errores uniformes y fallos de hash. | NO VERIFICADO | Confirmar coherencia y tratamiento seguro de errores. |
| Firma y claims JWT | Token manipulado, expirado o de tipo incorrecto. | `HS256`; claims obligatorios `sub`, `type`, `jti`, `iat`, `exp`; `org` emitido cuando está disponible y exigido por `/me`, no por el verificador global. | Firma incorrecta, expiración, claims obligatorios ausentes/inválidos y exigencia de `org` en `/me`; errores de verificación JWT, separados de los errores del DTO de formulario de `/token`. | NO VERIFICADO | Confirmar rechazo controlado sin filtrar detalles internos. |
| Endpoint `/auth/token` | Entradas de formulario inválidas o emisión bearer sin opt-in. | Ruta publicada; flag `False` por defecto rechaza la operación con `403`; DTO de formulario y respuesta bearer sin cookie mediante opt-in. | Errores de validación del DTO de formulario, rechazo `403` con el flag desactivado y respuesta bearer sin cookie con opt-in. | NO VERIFICADO | Confirmar contrato del adaptador y tratamiento controlado de errores del formulario. |
| Atributos y borrado de cookie | Exposición de sesión o persistencia involuntaria de cookie. | Defaults `Secure`, `HttpOnly`, `lax`; `none` requiere `Secure`; borrado en logout. | Atributos emitidos y borrados, combinaciones de settings y comportamiento de navegador. | NO VERIFICADO | Validación por entorno y correspondencia de atributos. |
| Resolución de `sub` + `org` y estado | Suplantación de tenant o uso de identidad/organización no activa. | Consulta de identidad; comprobación de organización `ACTIVE` no observada en login/me. | Cruce de tenant, usuario inactivo, organización inactiva y cambios de estado tras emitir token. | NO VERIFICADO | Determinar política efectiva; no certificar RBAC E2E. |
| CSRF ligado a `sub`/`jti` | Petición forzada, token CSRF de otra sesión o replay. | Emisión CSRF y exigencia de cabecera en logout; sin DB. | Ausencia, manipulación, otra sesión y reutilización de CSRF. | NO VERIFICADO | Precisar límites de vinculación y replay. |
| Logout mediante borrado local | Reutilización de un JWT previamente copiado. | Borrado de cookie; no revocación observada ni consulta DB. | Reutilizar token tras logout y contrastar comportamiento hasta expiración. | NO VERIFICADO | Distinguir cierre local de invalidación server-side. |
| Rate limiting por ruta/IP | Fuerza bruta y agotamiento de recursos. | Contador en memoria de proceso. | Umbral, ventana, separación de rutas/IP, concurrencia y comportamiento con varios procesos/proxy. | NO VERIFICADO | No hay límite distribuido; revisar confianza en IP. |
| Logging de auditoría saneado | Fuga de secretos o pérdida de trazabilidad. | Adaptadores de logging; no almacenamiento durable. | Captura de logs de éxito/error, excepciones y ausencia de contraseñas, hashes, JWT, claves y CSRF. | NO VERIFICADO | Confirmar saneamiento y definir persistencia/retención. |
| Selección y aislamiento de DB de tests | Destrucción de datos fuera del destino autorizado. | Fixtures con fallback local; conectividad básica confirmada por QA. | Verificar destino efectivo antes de pruebas y comprobar aislamiento/limpieza de fixtures. | NO VERIFICADO | Autorización limitada a seed/demo local; falta validar ejecución segura de fixtures. |

#### Decisiones, límites y cierre del punto 1

Se mantiene el histórico íntegro y se añade esta fotografía inicial para separar implementación descrita, evidencia disponible y demostración pendiente. No se asignan severidades definitivas: la comprobación de organización `ACTIVE` no observada en login/me, la coherencia de contraseñas con espacios, la validación interna del token y sus errores, los fallos de hash, la seguridad de logs y los límites de replay/logout son **preguntas de verificación**, no hallazgos explotables demostrados. Los puntos 2 y 3 deberán contrastarlas.

El impacto sobre el backend es de trazabilidad y preparación de la auditoría: delimita qué componentes y fronteras se deberán probar, sin alterar rutas, contratos, persistencia ni configuración. No se ha implementado código ni ejecutado tests en este punto.

**Arquitectura y QA aprueban el inventario y el modelo de amenazas del punto 1; la eficacia de los controles de seguridad permanece pendiente.** No se han abordado los puntos 2–8 ni se han abierto PRs en este punto. No se crea baseline.

### 2. Auditoría de arquitectura y contratos

La revisión estática cubrió los seis endpoints inventariados en el punto 1: registro, login, identidad actual, CSRF, logout y token técnico. Se revisaron sus contratos, dependencias y límites de seguridad; esta subsección diferencia los hallazgos iniciales de las decisiones aplicadas después, sin repetir el histórico funcional de la fase.

| Hallazgo | Área | Severidad | Riesgo | Decisión | Acción | Estado |
| --- | --- | --- | --- | --- | --- | --- |
| AUTH-001: la organización inactiva no se comprobaba de forma uniforme en la resolución de sesión. | Login, `/auth/me`, CSRF, logout y token técnico. | Alta | Una credencial válida podía asociarse a una organización ya inactiva. | Exigir organización activa en todos los recorridos autenticados. | Se incorporó la comprobación común de organización activa. | Corregido y re-auditado. |
| AUTH-002: el modelo actual presupone una organización efectiva por usuario. | IAM y selección de tenant. | Alta arquitectónica/futura | El modelo no puede seleccionar de forma segura una organización entre varias memberships. | Mantener el modelo actual sin exponer una selección inexistente. | Declarar multi-membership como prerrequisito de una fase IAM futura. | Prerrequisito bloqueante de una futura fase IAM, explícitamente autorizado fuera de alcance. |
| Contraseñas con espacios: el tratamiento no era simétrico entre los flujos revisados. | Registro y login. | Media | Alterar silenciosamente una contraseña puede cambiar la credencial efectiva. | Tratar la contraseña como valor literal. | Se eliminó cualquier normalización semántica de contraseña. | Corregido y re-auditado. |
| Hash de contraseña malformado podía provocar error interno. | Login y token técnico. | Media | Un hash persistido corrupto podía derivar en un `500` y revelar un fallo operativo. | Convertir el fallo de verificación en credenciales no válidas. | El adaptador de `pwdlib` devuelve fallo seguro. | Corregido y re-auditado. |
| `/auth/token` es una superficie técnica publicada sin consumidor bearer operativo. | Contrato OAuth2 técnico. | Baja | Activarlo sin caso de uso aprobado ampliaría la superficie de credenciales. | Mantenerlo deshabilitado por defecto. | Se conserva el opt-in explícito. | Control conforme. |
| CSRF no es un sustituto de autenticación ni de autorización. | Mutaciones con cookie. | Baja | Futuros endpoints podrían asumir una protección que no cubre permisos ni tenant. | Mantenerlo como guardarraíl obligatorio para futuras mutaciones con cookie. | Se documenta su integración obligatoria en nuevas rutas. | Control conforme; guardarraíl futuro. |
| Rate limit local al proceso. | Protección ante abuso. | Media | No coordina límites entre procesos o instancias. | Mantener la defensa local del MVP sin presentar capacidad distribuida. | Registrar la evolución a almacenamiento compartido como deuda. | Deuda futura. |
| Auditoría basada en logging no durable. | Trazabilidad. | Media | No proporciona retención ni consulta operativa equivalente a `AuditEvent`. | Mantener logging saneado y planificar persistencia transversal. | Deuda explícita de auditoría durable. | Deuda futura. |
| Logout originalmente era solo borrado de cookie. | Gestión de sesión. | Alta | Un JWT copiado podía reutilizarse hasta expirar. | Revocar el `jti` de forma persistente antes de borrar la cookie. | Se añadió revocación persistente y comprobación en rutas de sesión. | Corregido y re-auditado. |
| Validación de `iss` y `aud`. | JWT. | Baja | La aceptación de tokens requiere una política explícita de emisor y audiencia al integrarse con otros emisores o consumidores. | Mantener la validación actual limitada al emisor local y tratar `aud` como extensión de contrato. | No se habilitan consumidores bearer adicionales. | Deuda de evolución, sin hallazgo pendiente en el flujo actual. |

Los controles que no figuran como deuda se consideraron conformes tras la revisión estática y la re-auditoría: contratos mínimos, cookie `HttpOnly`, separación del token técnico y validación de sesión contra persistencia. La aprobación no certifica RBAC ni IAM multi-membership, que quedan fuera de este alcance.

### 3. Evidencia de QA en entorno real

QA ejecutó las comprobaciones iniciales contra el entorno local real con Docker y PostgreSQL como destino confirmado. No se documentan secretos, direcciones ni datos reales. Antes de corregir, la suite completa se ejecutó desde `backend` con `uv run pytest`: **`458 passed`**, sin pruebas deseleccionadas. Las comprobaciones E2E se realizaron después sobre el mismo destino real y antes de aplicar las correcciones descritas en el punto 5.

| Evidencia inicial ejecutada | Resultado observado antes de la corrección | Interpretación |
| --- | --- | --- |
| Login y `/auth/me` con organización inactiva. | El flujo devolvió `200`. | Confirmó AUTH-001. |
| Login con hash de contraseña malformado en persistencia. | El flujo devolvió `500`. | Confirmó que el fallo no se degradaba a error de credenciales. |
| Logout y reutilización de la credencial previa en `/auth/me`. | `/auth/me` devolvió `200`. | Confirmó que el logout era local y no revocaba el JWT. |
| Contraseñas con espacios. | Se observó asimetría entre flujos. | Confirmó la necesidad de semántica literal. |
| Rate limiting. | El límite se aplicó por proceso. | Confirmó el comportamiento local, no distribuido. |

El comando completo de suite y su resultado quedan indicados arriba. Las comprobaciones HTTP usaron el recorrido real con PostgreSQL y sin overrides de dependencias; sus resultados anteriores se resumen aquí para no duplicar el registro de QA ni introducir rutas, credenciales o destinos reales. Esta evidencia es distinta de la re-ejecución final: los resultados de esta tabla **no** describen el estado corregido.

> [!WARNING]
> Que Docker y PostgreSQL locales estuvieran disponibles confirma el destino de pruebas autorizado de aquella ejecución; no convierte ese entorno en evidencia de despliegue ni valida el ciclo de vida de Alembic o Docker.

### 4. Consolidación de decisiones

Las decisiones aprobadas tras la evidencia inicial son las siguientes:

- La organización debe estar activa en login, `/auth/me`, CSRF, logout y el token técnico cuando este se habilite explícitamente.
- La revocación de sesión se basa en `jti` persistente, con migración de esquema.
- Las contraseñas son literales: no se recortan ni normalizan sus espacios.
- Un hash malformado se trata como credencial no válida (`401`), sin propagar un error interno.
- `/auth/token` permanece deshabilitado por defecto; no existe consumidor bearer operativo que justifique ampliar esa exposición.
- El rate limiting sin Redis queda como deuda topológica: es local al proceso y no debe describirse como distribuido.
- El soporte de múltiples memberships por usuario es prerrequisito explícito antes de diseñar selección de organización activa; no se fuerza esa capacidad en el modelo actual.

El alcance se amplió únicamente para incorporar la migración **0014** de revocación. Esta ampliación no incluye reconciliación de historial ni verificación del ciclo de vida de Alembic o Docker. Esa revisión se difiere a una fase separada, `BACK-DB-MIGRATIONS-AUDIT-001`, en la rama `backend/audit/BACK-DB-MIGRATIONS-AUDIT-001`, que **no se ha iniciado**.

### 5. Correcciones y re-auditoría

La corrección incorporó revocación persistente mediante el esquema `sch_iam` y la tabla `tbl_revoked_access_token`. Su registro contiene únicamente `id`, `jti` único, expiración y marca temporal de revocación; no guarda tokens JWT en bruto. La migración Alembic 0014 crea esta estructura y el registro de modelos la incorpora al conjunto ORM.

La lógica se separó entre `AuthSessionService` y un repositorio SQLAlchemy: en logout se revoca primero el `jti` y después se ordena borrar la cookie. Las rutas `/auth/me`, CSRF y logout rechazan con `401` una sesión revocada. La resolución de sesión aplica además la condición de organización activa. El evento de logout se registra de forma saneada como `LOGOUT`, con solo IDs públicos y hash de `jti`; no incluye token en bruto, contraseña ni otro secreto.

La verificación de contraseña conserva el valor literal y encapsula los errores de `pwdlib` para devolver fallo seguro. Por ello, un hash malformado deja de producir error interno y se traduce en credenciales no válidas.

La re-auditoría ejecutó escenarios E2E HTTP con PostgreSQL real, sin overrides de dependencias: organización inactiva, hash malformado, revocación tras logout, semántica literal de contraseña, token técnico deshabilitado y sus contratos asociados. Arquitectura y QA aprueban ambas re-auditorías: la de correcciones funcionales y la de calidad final.

| Comprobación final | Resultado exacto |
| --- | --- |
| Calidad | `make backend-quality`: Ruff, comprobación de formato y mypy strict correctos |
| Unitarios | `396 passed, 72 deselected` |
| Base de datos | `50 passed, 418 deselected` |
| Seguridad | `22 passed, 446 deselected` |
| Suite completa | `468 passed` (sin tests deseleccionados) |

#### Deuda que permanece abierta

- La verificación del ciclo de vida de Alembic y Docker se mantiene diferida a `BACK-DB-MIGRATIONS-AUDIT-001`; no queda resuelta por la migración 0014.
- El rate limiting distribuido con almacenamiento compartido sigue pendiente.
- Una auditoría durable basada en `AuditEvent`, con retención y consulta operativa, sigue pendiente.
- El modelo de múltiples memberships y la selección explícita de organización activa pertenecen a una futura fase IAM.

Estas deudas no deben interpretarse como corregidas ni cubiertas por la aprobación de esta re-auditoría.

### Consolidación documental histórica

Esta sección conserva la trazabilidad exclusiva de la documentación original `BACK-AUTH-OAUTH2-001` a `BACK-AUTH-OAUTH2-012`. Los documentos individuales se han consolidado y eliminado porque su contenido funcional ya estaba absorbido por este documento o era redundante; no se eliminan hechos validados ni se da por resuelta la deuda OAuth/IAM pendiente.

| ID original | Propósito | Tema o decisión relevante conservada |
| --- | --- | --- |
| `BACK-AUTH-OAUTH2-001` | Roadmap, diseño e informe de implementación de partida. | Definió la secuencia modular (configuración, IDs públicos, hash, token, cookie, registro, sesión, CSRF, CORS y QA), routers finos, servicios testeables y repositorios SQLAlchemy. También dejó explícita la frontera entre OAuth2 Password Bearer técnico y la sesión browser. |
| `BACK-AUTH-OAUTH2-002` | Auth Core. | Introdujo configuración tipada, Argon2id mediante `pwdlib`, JWT mínimo, value object de cookie y public IDs; no exponía rutas HTTP. |
| `BACK-AUTH-OAUTH2-003` | Registro inicial. | Separó el alta de organización/administrador del login, añadió `public_id` único y secuencias internas de rango alto, y documentó que el readiness de PostgreSQL requería una comprobación real posterior. |
| `BACK-AUTH-OAUTH2-004` | Login browser. | Estableció cookie `HttpOnly`, request estricta y errores genéricos; el JWT pasó a transportar `sub` y `org` públicos, sin roles ni IDs internos. |
| `BACK-AUTH-OAUTH2-005` | Identidad actual. | Consolidó la resolución de identidad mediante `sub + org` contra PostgreSQL, sin aceptar un tenant enviado por el cliente. |
| `BACK-AUTH-OAUTH2-006` | Logout inicial. | Nació como borrado idempotente de cookie, sin revocación server-side; esa limitación fue detectada y corregida en la auditoría posterior con revocación persistente de `jti`. |
| `BACK-AUTH-OAUTH2-007` | CSRF. | Añadió token firmado ligado a `sub` y `access_jti`, aplicado primero a logout mediante dependencia explícita, no middleware global. |
| `BACK-AUTH-OAUTH2-008` | Token técnico. | Añadió `/auth/token` con formulario OAuth2 y reutilización de `LoginService`, sin cookie y separada del flujo browser. |
| `BACK-AUTH-OAUTH2-009` | CORS. | Centralizó `CORSMiddleware`, origins y headers explícitos, y separó `CorsSettings` de los secretos JWT para que el arranque de la app no los necesitase solo por CORS. |
| `BACK-AUTH-OAUTH2-010` | Hardening de regresión. | Cubrió los cuatro origins locales, rechazo de wildcard, configuración de expiración y aislamiento de parámetros form ajenos al login; no cambió contratos HTTP. |
| `BACK-AUTH-OAUTH2-011` | Rate limiting. | Incorporó límites in-memory antes de los servicios de login/registro y corrigió la concurrencia con `threading.Lock`; su naturaleza no distribuida se mantiene como deuda. |
| `BACK-AUTH-OAUTH2-012` | Validación y cierre de fase. | Recopiló el flujo completo, sus garantías iniciales y las recomendaciones hacia auditoría durable, contexto de tenant, RBAC, integración cliente y limitación distribuida. |

#### Decisiones iniciales y evolución relevante

- La planificación inicial de `001` fijó cookie `HttpOnly`, `Argon2id`, public IDs, ausencia de tokens en el login browser, CORS sin wildcard y CSRF para mutaciones autenticadas. Estas decisiones siguen siendo el hilo conductor histórico de la fase.
- Algunos contratos y supuestos de `001` eran diseño previo, no estado final: se propusieron respuestas más ricas para login, `/auth/me` y logout, y el diseño inicial no incorporaba `org` al JWT. La implementación consolidada adoptó contratos mínimos y el claim `org` para la resolución de sesión; la auditoría describe además el comportamiento posterior revalidado.
- La evolución fue: **diseño y planificación → Auth Core → registro → sesión browser e identidad → logout y CSRF → bearer técnico y CORS → hardening de regresión → rate limiting → validación de fase → auditoría, correcciones y re-auditoría**.
- Los resultados de QA de las tareas originales se preservan como cronología histórica: el Auth Core registró `291 passed, 56 deselected`; el registro cerró con `313 passed, 56 deselected` y `34 passed, 335 deselected` en base de datos; y la validación de fase `012` registró `381 passed, 63 deselected` y `41 passed, 403 deselected`. La evidencia más reciente y aplicable al estado auditado es la re-auditoría ya recogida arriba (`468 passed` en la suite completa), sin que ello cierre la deuda listada en este documento.
- La documentación inicial consideraba pendientes la auditoría persistente, refresh/revocación server-side, rate limiting distribuido, trusted proxies, `CurrentUser`/tenant context, RBAC, MFA y la integración cliente. La auditoría posterior corrigió específicamente la revocación de `jti`, el control de organización activa, la semántica literal de contraseña y el fallo seguro ante hashes malformados. Permanecen abiertas las deudas expresamente enumeradas en la re-auditoría, incluidas auditoría durable, rate limiting distribuido y multi-membership/selección de organización.

### 6. Consolidación documental

Tras la revisión, los documentos individuales `BACK-AUTH-OAUTH2-001` a `BACK-AUTH-OAUTH2-012` han quedado absorbidos en este documento de fase completa. La documentación OAuth2 individual se ha retirado y OAuth conserva el documento de fase completa como referencia consolidada. La trazabilidad se mantiene de forma concisa en la sección **Consolidación documental histórica**: no se ha perdido ni sustituido el historial, los hechos validados, las decisiones ni las deudas abiertas.

### 7. Baseline de autenticación

Se ha creado una baseline viva e independiente, `BACK-AUTH-OAUTH-BASELINE`, destinada exclusivamente a los controles de autenticación vigentes. No es una baseline hex ni un sustituto del histórico de esta auditoría. Recoge cookies, JWT, revocación, CSRF, validación del endpoint de token, organización activa, semántica de contraseña, auditoría y las pruebas y deudas aplicables. No se declaran rutas ni enlaces de archivo para esa baseline en este documento.

### 8. Validación global y cierre de auditoría

La validación global ejecutada registra los siguientes comandos y resultados exactos:

| Comando o grupo | Resultado |
| --- | --- |
| `make backend-quality` | Ruff correcto; formato `172 files already formatted`; mypy strict `Success: no issues found in 171 source files`. |
| Unitarios | `396 passed, 72 deselected` (deselección intencionada). |
| Base de datos | `50 passed, 418 deselected` (deselección intencionada). |
| Seguridad | `22 passed, 446 deselected` (deselección intencionada). |
| `uv run pytest` desde `backend` | `468 passed in 11.82s`, sin pruebas deseleccionadas. |

La suite completa sin deselecciones es el criterio de cierre; las ejecuciones filtradas sirven para diagnóstico y no la sustituyen. Arquitectura y QA ya han aprobado las dos re-auditorías de las correcciones. La fase está preparada para una PR única, sin afirmar que dicha PR exista o haya sido integrada.

### Dependencia futura: BACK-DB-MIGRATIONS-AUDIT-001

La convención de rama `backend/audit/BACK-DB-MIGRATIONS-AUDIT-001` está aprobada, pero la auditoría no se ha iniciado. El ciclo de vida de Alembic y Docker continúa explícitamente fuera de este alcance: la migración de revocación se verificó de forma estructural y en ejecución contra la base de datos actual, pero no se reclama una reconciliación global de migraciones ni la reproducibilidad de la imagen. Siguen abiertas, sin contradicción con lo ya documentado, la deuda de auditoría durable, el rate limiting distribuido y el soporte de múltiples memberships con selección explícita de organización activa.
