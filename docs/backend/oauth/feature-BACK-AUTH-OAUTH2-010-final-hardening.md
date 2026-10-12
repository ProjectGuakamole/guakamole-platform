# feature/BACK-AUTH-OAUTH2-010-final-hardening

## Objetivo

Completar el hardening final de OAuth2/CORS mediante tests de regresión de seguridad y documentación asociada.

La task no introduce cambios de contrato HTTP ni modifica el comportamiento público esperado de los endpoints. Su objetivo es reforzar garantías ya definidas para CORS y `POST /api/v1/auth/token`, cerrando deudas pequeñas detectadas durante QA.

## Cambios realizados

- Se documenta la cobertura final de regresión de CORS.
- Se documenta la cobertura final de regresión del endpoint `/auth/token`.
- Se deja constancia de que el cambio se limita a tests/regresiones y documentación.
- Se actualiza la documentación global OAuth2 con el cierre de `BACK-AUTH-OAUTH2-010`.

Cobertura CORS documentada:

- `create_app()` funciona sin `JWT_SECRET_KEY` ni `JWT_SECRET`.
- Los 4 origins por defecto quedan cubiertos explícitamente:
  - `http://localhost:3000`
  - `http://localhost:5173`
  - `http://127.0.0.1:3000`
  - `http://127.0.0.1:5173`
- `cors_allowed_origins` parsea correctamente un string separado por comas.
- El wildcard `*` sigue rechazado.

Cobertura `/auth/token` documentada:

- `expires_in` deriva de `ACCESS_TOKEN_EXPIRE_MINUTES` usando un valor distinto de `15` para evitar falsos positivos.
- Un body JSON incorrecto devuelve `422` y no autentica.
- Campos form extra como `organization_id` y `tenant` no llegan a `LoginRequest` ni influyen en autenticación.
- El endpoint sigue sin setear cookie.

## Justificacion tecnica

El cierre de OAuth2/CORS necesitaba asegurar que las decisiones de seguridad tomadas en tareas anteriores no se degradan por cambios futuros.

Las regresiones se centran en puntos sensibles del backend:

- CORS debe permitir únicamente origins explícitos y no depender de secretos JWT para arrancar la aplicación.
- `/auth/token` debe seguir siendo un adaptador OAuth2 Password Bearer para Swagger/desarrollo, sin contaminar la autenticación con parámetros de tenant enviados por cliente.
- La expiración devuelta debe proceder de configuración backend, no de un valor fijo accidental.
- El endpoint bearer no debe introducir cookies ni alterar el flujo principal basado en cookie `HttpOnly`.

## Decisiones tomadas

- No se modifica `frontend/`.
- No se implementa rate limiting en esta task.
- No se implementa auditoría persistente.
- No se implementan refresh tokens ni revocación server-side.
- No se cambian contratos HTTP.
- No se relaja CORS.
- No se introducen secretos reales.
- Se mantiene el hardening como una task de regresión y documentación, no como una ampliación funcional.

## Tests ejecutados

- `make backend-quality` ✅ PASS.
- `make backend-test-unit` ✅ PASS: `370 passed, 63 deselected`.
- `make backend-test-db` ✅ PASS: `41 passed, 392 deselected`.
- QA final ✅ PASS.

Aviso conocido: siguen apareciendo warnings de PyJWT por secretos de test cortos. Se consideran deuda no bloqueante porque afectan a datos de prueba y no introducen secretos reales ni cambian el contrato OAuth2/CORS.

## Riesgos o deuda tecnica

- Rate limiting pendiente antes de exposición pública.
- Auditoría persistente pendiente.
- Refresh tokens y revocación server-side no implementados.
- Warnings PyJWT en tests por secretos de test cortos.

## Relacion con el backend

El cambio refuerza la seguridad del backend en dos superficies relevantes del módulo OAuth2: el arranque de FastAPI con CORS y el endpoint bearer `/auth/token` utilizado por Swagger/desarrollo.

Aunque no añade funcionalidad nueva, aumenta la confianza en que las garantías de seguridad existentes se mantienen: origins explícitos, rechazo de wildcard, ausencia de cookies en `/auth/token`, configuración correcta de expiración y rechazo de entradas JSON/form inesperadas que pudieran intentar influir en el tenant o en la autenticación.
