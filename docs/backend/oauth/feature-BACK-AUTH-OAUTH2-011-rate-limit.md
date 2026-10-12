# feature/BACK-AUTH-OAUTH2-011-rate-limit

## Objetivo

Documentar la Task 11 OAuth2, centrada en incorporar rate limiting básico in-memory para endpoints públicos sensibles del backend durante la fase MVP/desarrollo.

El objetivo funcional es reducir el riesgo de fuerza bruta o abuso básico en:

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/token`
- `POST /api/v1/organizations/register`

Quedan fuera de la protección de esta tarea:

- `GET /api/v1/auth/me`
- `GET /api/v1/auth/csrf`
- `POST /api/v1/auth/logout`

## Cambios realizados

- Se ha añadido un rate limiter in-memory para uso inicial en MVP/dev.
- Se han definido límites iniciales por IP y ruta:
  - Login: `5` requests cada `60` segundos.
  - Token OAuth2 bearer: `5` requests cada `60` segundos.
  - Registro de organización: `3` requests cada `300` segundos.
- Se ha incorporado la configuración `RATE_LIMIT_ENABLED=false` para desactivar el limiter cuando sea necesario.
- Se ha implementado una respuesta HTTP `429 Too Many Requests` con el cuerpo:

```json
{
  "detail": "Demasiadas solicitudes. Inténtalo más tarde."
}
```

- Se devuelve el header `Retry-After` cuando el tiempo de espera restante es calculable.
- Se ha corregido la seguridad ante concurrencia mediante `threading.Lock` tras una revisión QA inicial.
- Se ha añadido una fixture de tests para limpiar el estado del singleton del rate limiter entre pruebas.

## Justificacion tecnica

La solución es deliberadamente simple porque cubre una necesidad inmediata del MVP: proteger endpoints públicos sensibles antes de exponerlos en entornos de desarrollo compartido o staging inicial.

Se ha optado por in-memory para evitar introducir Redis antes de que sea imprescindible. Esto reduce complejidad operacional en esta fase, aunque deja documentada la limitación de que no es una solución distribuida ni adecuada para múltiples workers o instancias.

El limiter se evalúa antes de llamar a `LoginService` o `RegistrationService`, de forma que las peticiones bloqueadas no ejecutan validación de credenciales, hashing, emisión de tokens ni creación de entidades.

## Decisiones tomadas

- La clave de rate limiting usa `scope + path + request.client.host`.
- No se utilizan email, username, password, token, payload ni `organization_id` para construir la clave.
- No se confía todavía en `X-Forwarded-For`, porque queda pendiente definir una estrategia segura con reverse proxy y proxies de confianza.
- Los errores son genéricos y no indican si el usuario existe.
- La respuesta `429` no expone email, password, token ni `organization_id`.
- `RateLimitSettings` queda separado de la configuración JWT.
- Se crean dependencias explícitas por caso de uso:
  - `require_auth_login_rate_limit`
  - `require_auth_token_rate_limit`
  - `require_registration_rate_limit`
- Se mantiene fuera del alcance la protección de `/auth/me`, `/auth/csrf` y `/auth/logout`.
- La thread-safety se corrige con `threading.Lock` tras detectar el riesgo en QA.

## Tests ejecutados

- `make backend-quality` ✅ PASS.
- `make backend-test-unit` ✅ PASS: `381 passed, 63 deselected`.
- `make backend-test-db` ✅ PASS: `41 passed, 403 deselected`.
- QA inicial ❌ FAIL por thread-safety.
- Corrección aplicada con `threading.Lock` y test concurrente.
- QA final ✅ PASS.

Aviso conocido: los warnings de PyJWT en tests continúan como deuda no bloqueante.

## Riesgos o deuda tecnica

- El rate limiter in-memory no es distribuido.
- No es válido como solución definitiva para múltiples workers, múltiples procesos o varias instancias de backend.
- Futuro: sustituir por Redis para staging/productivo.
- Futuro: definir estrategia de IP real con reverse proxy y trusted proxies.
- La ventana fija simple puede permitir ráfagas en el borde de la ventana.
- No hay rate limiting adaptativo.
- No hay limitación por usuario autenticado o cuenta concreta.
- Los warnings de PyJWT en tests siguen pendientes como deuda no bloqueante.

## Relacion con el backend

El cambio afecta directamente a la superficie pública de autenticación y registro del backend. Refuerza los endpoints OAuth2 y de alta inicial frente a abuso básico, sin modificar contratos funcionales de login, token o registro salvo por la nueva respuesta `429` cuando se supera el límite configurado.

La arquitectura principal se concentra en `backend/app/core/rate_limit.py`, con:

- `RateLimitSettings` independiente de JWT.
- `InMemoryRateLimiter`.
- `RateLimitRule`.
- Dependencias explícitas para login, token y registro.

La integración en routers mantiene los servicios de dominio (`LoginService` y `RegistrationService`) desacoplados de la política HTTP de rate limiting.
