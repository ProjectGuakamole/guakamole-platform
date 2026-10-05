# DOC-BACK-ARCH-HEX-001-T01 — ADR arquitectura backend hexagonal pragmática

**Estado:** Propuesto para fase documental / pendiente de implantación en `BACK-ARCH-HEX-001`.

**Fecha:** 2026-10-05.

## Contexto

Project Guakamole es una plataforma B2B, multi-tenant y security-first orientada al entrenamiento práctico en ciberseguridad. El backend previsto para el MVP es un monolito modular FastAPI que debe crecer de forma controlada sin perder aislamiento entre organizaciones, trazabilidad ni capacidad de auditoría.

Las decisiones arquitectónicas existentes establecen que:

- PostgreSQL será el **Operational Source of Truth** para usuarios, organizaciones, roles, asignaciones, intentos, sesiones de laboratorio, Case Reports, evaluaciones y eventos de auditoría.
- GitHub será el **Content Source of Truth** para escenarios, Markdown, manifiestos, assets y configuración no sensible de laboratorios.
- La arquitectura general separa **Control Plane** y **Lab Plane** para diferenciar la gestión del producto de la ejecución de laboratorios temporales, aislados y desechables.
- El backend deberá cubrir áreas críticas como IAM, RBAC, `TenantContext`, Labs, Scenarios, SOC y Audit.

El crecimiento de estas áreas requiere una estructura backend suficientemente clara para que el equipo pueda implementar funcionalidades sin mezclar responsabilidades de seguridad, negocio, persistencia e integración externa.

## Problema

Si el backend evoluciona mediante routers FastAPI que acceden directamente a SQLAlchemy, deciden autorización, aplican lógica de negocio, generan auditoría y llaman a proveedores externos, aparecerán varios riesgos:

- endpoints difíciles de revisar y testear;
- autorización repartida en condiciones sueltas;
- duplicación de reglas de negocio;
- acoplamiento directo entre FastAPI, PostgreSQL, Docker, Guacamole, GitHub u otros proveedores;
- dificultad para introducir tests unitarios sin infraestructura real;
- auditoría incompleta o inconsistente.

Desde el punto de vista de seguridad, el riesgo principal es acabar con controles dispersos e inconsistentes que faciliten:

- **IDOR** y **Broken Access Control** por validar mal la relación usuario-organización-recurso;
- **SQL injection** si se introducen patrones de consulta inseguros o SQL manual no controlado;
- exposición accidental de `password_hash`, secretos, flags, respuestas correctas o campos internos;
- filtrado incorrecto por tenant;
- errores internos o stacktraces devueltos al cliente;
- falta de eventos auditables en acciones críticas.

## Decisión

Se decide adoptar para el backend de Guakamole el enfoque:

> **FastAPI modular monolith with pragmatic hexagonal architecture**

Esto significa mantener un monolito modular FastAPI durante el MVP, organizado con una arquitectura hexagonal pragmática, orientada a separar responsabilidades donde aporte seguridad, testabilidad o reducción de acoplamiento.

La arquitectura será **pragmática**, no pura ni académica. No se crearán puertos, interfaces o capas adicionales de forma automática para cada operación. Se aplicarán especialmente donde existan reglas críticas, riesgo de acoplamiento, dependencia externa o necesidad clara de testing aislado.

El criterio **security-first** queda fijado como principio de diseño. Las decisiones de estructura deben facilitar controles consistentes de autorización, aislamiento multi-tenant, validación server-side, no exposición de datos sensibles y auditoría.

Esta decisión es documental. La implantación real se abordará en la fase futura `BACK-ARCH-HEX-001`.

## Reglas arquitectónicas decididas

- Los **routers** serán adaptadores de entrada HTTP. Deben recibir la request, validar formato básico, resolver dependencias y delegar en casos de uso.
- Los **services** representarán casos de uso u orquestación de aplicación. No deben depender de detalles HTTP.
- Las **policies** concentrarán reglas de autorización, RBAC, tenant rules y decisiones de acceso.
- Los **repositories** encapsularán persistencia y consultas a PostgreSQL mediante patrones seguros.
- Los **adapters** encapsularán integraciones con sistemas externos como Docker, VMware, Guacamole, GitHub, Redis/RQ u observabilidad cuando aplique.
- Los **schemas Pydantic** controlarán entrada y salida de API.
- Los modelos SQLAlchemy no se devolverán directamente al cliente.
- No se confiará en un `organization_id` recibido desde el frontend sin validarlo contra identidad, membresía y permisos efectivos.
- Las acciones críticas deberán ser auditables, especialmente autenticación, cambios de roles, asignaciones, inicio/cierre de escenarios, Case Reports y operaciones de laboratorios.

## Alternativas consideradas

### Mantener arquitectura por capas simple sin puertos/adapters

**Ventaja:** menor fricción inicial y estructura más familiar para un equipo junior.

**Motivo de descarte:** no ofrece una frontera suficientemente clara para proveedores externos, policies, tenant isolation y testing aislado. Podría servir para CRUD sencillo, pero Guakamole combina IAM, Labs, Scenarios, SOC, Audit y fuentes de verdad distintas.

### Arquitectura hexagonal pura/estricta

**Ventaja:** máxima separación teórica entre dominio, aplicación e infraestructura.

**Motivo de descarte:** puede introducir demasiadas interfaces, DTOs y capas para el estado actual del MVP. El coste cognitivo y de mantenimiento sería alto para el equipo y podría ralentizar funcionalidades críticas.

### Microservicios desde el MVP

**Ventaja:** límites de despliegue y escalado independientes desde el inicio.

**Motivo de descarte:** añade complejidad operativa, observabilidad distribuida, versionado entre servicios y más superficie de fallo. Para el MVP es más seguro y sostenible mantener un monolito modular bien delimitado.

### Routers CRUD directos con SQLAlchemy

**Ventaja:** velocidad aparente para crear endpoints simples.

**Motivo de descarte:** concentra demasiada responsabilidad en el endpoint y aumenta el riesgo de authorization bypass, filtrado multi-tenant incompleto, exposición de modelos internos y tests pobres.

## Consecuencias positivas

- Seguridad más consistente al centralizar autorización, tenant rules y auditoría.
- Mejor testing mediante services, policies y repositories testeables de forma aislada.
- Menor acoplamiento entre FastAPI, PostgreSQL y proveedores externos.
- Sostenibilidad del monolito modular sin necesidad de microservicios prematuros.
- Mejor trazabilidad de decisiones críticas y eventos auditables.
- Preparación para providers futuros o alternativos como Docker, VMware, Guacamole y GitHub.

## Consecuencias negativas y costes

- Requiere más disciplina en diseño y code review.
- Exige documentación y estándares claros para evitar interpretaciones distintas.
- Puede derivar en sobreingeniería si se crean abstracciones sin valor real.
- Tiene curva de aprendizaje para un equipo junior.
- Necesita QA fuerte para confirmar que la estructura se aplica y no solo se documenta.

## Riesgos y mitigaciones

- **Abstracciones prematuras:** aplicar puertos solo cuando reduzcan riesgo, faciliten tests o desacoplen una dependencia real.
- **Documentación no aplicada:** incluir checklist de arquitectura y seguridad en PRs backend.
- **Falsa sensación de seguridad:** exigir tests security-first en la fase de implantación, especialmente para RBAC, tenant isolation y datos sensibles.
- **Refactor grande:** implantar de forma incremental, empezando por un piloto IAM controlado.

## Impacto en seguridad

La decisión busca reducir riesgos de:

- **IDOR / Broken Access Control:** mediante `TenantContext`, policies y validación explícita de acceso a recursos.
- **SQL injection:** mediante repositories que usen SQLAlchemy y consultas parametrizadas, evitando SQL manual inseguro.
- **Fallo de tenant isolation:** filtrando por organización validada, no por valores enviados sin verificar desde el cliente.
- **Exposición de datos sensibles:** evitando devolver `password_hash`, secretos, flags, respuestas correctas o campos internos.
- **Errores no controlados:** separando errores internos de respuestas seguras para cliente.
- **Falta de auditoría:** obligando a registrar acciones críticas de producto y seguridad.

## Impacto en testing futuro

La implantación futura deberá facilitar:

- unit tests de services con fake repositories;
- unit tests de policies;
- tests de tenant isolation y cross-organization access denied;
- tests de repositories/adapters con alcance controlado;
- tests API para validar contrato HTTP y errores;
- tests de no exposición de datos sensibles en responses.

## Impacto en documentación y PRs

Las futuras features backend deberán justificar si siguen este estándar o si existe una excepción razonada. Los PRs que afecten a IAM, RBAC, multi-tenancy, Labs, Scenarios, SOC, Audit, secretos o integración externa deberán incluir revisión de seguridad explícita.

## Relación con documentos existentes

Este ADR se apoya en:

- `docs/backend/hexagonal/architecture.md`.
- `docs/1-architecture/domain_model.md`.
- `docs/1-architecture/system_architecture.md`.

## Relación con tareas futuras

- **T02:** estructura de módulos backend.
- **T03:** reglas de seguridad y multi-tenancy.
- **T04:** estrategia de testing.
- **T05:** piloto IAM.
- **T06:** roadmap de implantación `BACK-ARCH-HEX-001`.

## Decisiones explícitas congeladas por este ADR

- El backend del MVP será un monolito modular, no un conjunto de microservicios.
- La arquitectura será hexagonal pragmática, no hexagonal pura.
- Security-first será criterio de diseño y revisión.
- IAM será el piloto de implantación futura.
- El caso piloto futuro será listar usuarios de una organización validando RBAC y `TenantContext`.

## Criterios de aceptación del ADR

- El ADR no afirma que la arquitectura ya esté implementada.
- La decisión principal queda expresada como monolito modular FastAPI con arquitectura hexagonal pragmática.
- El enfoque security-first queda explícito y vinculado a riesgos concretos.
- Incluye alternativas consideradas con ventaja y motivo de descarte.
- Define reglas arquitectónicas mínimas para guiar la implantación futura.
- Relaciona la decisión con testing, documentación, PRs y tareas futuras.
- No contiene secretos, flags, respuestas correctas ni outputs de comandos.
