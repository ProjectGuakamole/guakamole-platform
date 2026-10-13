# BACK-ARCH-HEX-BASELINE-001 — Historial de fase

## Alcance de esta fase

Este documento histórico recoge de forma incremental la fase `BACK-ARCH-HEX-BASELINE-001`. En este primer punto se fija la dirección arquitectónica de referencia para el backend. No certifica que la arquitectura esté implantada de forma completa ni sustituye las auditorías, decisiones de adopción o validaciones que se realizarán en los puntos posteriores.

El alcance actual es exclusivamente fundacional y documental. Los puntos 2 a 8 se incorporarán a este mismo documento cuando corresponda.

## 1. Fundamentos: arquitectura hexagonal progresiva

### Dirección arquitectónica y baseline objetivo

La arquitectura hexagonal se adopta como **dirección arquitectónica** y baseline objetivo para el monolito modular basado en FastAPI. Su finalidad es mantener separadas las responsabilidades de transporte, casos de uso, reglas de negocio, persistencia e integraciones, de modo que el backend pueda evolucionar sin convertir cada endpoint en un punto de acoplamiento.

Esta definición no certifica que todos los módulos actuales sigan ya este modelo ni que existan puertos, adapters o límites perfectos en toda la aplicación. La adopción será gradual, priorizando los flujos con mayor impacto funcional, de seguridad o de integración.

La dirección de dependencias esperada es:

```text
router / API → service o caso de uso → policy + repository o puerto
repository → ORM / base de datos
adapter → proveedor externo
```

Esta representación no implica que un adapter sea un paso lineal y obligatorio después de un repository. Un caso de uso puede necesitar un repository para recuperar estado y, de forma independiente, un adapter para interactuar con un proveedor externo. Por ejemplo, iniciar una sesión de laboratorio puede consultar y actualizar datos mediante un repository y solicitar el aprovisionamiento a través de una integración externa; ambas colaboraciones responden a responsabilidades distintas.

### Responsabilidades objetivo

| Componente | Responsabilidad objetivo | No debe asumir como responsabilidad principal |
| --- | --- | --- |
| Router / API | Traducir HTTP a entradas del caso de uso, aplicar dependencias de transporte, devolver respuestas HTTP y delegar la autenticación conforme al mecanismo definido. | Reglas de negocio complejas, autorización de dominio dispersa o acceso directo indiscriminado al ORM. |
| Service / caso de uso | Orquestar una operación de negocio concreta, aplicar el flujo y coordinar policies, repositories y puertos necesarios. | Detalles de HTTP, serialización de respuestas o particularidades de un proveedor externo. |
| Policy | Expresar reglas de autorización, alcance, transiciones o decisiones de negocio reutilizables. | Ser una capa decorativa sin regla verificable o depender de datos confiados al cliente. |
| Repository | Encapsular el acceso y las consultas de persistencia del agregado o recurso que corresponda, incluido el scope necesario. | Decidir permisos de negocio a partir de entradas no validadas o implementar protocolos de proveedores externos. |
| Adapter | Traducir una necesidad del núcleo a la API, SDK o protocolo de un proveedor externo, como OAuth, un motor de laboratorios o un servicio de mensajería. | Contener el caso de uso completo o convertirse en un repositorio genérico de lógica de negocio. |

El núcleo formado por reglas, policies y casos de uso debe poder razonar sobre el dominio sin depender de FastAPI ni de HTTP. Esto no significa que toda carpeta bajo `app/domains/` sea automáticamente ajena a FastAPI: la ubicación física no garantiza el aislamiento. Cada componente debe evaluarse por sus dependencias reales y por su responsabilidad.

### Progresividad y proporcionalidad

La arquitectura se aplicará de forma progresiva. No se introducirán interfaces, puertos, factories o adapters por moda ni para duplicar una abstracción que no aporta una variación real.

Una separación adicional estará justificada, entre otros casos, cuando exista:

- una integración que pueda sustituirse o deba aislarse de su SDK o protocolo;
- una necesidad concreta de probar un caso de uso sin infraestructura externa;
- una variación real entre proveedores, implementaciones o políticas;
- una frontera de seguridad, disponibilidad o coste operativo que convenga controlar explícitamente.

Por el contrario, una operación simple y local no necesita acumular capas artificiales. El objetivo es conseguir límites claros y comprobables, no maximizar el número de clases o interfaces.

### Seguridad y aislamiento multiempresa

El contexto de tenant debe derivarse de la identidad autenticada y de una membership validada. El `organization_id` recibido desde el cliente puede identificar un recurso solicitado, pero jamás autoriza por sí mismo el acceso a dicho recurso.

Las policies deben ejecutarse antes de las operaciones protegidas y las consultas de persistencia deben mantener un scope de tenant defensivo cuando aplique. Esta doble protección reduce el riesgo de que una comprobación omitida en un flujo exponga datos de otra organización.

Los modelos Pydantic forman parte del límite de seguridad: deben aceptar únicamente los campos permitidos para cada operación, evitar mass assignment y no exponer atributos sensibles en las respuestas. Los errores deben estar controlados y no permitir enumerar recursos, memberships u organizaciones ajenas mediante diferencias de respuesta. La auditoría debe registrar acciones relevantes con el contexto necesario, sin incluir secretos, credenciales, tokens ni datos sensibles innecesarios.

### Testabilidad como objetivo de la fase

La testabilidad es un objetivo explícito de esta baseline, no un resultado que se declare ya implantado globalmente. Los puntos posteriores deberán comprobar, según el ámbito que se audite, la cobertura de:

- pruebas unitarias de policies y casos de uso;
- pruebas de integración de persistencia e integraciones relevantes;
- pruebas de API para contratos, validación y errores controlados;
- pruebas de RBAC y de acceso cruzado entre tenants;
- checks arquitectónicos orientados a detectar dependencias o responsabilidades indebidas.

### Integraciones y evolución controlada

OAuth, el aprovisionamiento de laboratorios y la persistencia son ámbitos de evolución controlada. Cuando su variabilidad, testabilidad o dependencia de proveedor lo justifique, podrán definirse puertos y adapters para proteger los casos de uso de detalles tecnológicos. Esta baseline no afirma la existencia actual de adapters ni de una implementación concreta para dichas integraciones.

### Controles objetivo

| Control | Objetivo | Estado |
| --- | --- | --- |
| Separación router, caso de uso y persistencia | Evitar que el transporte HTTP concentre reglas de negocio y acceso a datos. | Pendiente de auditoría en puntos posteriores |
| Núcleo independiente de FastAPI/HTTP | Mantener rules, policies y casos de uso libres de dependencias de transporte cuando su responsabilidad lo permita. | Pendiente de auditoría en puntos posteriores |
| TenantContext validado | Derivar el tenant de identidad autenticada y membership válida. | Pendiente de auditoría en puntos posteriores |
| Scope defensivo de tenant | Aplicar filtros y comprobaciones de tenant en operaciones y consultas sensibles. | Pendiente de auditoría en puntos posteriores |
| Protección de esquemas | Prevenir mass assignment y exposición de campos sensibles mediante modelos de entrada y salida explícitos. | Pendiente de auditoría en puntos posteriores |
| Errores y auditoría seguros | Evitar enumeración cross-tenant y registrar acciones sin secretos. | Pendiente de auditoría en puntos posteriores |
| Puertos y adapters proporcionales | Introducir abstracciones solo ante sustitución, testabilidad o variación reales. | Pendiente de auditoría en puntos posteriores |
| Estrategia de pruebas | Validar unit, integración, API, RBAC/cross-tenant y restricciones arquitectónicas de forma progresiva. | Pendiente de auditoría en puntos posteriores |

### Beneficios, compromisos y validación posterior

La dirección propuesta busca mejorar la legibilidad de los flujos, la protección del aislamiento multiempresa, la capacidad de prueba y la sustitución controlada de dependencias externas. A cambio, exige disciplina para no desplazar lógica de forma superficial entre carpetas ni crear abstracciones prematuras que aumenten el coste de mantenimiento.

Los puntos posteriores validarán el grado de alineamiento de los módulos que se revisen, identificarán dependencias y riesgos concretos, y definirán las acciones de adopción que procedan. Hasta entonces, esta sección establece el criterio de diseño objetivo y no afirma resultados de código, configuración, pruebas o auditorías.

## 2. Auditoría arquitectónica

### Hechos auditados

La auditoría inicial revisó la organización y las dependencias de `backend/app`, la suite de tests, las migraciones de Alembic, la configuración de `pyproject` y la automatización local. No se encontró `Makefile`, por lo que no existía ese punto de entrada para estandarizar los checks del repositorio.

Los hallazgos describen el estado inicial revisado y sirvieron para priorizar correcciones. No deben interpretarse como una afirmación de que permanecieran presentes después de las actuaciones y reauditorías documentadas en este historial.

| Hallazgo | Área | Severidad | Riesgo | Decisión | Acción | Estado |
| --- | --- | --- | --- | --- | --- | --- |
| Routers con dependencias directas de SQLAlchemy, repositories y factories. | Transporte y composición | Alta | Acoplamiento de HTTP con persistencia y dificultad para sustituir o probar colaboraciones. | Separar composición e infraestructura del transporte. | Mover factories fuera de routers y reforzar las fronteras mediante tests. | Corregido y reauditorizado. |
| `RegistrationService` acoplado a ORM/SQLAlchemy. | Caso de uso y persistencia | Alta | El flujo de registro dependía de detalles de persistencia y filtraba responsabilidades de infraestructura. | Mantener el caso de uso independiente de excepciones ORM. | Traducir conflictos de persistencia en el repositorio. | Corregido y reauditorizado. |
| Imports entre dominios desde dependencias y routers. | Límites modulares | Media | Dependencias transversales implícitas y mayor riesgo de cambios en cascada. | Definir fronteras comprobables globalmente. | Añadir controles AST para imports y paquetes mínimos. | Corregido y reauditorizado. |
| Bearer token expuesto por defecto. | Autenticación | Alta | Ampliación innecesaria de la superficie de autenticación. | Exigir activación explícita cuando se necesite. | Deshabilitar bearer por defecto. | Corregido y reauditorizado. |
| Auditoría runtime basada en NoOp. | Auditoría | Media | Pérdida silenciosa de trazabilidad operativa. | Incorporar una alternativa segura y no bloqueante mientras no haya persistencia. | Centralizar logging estructurado saneado. | Corregido y reauditorizado. |
| `TenantContext` de IAM era un piloto, no un contexto efectivo de autorización. | Multiempresa e IAM | Alta | Falsa sensación de aislamiento y autorización insuficiente. | No publicar capacidades de identidad no implementadas realmente. | Retirar la ruta IAM pública piloto. | Corregido y reauditorizado. |
| Schemas genéricos con capacidad de aceptar o exponer campos inadecuados. | DTOs y validación | Alta | Mass assignment y exposición accidental de atributos. | Usar contratos explícitos y restrictivos. | Endurecer DTOs publicados. | Corregido y reauditorizado. |
| Cobertura arquitectónica parcial. | Calidad | Media | Regresiones en las fronteras al modificar módulos no cubiertos. | Extender los checks al árbol global. | Añadir pruebas AST globales. | Corregido y reauditorizado. |
| Cookies con configuración insegura por defecto. | Sesión y transporte | Alta | Riesgo de exposición de cookies en contextos no TLS o configuraciones ambiguas. | Adoptar valores seguros con excepción local explícita. | Configurar cookie segura por defecto y validar combinaciones SameSite. | Corregido y reauditorizado. |

### Riesgo identificado

La combinación de límites arquitectónicos débiles, contratos de entrada amplios y defaults de autenticación o cookies permisivos elevaba el riesgo de regresiones de seguridad y de acoplamiento. La prioridad fue eliminar los defaults inseguros sin transformar esta fase en una reescritura del backend.

## 3. Auditoría de QA, seguridad y calidad

### Hechos verificados en el estado inicial

Los checks disponibles se ejecutaban correctamente y la suite inicial contabilizaba **447 tests**. La comprobación `alembic current/check` no pudo validarse sin una URL de base de datos configurada. También aparecieron alertas por claves JWT de prueba demasiado cortas.

La revisión confirmó los siguientes riesgos: auditoría runtime NoOp, defaults inseguros de JWT y cookies, bearer activo, una ruta IAM publicada que respondía con `501`, DTOs con riesgo de contratos demasiado amplios, ausencia de una prueba del ciclo de migración y acoplamiento cross-domain.

### Controles ya conformes en la revisión

Los siguientes controles ya presentaban una base correcta y no requirieron una sustitución de su enfoque:

- filtrado de tenant en repositories;
- allowlist para paginación y ordenación;
- protección CSRF en logout;
- CORS restringido;
- rate limits;
- registro con prevención de mass assignment y hashing del secreto en servidor;
- una única revisión head de Alembic.

### Limitaciones de la validación

La ausencia de URL de base de datos impidió certificar en esa ejecución el estado operativo de `alembic current/check`. La existencia de un único head reduce el riesgo de divergencia de revisiones, pero no sustituye una prueba integral de aplicar y revertir migraciones sobre una base de datos efímera.

## 4. Consolidación y decisiones

### Decisión de alcance

Se aprobó una ampliación controlada de la fase: no se modificaría el frontend, no se crearían migraciones ni modelos ORM y no se emprendería un refactor masivo. Sí se autorizó hardening de backend mediante defaults seguros y overrides explícitos para desarrollo local, porque estos cambios reducían exposición sin ampliar indebidamente el alcance.

### Decisiones adoptadas

- El uso de bearer queda deshabilitado por defecto y requiere opt-in explícito.
- Las cookies son `secure` por defecto; el desarrollo local debe habilitar de forma explícita el override que corresponda.
- Las claves JWT deben tener al menos 32 bytes.
- IAM users no se monta hasta disponer de una identidad real y operativa.
- La auditoría pasa a logging estructurado, no bloqueante y sin persistencia en esta fase.
- La composición se desacopla de los routers y el registro se desacopla de los detalles ORM.
- Se añaden límites y testing arquitectónico global para prevenir regresiones cross-domain.

### Riesgos y compromisos aceptados

Los defaults más estrictos pueden provocar incompatibilidades intencionadas en HTTP local, secretos JWT cortos o clientes que esperasen bearer. El impacto se mitiga mediante overrides explícitos para desarrollo, no relajando los valores por defecto. La ruta piloto de usuarios IAM deja de responder `501` y pasa a no estar publicada, con resultado `404`. La persistencia de `AuditEvent` y el ciclo integral de Alembic se mantienen fuera de alcance y se registran como deuda técnica.

## 5. Correcciones y reauditorías

### Correcciones realizadas

La sesión de base de datos se situó bajo un módulo neutral `app.db` y las factories se extrajeron de los routers. Como resultado, los routers dejaron de importar directamente SQLAlchemy o repositories, preservando su papel de capa de transporte.

El servicio de registro se desacopló de SQLAlchemy: el repositorio es ahora quien traduce los conflictos de persistencia para que el caso de uso trate resultados propios de su responsabilidad. También se retiró IAM users del router público y se endurecieron los schemas expuestos.

La auditoría se centralizó en un mecanismo de logging estructurado, saneado y no bloqueante. Se restringieron los metadatos seguros y, tras una reauditoría, el saneamiento se amplió para cubrir `private_key`, `passphrase` y sus variantes. Esta solución mejora la trazabilidad runtime sin bloquear operaciones por fallos de auditoría, pero no constituye persistencia de eventos de auditoría.

En autenticación se exigió una clave JWT mínima de 32 bytes, se configuraron cookies seguras por defecto, se validó la combinación de `SameSite=None` y cookie segura, y se dejó bearer deshabilitado salvo activación explícita.

### Iteraciones de reauditoría

Fueron necesarias varias rondas de revisión; las aprobaciones finales no ocultan estas iteraciones. Las reauditorías detectaron y llevaron a corregir el saneamiento central de auditoría, los tests de configuración, el registro de auditoría no bloqueante, la cobertura AST global, la protección de secretos `private_key` y `passphrase`, y las pruebas de `IntegrityError` en `flush` y `commit` con rollback.

Ambas auditorías finales quedaron **APROBADAS** tras verificar estas correcciones.

### Trabajo futuro y deuda explícita

La persistencia de `AuditEvent` no se implementó en esta fase. Tampoco se incorporó una prueba completa del ciclo de Alembic contra una base de datos efímera. Ambos elementos siguen siendo necesarios para reforzar trazabilidad y fiabilidad operativa.

## 6. Tests y evidencias de calidad

### Cobertura incorporada

Se añadieron tests AST globales para verificar fronteras arquitectónicas, imports cross-domain, `__init__` mínimos y ausencia de un paquete `app.domain` en singular. Estos controles evitan que la corrección quede limitada a rutas concretas y detectan regresiones estructurales en el árbol auditado.

También se cubrieron la configuración de autenticación, bearer opt-in, auditoría saneada y no bloqueante, mapeo de conflictos de registro y el comportamiento del repositorio ante `IntegrityError` tanto en `flush` como en `commit`, incluyendo rollback.

### Resultado final ejecutado

- `ruff check`: **OK**.
- Comprobación de formato: **OK**.
- `mypy` en modo estricto: **OK**.
- `pytest`: **458 passed**.

### Controles conformes y evidencias generales

| Control | Evidencia general | Estado |
| --- | --- | --- |
| Fronteras de transporte e infraestructura | Tests AST globales verifican que routers no dependan directamente de SQLAlchemy ni repositories. | Conforme. |
| Límites entre dominios | Tests AST sobre imports cross-domain y paquetes `__init__` mínimos. | Conforme. |
| Configuración de autenticación | Tests de longitud JWT, cookie segura, validación SameSite y bearer opt-in. | Conforme. |
| Auditoría runtime segura | Tests de saneamiento de metadatos y de comportamiento no bloqueante. | Conforme. |
| Registro y persistencia | Tests de mapeo de conflictos y de `IntegrityError` en `flush`/`commit` con rollback. | Conforme. |
| Calidad estática y regresión | `ruff`, formato, `mypy` estricto y suite completa de 458 tests. | Conforme. |

### Deuda técnica pendiente

- Implementar persistencia de `AuditEvent` con su correspondiente modelo, controles de acceso y política de retención.
- Añadir un ciclo integral de Alembic que aplique y valide migraciones sobre una base de datos efímera.

## 7. Formalización del estándar vivo

Se creó el estándar vivo de arquitectura backend como referencia normativa para los cambios futuros. Su propósito no es reconstruir el historial de esta fase ni declarar automáticamente la conformidad de todo el código existente, sino establecer reglas verificables para diseñar, revisar y evolucionar el backend de forma consistente.

### Arquitectura y límites de responsabilidad

El estándar adopta una arquitectura hexagonal progresiva y proporcional: los límites se introducen cuando aportan aislamiento de infraestructura, testabilidad, seguridad o capacidad real de sustitución, evitando capas o abstracciones artificiales.

| Componente | Responsabilidad y límite |
| --- | --- |
| Router / API | Traduce HTTP, aplica dependencias de transporte y delega en el caso de uso; no concentra reglas de negocio ni acceso directo indiscriminado al ORM. |
| Service / caso de uso | Orquesta una operación de negocio y coordina policies, repositories y puertos; no conoce detalles de HTTP ni de proveedores externos. |
| Policy | Expresa reglas reutilizables de autorización, alcance, transiciones o decisión de negocio; no confía en datos aportados por el cliente. |
| Repository | Encapsula persistencia y aplica el scope defensivo que corresponda; no decide permisos de negocio ni implementa integraciones externas. |
| Model | Representa el modelo de persistencia o de intercambio propio de su capa; no sustituye contratos Pydantic explícitos ni incorpora lógica de transporte. |
| Adapter | Traduce las necesidades del núcleo a APIs, SDK o protocolos externos; no contiene el caso de uso completo ni actúa como repositorio de lógica de negocio. |

La composición debe ser neutral respecto al transporte: factories, cableado de dependencias y configuración no pertenecen a los routers. Las dependencias cross-domain solo se permiten cuando responden a un contrato o capacidad transversal explícita y necesaria. Quedan prohibidos los imports directos que acoplen routers, casos de uso o infraestructura a detalles internos de otro dominio, así como las dependencias circulares y los atajos que eludan los límites establecidos.

### Seguridad, autenticación y auditoría

El tenant se deriva de la identidad autenticada y de una membership validada; un `organization_id` recibido del cliente nunca autoriza acceso por sí mismo. RBAC y las policies deben evaluarse antes de las operaciones protegidas, y los repositories deben conservar filtros defensivos de tenant cuando proceda.

Los contratos Pydantic de entrada y salida son restrictivos: solo admiten y exponen los campos autorizados para cada operación, para prevenir mass assignment y filtraciones de atributos sensibles. La auditoría debe recoger acciones relevantes con contexto suficiente, sin secretos, credenciales, tokens ni metadatos sensibles innecesarios; el saneamiento es obligatorio antes de emitir cualquier evento o log de auditoría.

La autenticación mantiene JWT con requisitos de configuración segura, cookies seguras por defecto y validación de combinaciones `SameSite`. El uso de bearer queda deshabilitado por defecto y requiere opt-in explícito; no se habilita como mecanismo implícito por compatibilidad.

### Tests y gobernanza

El estándar exige pruebas proporcionales a cada cambio: unitarias para policies y casos de uso, de integración para persistencia e integraciones, de API para contratos y errores controlados, y de seguridad para RBAC y accesos cross-tenant. Los checks arquitectónicos deben prevenir regresiones en dependencias, composición y límites entre dominios.

La gobernanza de auditoría exige distinguir explícitamente entre la obligación normativa, el estado efectivamente validado por evidencias y la deuda técnica pendiente. Ninguna regla se considera implantada solo por estar definida en el estándar, y ninguna validación cierra una deuda sin evidencia concreta de su resolución.

> [!warning] Deuda técnica persistente
> La persistencia de `AuditEvent` y un ciclo integral de Alembic que aplique y valide migraciones sobre una base de datos efímera siguen abiertos. El estándar los identifica como obligaciones pendientes, no como controles ya resueltos.

En este punto no se introdujeron nuevas modificaciones funcionales en el backend. Únicamente se formalizaron como estándar vivo las normas arquitectónicas, de seguridad, pruebas y gobernanza ya validadas durante la fase.

## 8. Cierre de fase: validación global final

La validación global final se ejecutó después de los commits previos de la fase. Su propósito fue confirmar el estado consolidado del backend, sin tomar los subconjuntos de pruebas como sustituto de la suite completa.

### Comandos ejecutados y resultados exactos

| Comando | Resultado |
| --- | --- |
| `make backend-quality` | `ruff` OK; formato: `163 files already formatted`; `mypy` en modo estricto sobre `162 source files`, sin incidencias. |
| `make backend-test-unit` | `394 passed, 64 deselected`. Los `deselected` corresponden al filtro intencional de pruebas `unit/architecture`. |
| `make backend-test-db` | `42 passed, 416 deselected`. Los `deselected` corresponden al filtro intencional de pruebas `db/integration`. |
| Desde `backend`, `uv run pytest` | `458 passed in 7.04s`, sin pruebas `deselected`. |

> [!important] Criterio de cierre
> Los filtros parciales de `backend-test-unit` y `backend-test-db` sirven para validar ámbitos concretos, pero no se utilizan como evidencia de una suite completa. El criterio de cierre fue la ejecución completa desde `backend`, con `458 passed in 7.04s` y sin `deselected`.

### Garantías validadas

- Se mantienen los límites arquitectónicos comprobados mediante los controles incorporados.
- Se valida el hardening de autenticación configurado en la fase.
- La auditoría runtime saneada y no bloqueante conserva su comportamiento previsto.
- El registro mantiene la seguridad ante conflictos de persistencia.
- El piloto de IAM no queda expuesto públicamente.
- Se preservan las garantías de aislamiento de tenant y RBAC cubiertas por la baseline.

### Estado final

La baseline queda aprobada como base para un único PR. Esta afirmación no implica que exista una PR ni que se haya fusionado ningún cambio.

> [!warning] Deuda técnica pendiente
> La persistencia de `AuditEvent` sigue sin implementarse. También sigue pendiente un ciclo integral de Alembic sobre una base de datos efímera. Ambas deudas permanecen abiertas y no se consideran resueltas por esta validación.
