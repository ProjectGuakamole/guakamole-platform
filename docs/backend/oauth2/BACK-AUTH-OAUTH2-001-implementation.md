# BACK-AUTH-OAUTH2-001 — Implementación y validación OAuth2

**Estado:** Pendiente de implementación  
**Ámbito:** `backend/`  
**Carpeta:** `docs/backend/oauth2/`

## 1. Resumen de cambios

Pendiente de implementación.

## 2. Archivos modificados

Pendiente de implementación.

## 3. Endpoints añadidos

Pendiente de implementación.

## 4. Configuración añadida

Pendiente de implementación.

## 5. Tests añadidos

Pendiente de implementación.

## 6. Validaciones ejecutadas

Pendiente de implementación.

## 7. Resultado QA

Pendiente de implementación.

## 8. Riesgos pendientes

Pendiente de implementación.

## 9. Notas para la fase JWT

Pendiente de implementación.

## 10. Estado final

Pendiente de implementación.

---

# BACK-AUTH-OAUTH2-002 — Auth Core

**Estado:** QA aprobado  
**Ámbito:** `backend/`  
**Tipo de cambio:** Núcleo de autenticación sin endpoints ni routers

## 1. Resumen de cambios

Se ha incorporado el núcleo base de autenticación para el backend, dejando preparadas las piezas reutilizables que necesitarán las fases posteriores de login, emisión de sesiones, autorización y protección de rutas.

El alcance de esta tarea se limita a componentes de dominio/infraestructura de autenticación. No se han implementado endpoints HTTP, routers, flujos de login/register, CORS ni protección CSRF.

## 2. Componentes añadidos

```mermaid
flowchart TD
    Config[Auth config tipada]
    Hasher[Password hasher Argon2]
    Tokens[JWT issuer/verifier]
    Cookies[Cookie settings value object]
    PublicIds[Public IDs helper]

    Config --> Hasher
    Config --> Tokens
    Config --> Cookies
    Tokens --> Claims[sub, type, jti, iat, exp]
    PublicIds --> UserId[usr_*]
    PublicIds --> OrgId[org_*]
```

- Configuración de autenticación tipada.
- Hashing y verificación de contraseñas con `pwdlib[argon2]`.
- Emisor/verificador JWT mínimo para tokens de acceso.
- Value object para settings de cookies.
- Helper para identificadores públicos con prefijos `usr_` y `org_`.
- Tests unitarios para el comportamiento del Auth Core.

## 3. Archivos modificados

- `.env.example`
- `backend/pyproject.toml`
- `backend/uv.lock`
- `backend/app/domain/auth/__init__.py`
- `backend/app/domain/auth/config.py`
- `backend/app/domain/auth/cookies.py`
- `backend/app/domain/auth/password_hasher.py`
- `backend/app/domain/auth/public_ids.py`
- `backend/app/domain/auth/tokens.py`
- `backend/tests/unit/test_auth_core.py`

## 4. Endpoints añadidos

No se han añadido endpoints ni routers en esta tarea.

## 5. Ejemplos de contrato interno

### Claims JWT esperados

Ejemplo orientativo de payload esperado para un access token, sin incluir secretos ni token real:

```json
{
  "sub": "usr_01HZXAMPLEUSERID0000000000",
  "type": "access",
  "jti": "01HZXAMPLETOKENID0000000000",
  "iat": 1760000000,
  "exp": 1760000900
}
```

### Cookie settings

Ejemplo de configuración serializable del value object de cookies:

```json
{
  "httponly": true,
  "secure": true,
  "samesite": "lax",
  "path": "/"
}
```

### Public IDs

Ejemplos de formato esperado:

```text
usr_01HZXAMPLEUSERID0000000000
org_01HZXAMPLEORGID00000000000
```

## 6. Secuencia de emisión y verificación JWT

```mermaid
sequenceDiagram
    participant ServicioAuth as Servicio Auth futuro
    participant Issuer as JWT Issuer
    participant Verifier as JWT Verifier
    participant Recurso as Recurso protegido futuro

    ServicioAuth->>Issuer: Solicita access token para sub=usr_*
    Issuer-->>ServicioAuth: Token con sub, type, jti, iat, exp
    Recurso->>Verifier: Verifica token recibido
    Verifier-->>Recurso: Claims validados o error
```

La secuencia muestra el contrato técnico del core, no endpoints implementados en esta tarea.

## 7. Tests añadidos

Se han añadido tests unitarios en:

- `backend/tests/unit/test_auth_core.py`

Los tests cubren el comportamiento base del hashing de contraseñas, tokens, configuración, cookies e identificadores públicos según el alcance indicado por la implementación.

## 8. Validaciones ejecutadas

- `make backend-quality` ✅
- `make backend-test-unit` ✅ (`291 passed, 56 deselected`)

## 9. Resultado QA

QA aprobado según las validaciones indicadas.

## 10. Riesgos pendientes

- Todavía no existen endpoints de autenticación, login, register ni refresh.
- La integración con RBAC, tenant context y auditoría queda pendiente para tareas posteriores.
- Las cookies están modeladas como configuración/value object, pero no se ha documentado uso en respuestas HTTP porque no forma parte de esta task.
- Debe revisarse la política definitiva de rotación de secretos, expiración y revocación cuando se implementen sesiones reales.

## 11. Impacto backend

Este cambio establece las bases internas de autenticación del backend. Reduce acoplamiento futuro al separar configuración, hashing, emisión/verificación de tokens, cookies e identificadores públicos antes de exponer flujos HTTP. También prepara el terreno para aplicar seguridad server-side sin colocar lógica crítica en frontend.

---

# BACK-AUTH-OAUTH2-003 — Registro inicial de organización

**Estado:** QA aprobado  
**Ámbito:** `backend/`  
**Endpoint:** `POST /api/v1/organizations/register`

## 1. Resumen de cambios

Se ha incorporado el registro inicial de organización y usuario administrador mediante un endpoint HTTP específico. El flujo crea la organización y el usuario inicial, pero no realiza login ni entrega token de acceso.

El objetivo es habilitar el alta inicial desde backend manteniendo una frontera clara entre registro, autenticación y sesiones.

## 2. Contrato HTTP

```http
POST /api/v1/organizations/register
Content-Type: application/json
```

Request esperado:

```json
{
  "organization_name": "ACME SOC",
  "admin_email": "admin@acme.example",
  "admin_password": "ChangeMe123!",
  "admin_display_name": "Admin ACME"
}
```

Response esperado:

```json
{
  "organization": {
    "public_id": "org_...",
    "name": "ACME SOC"
  },
  "user": {
    "public_id": "usr_...",
    "email": "admin@acme.example",
    "display_name": "Admin ACME"
  }
}
```

## 3. Decisiones de seguridad

- No se devuelve token en el registro.
- No se crea login ni cookie de sesión en esta task.
- No se exponen IDs internos de base de datos.
- Se usan public IDs `org_...` y `usr_...`.
- La contraseña se hashea mediante Auth Core.
- `jwt_secret_key` sigue siendo obligatorio y sin fallback.
- Los errores por duplicados son genéricos para reducir enumeración.

## 4. Arquitectura modular

La implementación se estructura en piezas separadas:

- `schemas`: contrato de entrada/salida y validación.
- `router`: exposición de `POST /api/v1/organizations/register`.
- `service`: caso de uso de registro, testable sin FastAPI.
- `repository`: encapsulación de SQLAlchemy.
- `exceptions`: errores propios del flujo traducibles a HTTP.

Esta división mantiene el endpoint fino, reduce acoplamiento y facilita pruebas unitarias de la lógica de registro.

## 5. Migración

- `public_id` único y no nulo para organización y usuario.
- Secuencias de base de datos para IDs internos con rango alto reservado `1000000000`.
- Se evita el uso de `MAX(id)+1` para no introducir condiciones de carrera ni lógica frágil de asignación de identificadores.

Nota de validación: la base de datos local del entorno quedó contaminada con una revisión antigua `0014_add_iam_registration_id_sequences`. La validación de migración debe repetirse en una base de datos limpia o en CI.

## 6. Validaciones ejecutadas

- `make backend-quality` ✅
- `make backend-test-unit` ✅ (`313 passed, 56 deselected`)
- `make backend-test-db` ✅ tras levantar PostgreSQL (`34 passed`), según ejecución previa del implementer.
- QA final ✅

## 7. Riesgos pendientes

- Repetir validación de migración en base de datos limpia por contaminación local de Alembic.
- Rate limiting pendiente fuera del alcance de esta task.
- El registro no implementa login, cookie ni emisión de tokens.

## 8. Impacto backend

El backend gana el primer flujo de alta de organización y usuario administrador dentro del módulo OAuth2/Auth. El diseño mantiene la separación entre registro y autenticación, reutiliza Auth Core para hashing y preserva una superficie de respuesta segura mediante public IDs.
