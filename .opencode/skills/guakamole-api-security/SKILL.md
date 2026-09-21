---
name: guakamole-api-security
description: Use when designing or reviewing Guakamole FastAPI endpoints, authentication, authorization, RBAC, multi-tenant isolation, validation and audit events.
---

# Guakamole API Security

Usa esta skill para disenar o revisar endpoints, autenticacion, autorizacion, RBAC, aislamiento multi-tenant y auditoria.

Reglas obligatorias:

- Validar siempre inputs en servidor.
- No confiar en datos enviados por el frontend para autorizacion.
- Nunca confiar en `organization_id` enviado por el navegador sin validarlo contra la identidad autenticada.
- Aislar datos entre organizaciones.
- No exponer secretos, flags, respuestas correctas ni logica critica al frontend.
- Toda accion relevante debe poder generar `AuditEvent`.
- Los errores deben ser controlados y no filtrar detalles internos.

Al disenar endpoints, define:

- Ruta y metodo HTTP.
- Schema de request.
- Schema de response.
- Reglas de autenticacion.
- Reglas de autorizacion.
- Validaciones de negocio.
- Errores esperados.
- Eventos de auditoria.
- Tests positivos, negativos y cross-tenant.

Principios del proyecto:

- GitHub es Content Source of Truth.
- PostgreSQL es Operational Source of Truth.
- Control Plane y Lab Plane deben permanecer separados.
