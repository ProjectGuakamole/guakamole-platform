# BACK-ARCH-HEX-BASELINE

## Objetivo

Establecer el estándar vivo de arquitectura backend para las futuras fases de Guakamole. Su ámbito es exclusivamente el backend: define límites, dependencias, seguridad y validación del código servidor. No es un historial de cambios ni sustituye las decisiones funcionales de cada tarea.

La arquitectura hexagonal se aplicará de forma **progresiva**: se introducirá un puerto o un adaptador cuando reduzca un acoplamiento real, facilite pruebas o aísle una integración. No se crearán capas, interfaces o abstracciones por anticipado si un caso de uso simple no las necesita.

## Cambios realizados

### Estándar obligatorio

#### Dirección de dependencias

La dirección normal será:

```text
router/API → service o caso de uso → policy + repository o puerto
repository → ORM/base de datos
adapter → proveedor externo
```

Un adaptador no es una fase lineal obligatoria tras un repositorio: se utiliza para integrar un proveedor externo (por ejemplo, correo, colas o acceso remoto) y no para envolver código interno sin motivo. Un caso de uso puede combinar una policy con un repositorio, un puerto o ambos, según su necesidad.

Ejemplo conceptual:

```python
# El router traduce HTTP y delega.
result = service.create_group(actor, command)

# El servicio aplica el flujo; la policy autoriza; el repositorio persiste.
policy.assert_can_manage_groups(actor)
repository.add(group)
```

#### Responsabilidades y restricciones por capa

| Capa | Responsabilidad | Prohibiciones |
| --- | --- | --- |
| `router` | HTTP, schemas, dependencies y delegación. | Reglas de negocio, SQLAlchemy y acceso directo a repository. |
| `service` / caso de uso | Orquestar el caso de uso y sus invariantes de aplicación. | FastAPI, `HTTPException`, `Request`, `Response`, SQLAlchemy y modelos ORM. |
| `policy` | Decidir autorización y reglas reutilizables de dominio/aplicación. | FastAPI y SQLAlchemy. |
| `repository` | Consultas y persistencia mediante ORM. | FastAPI y lógica de transporte HTTP. |
| `model` | Representar datos ORM y sus relaciones de persistencia. | FastAPI, routers y services. |
| `adapter` | Traducir una integración con un proveedor externo a un puerto o contrato local. | Implementar un caso de uso completo. |
| `api/v1/router` | Agregar routers de versión API. | Reglas de negocio, factories de dominio y lógica de infraestructura. |
| `__init__.py` | Incluir, como máximo, un docstring mínimo de paquete. | Imports, exports y lógica. |

#### Composición y límites entre dominios

Están prohibidos los imports de routers, services o dependencies HTTP de otro dominio. Un router hermano no ofrece factories a otro router. La construcción de dependencias y factories vive en el área de composición/dependencies, que es el único lugar que conecta implementaciones con sus consumidores HTTP.

Se permiten dependencias neutrales de `app.db`, componentes compartidos estables, tipos y modelos ORM estrictamente requeridos por los repositories. Esta excepción no permite que un service dependa de un modelo ORM: los modelos solo cruzan el límite de persistencia cuando un repository los necesita.

#### Multi-tenant y RBAC

El `TenantContext` procede de la identidad autenticada y de su membership válida. Un `organization_id` recibido del cliente nunca autoriza una operación ni determina por sí solo el tenant.

La protección se aplica en dos niveles:

1. La policy comprueba identidad, rol y ámbito antes de realizar la operación.
2. El repository aplica de forma defensiva el filtro por organización en consultas y mutaciones operativas.

Los errores deben estar controlados y evitar la enumeración de recursos de otros tenants: cuando revelar la existencia del recurso aumente el riesgo, la respuesta no debe diferenciarlo indebidamente. Las acciones sensibles deben generar auditoría.

#### Contratos, datos sensibles y observabilidad

Los contratos Pydantic serán explícitos; se aplicará `extra="forbid"` cuando el endpoint no admita campos adicionales. No habrá mass assignment: se copiarán de forma expresa los campos permitidos al comando o entidad.

No se expondrán ni aceptarán por contratos públicos hashes, contraseñas, roles privilegiados, tenant u otros atributos sensibles salvo que el caso de uso los gestione explícitamente y con autorización. La auditoría y el logging estructurado serán saneados y no bloqueantes: no incluirán tokens, contraseñas, secretos ni PII innecesaria.

#### Autenticación

Los JWT usarán HS256 y un secreto de al menos 32 bytes. Las cookies de sesión usarán `Secure` y `HttpOnly`. `SameSite=None` exige `Secure`.

El uso de bearer estará desactivado por defecto. Solo puede activarse de manera explícita en desarrollo/local. Para compatibilidad con HTTP local, las cookies `Secure` no se enviarán por HTTP: el modo local debe usar una configuración de desarrollo explícita y aislada, nunca rebajar silenciosamente la configuración de entornos seguros.

#### Tests y controles arquitectónicos

Los cambios seleccionarán validaciones de forma proporcional al riesgo y al alcance, sin omitir controles de seguridad aplicables. La selección debe cubrir, cuando corresponda:

- unitarios de services y policies;
- integración de repositories y persistencia;
- API de routers y contratos;
- RBAC y accesos cross-tenant;
- límites arquitectónicos mediante AST.

Comandos base (ejecutar desde `backend/`):

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict .
uv run pytest
```

La ruta concreta puede ajustarse a la configuración vigente del repositorio, pero no se sustituirán los controles equivalentes de lint, formato, tipado estricto y pruebas.

#### Flujo de auditoría y gobernanza

El flujo confirmado es el siguiente:

0. Alcance y baseline.
1. Auditoría de `api-architect` y `qa-tester`.
2. Consolidación de hallazgos.
3. `python-implementer` corrige.
4. Validaciones.
5. Reauditorías.
6. `doc-orchestrator` documenta.
7. `api-architect` verifica la documentación.
8. Commit/push.
9. Siguiente task.

Un desacuerdo bloquea el avance hasta resolverse. Los hallazgos `BLOCKER` y `HIGH` deben estar corregidos; los `MEDIUM` se corrigen si su solución está acotada o se documentan de forma explícita; los `LOW` se documentan o corrigen si ello no amplía el alcance.

### Estado validado en esta baseline

En el cierre actual se han validado los controles de calidad y arquitectura definidos para esta baseline, incluyendo separación de capas, límites de dependencias, controles de tenant/RBAC, contratos y cobertura de pruebas aplicable. El resultado puntual registrado es:

```text
458 passed
```

Este resultado describe esta validación concreta; no promete que el estado permanezca estable ante cambios futuros.

### Deuda técnica y trabajo futuro

- Implementar `AuditEvent` persistente, incluyendo modelo, acceso y política de retención.
- Añadir un test integral de Alembic con una base de datos efímera.

Toda excepción futura a este estándar se registrará con: justificación concreta, riesgo aceptado, tests o controles compensatorios, fecha de alta y fecha o condición de revisión. La excepción debe tener propietario y no se convierte en norma por repetición.

## Justificacion tecnica

Separar transporte, casos de uso, autorización y persistencia evita que las decisiones HTTP o del ORM condicionen el núcleo de aplicación. Esto hace más directas las pruebas unitarias y reduce el riesgo de que una consulta sin ámbito de organización o una decisión de permisos quede dispersa en routers.

La aplicación gradual evita el coste de una hexagonal ceremonial: los puertos y adapters se reservan para límites que cambian, se prueban de forma independiente o conectan con infraestructura externa.

## Decisiones tomadas

- La composición de dependencias se centraliza y no se comparte mediante routers hermanos.
- El tenant se deriva del contexto autenticado, no de datos controlados por el cliente.
- Se mantiene defensa en profundidad: policy previa y scope organizativo en repository.
- La seguridad de cookies y bearer distingue explícitamente entre entornos seguros y desarrollo local.

## Tests ejecutados

Resultado informado para el cierre de esta baseline:

```text
458 passed
```

Las futuras tareas deberán ejecutar y registrar los controles proporcionales que les apliquen, incluidos los de seguridad cuando afecten a identidad, autorización, tenant o datos sensibles.

## Riesgos o deuda tecnica

La auditoría persistente y la validación integral de migraciones siguen pendientes, según la sección de deuda técnica. Hasta que existan, deben mantenerse controles compensatorios de logging saneado, revisión y pruebas de seguridad aplicables.

## Relacion con el backend

Este estándar define cómo se estructuran y validan los módulos backend de FastAPI, persistencia ORM, autorización multi-tenant, integraciones externas y sus pruebas. No impone cambios sobre frontend ni sobre contratos fuera de los que publique la API backend.
