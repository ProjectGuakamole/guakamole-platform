# BACK-AUTH-OAUTH-BASELINE

## Objetivo

### Alcance

Este documento es el estándar vivo de seguridad y de contratos para la autenticación actual del backend. Define los controles que deben preservarse al modificar AUTH y los prerrequisitos para ampliar el sistema. Es autocontenido y no describe la arquitectura hexagonal ni el historial de cambios.

El alcance actual comprende sesiones de navegador mediante cookie y JWT, registro, inicio de sesión, consulta de identidad (`me`), emisión/verificación de CSRF y cierre de sesión. Puede existir un endpoint técnico de contraseña que entregue un token, bajo las restricciones indicadas más adelante.

No existe un servidor de autorización OAuth: no se implementan autorización por código, PKCE, clientes, scopes, refresh tokens, introspección ni revocación como protocolo OAuth. El uso bearer está desactivado por defecto y no hay consumidores bearer existentes.

## Cambios realizados

### Estándar obligatorio

#### Credenciales y validación

- Las entradas de credenciales se validan en servidor con modelos Pydantic estrictos y campos adicionales prohibidos. No se permite asignación masiva de atributos.
- La contraseña literal no se recorta ni normaliza antes de verificarla o derivar su hash: cualquier transformación cambiaría el secreto introducido por la persona usuaria.
- Las contraseñas se almacenan mediante Argon2. Una contraseña o hash malformado produce el mismo fallo genérico que una credencial incorrecta; no se revela la causa.
- No se devuelve, registra ni audita una contraseña literal, un hash de contraseña, un JWT completo ni otro secreto de autenticación.

#### Estado de usuario y organización

- Se exige usuario activo y organización activa al iniciar sesión y al usar cualquier sesión actual: `me`, CSRF, cierre de sesión y endpoint técnico de token.
- Los rechazos de autenticación o de estado se expresan con `401` genérico, sin enumerar si falló usuario, contraseña, organización, pertenencia o estado.
- Un identificador de organización recibido desde cliente nunca autoriza ni selecciona por sí mismo el tenant. La identidad autenticada determina el contexto autorizado.
- Actualmente cada usuario pertenece a una única organización. No se añade un selector de organización en cliente como solución provisional; la pertenencia múltiple requiere primero un diseño IAM explícito.

#### JWT y revocación

- El sistema actual admite únicamente firmas `HS256` con una clave de al menos 32 bytes.
- Todo JWT de acceso incluye `sub`, `type`, `jti`, `iat` y `exp`; incluye además organización cuando es necesaria para resolver el tenant. La expiración es obligatoria y el tipo permitido para acceso es `access`.
- El token CSRF firmado tiene propósito y claims propios; no se confunde con un JWT de acceso.
- Se valida firma, tipo, expiración y claims requeridos antes de aceptar la sesión. No se persiste ni registra el JWT sin procesar.
- La revocación es persistente por `jti`. Al cerrar sesión se revoca antes de eliminar la cookie. `me`, CSRF y cierre de sesión rechazan tokens revocados.
- La tabla de revocación debe guardar, como mínimo, un `jti` único, su expiración y la marca temporal de revocación; no guarda el token. La limpieza de revocaciones expiradas es una necesidad operativa pendiente.
- `iss` y `aud` son una dependencia futura si se pasa a una arquitectura con varios servicios o audiencias; no se simulan como si existieran hoy.

#### Cookies y CSRF

- Las cookies de sesión son `Secure`, `HttpOnly`, con `SameSite=Lax` y el `Path` vigente por defecto. `SameSite=None` exige siempre `Secure`.
- HTTP local solo se admite mediante configuración de desarrollo explícita. No se debilitan atributos de cookie de forma implícita para facilitar desarrollo.
- Borrar la cookie en el navegador no sustituye la revocación en servidor.
- El CSRF está ligado a `sub`, `jti` y expiración. Se exige en toda ruta mutante futura autenticada por cookie.
- CSRF no autentica, no autoriza RBAC, no resuelve el tenant y su vinculación no implica que sea de un solo uso. Un fallo CSRF devuelve `403`; un fallo de sesión devuelve `401`.

#### Endpoint técnico de token

- El endpoint de contraseña para token devuelve `403` por defecto y solo se habilita mediante configuración explícita de desarrollo.
- Si se habilita, entrega un bearer en el cuerpo de la respuesta y no crea cookie. Es exclusivamente una utilidad técnica.
- No transforma al backend en un servidor OAuth ni habilita consumidores bearer. Cualquier consumidor bearer exige diseño, controles y decisión explícitos previos.

#### Errores, límites y auditoría

- Los errores no incluyen secretos ni detalles internos. La validación de entrada usa `422`; inicio o comprobación de sesión fallidos usan `401` genérico; CSRF usa `403`; y limitación de tasa usa `429` con `Retry-After`.
- El rate limiting actual es en memoria y por proceso. No presupone Redis. Debe reevaluarse antes de operar con múltiples workers, proxy distribuido o requisitos de límite global; será necesaria una dependencia externa o un diseño equivalente.
- Se registran eventos relevantes de éxito y fallo con datos saneados. El cierre de sesión produce `LOGOUT` con identificadores públicos seguros y, cuando proceda, hash de `jti`, nunca el token.
- El `AuditEvent` durable sigue pendiente. Hasta su implantación, los logs no deben contener secretos ni PII no necesaria.

### Justificacion tecnica

Los contratos anteriores reducen exposición de credenciales, evitan aceptar sesiones ya invalidadas y separan inequívocamente autenticación, autorización, tenant y protección CSRF. La respuesta genérica impide convertir los endpoints AUTH en un oráculo de cuentas, estados o pertenencias.

Mantener la revocación en servidor es imprescindible porque la cookie puede haberse copiado o permanecer en un cliente que no recibió su borrado. Limitar el endpoint técnico y mantener bearer desactivado evita publicar accidentalmente una superficie OAuth incompleta o un contrato de consumo que no está diseñado.

## Decisiones tomadas

### Gobernanza de auditorías AUTH

Las auditorías de AUTH se trabajan en ramas `backend/audit/<ID>`. Deben aportar un modelo de amenazas y una matriz de controles con evidencias y estado de cada hallazgo. El flujo mínimo es: revisión de arquitectura y QA, implementación de correcciones, reauditoría, actualización de esta norma si cambia el contrato y documentación de la evidencia. No se duplican aquí reglas generales de capas, routers, servicios o repositorios.

## Tests ejecutados

### Estado validado baseline

Este estado es una fotografía temporal: la suite completa del baseline validó **468 tests**. No afirma una ejecución nueva al crear este documento.

Las modificaciones AUTH exigen pruebas de seguridad proporcionales al cambio, incluyendo rutas HTTP con PostgreSQL real para los recorridos de estado y revocación; no se sustituyen esos recorridos por overrides de servicios. Se complementan con pruebas unitarias, metadatos de migración y comprobaciones estáticas.

Desde la raíz del repositorio, la secuencia de referencia es:

```bash
make backend-quality
make backend-test-unit
make backend-test-db
make backend-test-security
cd backend && uv run pytest
```

La última orden se ejecuta sin `deselect`. Las ejecuciones filtradas por marcadores son esperables en los grupos anteriores y deben comunicar explícitamente sus tests deseleccionados; no sustituyen la suite completa.

## Riesgos o deuda tecnica

### Deuda y dependencias futuras

- La limpieza programada de revocaciones expiradas debe definirse y operarse sin guardar tokens.
- El rate limiting distribuido es necesario antes de múltiples workers, balanceadores o proxies que hagan insuficiente el estado por proceso.
- El registro durable de `AuditEvent` está pendiente; deben definirse retención, integridad, consulta y protección de datos.
- La pertenencia multi-organización y una selección de contexto requieren evolución IAM previa; no se resuelven con parámetros del navegador.
- La dependencia `BACK-DB-MIGRATIONS-AUDIT-001`, relativa al ciclo de vida Alembic/Docker, no se ha iniciado. Cualquier persistencia nueva de AUTH debe coordinarse con ese ciclo antes de declararse operativa.
- Una futura exposición entre servicios deberá incorporar emisor y audiencia JWT, además de revisar claves, rotación y consumidores.

## Relacion con el backend

AUTH es la frontera que establece la identidad con la que el backend evalúa estado de cuenta, organización, autorización y operaciones mutantes. Por ello, un cambio en sus contratos afecta a todos los endpoints que consumen sesión, al aislamiento de organización, a la persistencia de revocación, a las migraciones y a la observabilidad.

### Procedimiento de excepciones

No existen excepciones silenciosas. Toda excepción temporal a este estándar debe documentar: justificación, riesgo aceptado, controles compensatorios y pruebas, persona propietaria, revisores y condición objetiva de caducidad o retirada. Requiere revisión explícita de arquitectura y QA antes de aplicarse, y revalidación al vencimiento. Una conveniencia local, una prueba manual o una configuración implícita no constituyen una excepción válida.
