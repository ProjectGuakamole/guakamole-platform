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
> En esta iteración quedan desarrollados los puntos 1 y 2. Los puntos 3-11 permanecen como índice de trabajo para completar el documento en ejecuciones posteriores.

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
