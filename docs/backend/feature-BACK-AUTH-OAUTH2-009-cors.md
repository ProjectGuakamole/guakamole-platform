# feature/BACK-AUTH-OAUTH2-009-cors

## Objetivo

Documentar la Task 9 de OAuth2: configuración CORS segura y controlada para permitir el uso del frontend local/dev contra el backend sin abrir la API con comodines inseguros.

## Cambios realizados

- Configurado `CORSMiddleware` en `create_app()` mediante una función dedicada.
- Añadida configuración CORS con origins explícitos para entornos locales de desarrollo.
- Mantenido `allow_credentials=True` por defecto para compatibilidad con sesiones basadas en cookie `HttpOnly`.
- Evitado el uso de wildcard en origins y headers.
- Hecho configurable el header `Authorization` mediante `cors_allow_authorization_header`.
- Separada la configuración CORS en `CorsSettings`, de forma que construir la aplicación y aplicar CORS no requiere `JWT_SECRET_KEY`.

Origins permitidos por defecto:

```text
http://localhost:3000
http://localhost:5173
http://127.0.0.1:3000
http://127.0.0.1:5173
```

Métodos permitidos:

```text
GET
POST
PUT
PATCH
DELETE
OPTIONS
```

Headers permitidos siempre:

```text
Content-Type
X-CSRF-Token
```

Header permitido solo si `cors_allow_authorization_header=True`:

```text
Authorization
```

## Justificacion tecnica

CORS se aplica en el backend porque es el punto responsable de decidir qué origins de navegador pueden interactuar con la API. La configuración se limita a origins explícitos de desarrollo local para permitir la integración con React/Vite sin exponer la API a cualquier origen.

La separación de `CorsSettings` respecto a `AuthSettings` evita que la creación de la aplicación dependa de un secreto JWT cuando solo se necesita configurar middleware CORS. Esto mejora la testabilidad de `create_app()` y reduce acoplamientos innecesarios entre arranque de aplicación y autenticación.

## Decisiones tomadas

- No usar wildcard `*` en origins.
- No usar wildcard en headers.
- Rechazar el origin `*` en settings.
- No combinar `allow_credentials=True` con wildcard.
- Permitir que solo origins explícitos reciban `access-control-allow-origin`.
- Mantener claro que CORS no autoriza por sí mismo: solo habilita el acceso desde navegador/frontend cuando el origin está permitido.
- No modificar autenticación, CSRF ni endpoints existentes en esta task.
- Centralizar la lógica en `backend/app/core/cors.py`:
  - `configure_cors(app, settings)`.
  - `build_allowed_cors_headers(settings)`.
- Mantener compatibilidad haciendo que `AuthSettings` herede de `CorsSettings`.
- Aplicar CORS desde `create_app()` con `configure_cors(app, CorsSettings())`.

## Tests ejecutados

- `make backend-quality` PASS.
- `make backend-test-unit` PASS: `356 passed, 63 deselected`.
- `make backend-test-db` PASS: `41 passed, 378 deselected`.
- QA final PASS.
- Validación adicional QA: `create_app()` funciona sin `JWT_SECRET_KEY`.

## Riesgos o deuda tecnica

- Futuro: parametrizar tests para cubrir los 4 origins por defecto.
- Futuro: añadir test unitario explícito para `create_app()` sin `JWT_SECRET_KEY`.
- Rate limiting sigue pendiente antes de exposición pública.
- CORS no reemplaza CSRF ni autorización backend.
- `/auth/token`, refresh tokens, RBAC/roles y frontend quedan fuera de esta task.

## Relacion con el backend

El cambio afecta al arranque de la aplicación FastAPI y a su política de acceso desde navegadores. Permite integrar el frontend local/dev con endpoints OAuth2 existentes manteniendo una postura restrictiva: origins y headers explícitos, credenciales habilitadas para cookies y sin ampliar permisos de autenticación o autorización.
