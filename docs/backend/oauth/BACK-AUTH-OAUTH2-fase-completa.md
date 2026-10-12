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
> En esta iteración quedan desarrollados los puntos 1, 2, 3, 4 y 5. Los puntos 6-11 permanecen como índice de trabajo para completar el documento en ejecuciones posteriores.

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
login_routers.py
   │
   ├── recibe POST /login
   ├── llama a LoginService
   ├── traduce errores a HTTP 401
   └── configura Set-Cookie

login_schemas.py
   │
   ├── LoginRequest
   ├── LoginResponse
   └── LoginTokenData

login_services.py
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
auth/me_routers.py        → router HTTP y lectura de cookie
auth/me_schemas.py        → schema público de respuesta
auth/me_services.py       → caso de uso de identidad actual
auth/me_repositories.py   → consulta a base de datos
auth/dependencies.py      → settings de autenticación
auth/tokens.py            → verificación del JWT de acceso
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
logout_schemas.py
   └── define la respuesta pública mínima

logout_routers.py
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
