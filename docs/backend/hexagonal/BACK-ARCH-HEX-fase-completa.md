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

## 2. Pendiente de incorporación

Pendiente de documentar en el punto 2 de la fase.

## 3. Pendiente de incorporación

Pendiente de documentar en el punto 3 de la fase.

## 4. Pendiente de incorporación

Pendiente de documentar en el punto 4 de la fase.

## 5. Pendiente de incorporación

Pendiente de documentar en el punto 5 de la fase.

## 6. Pendiente de incorporación

Pendiente de documentar en el punto 6 de la fase.

## 7. Pendiente de incorporación

Pendiente de documentar en el punto 7 de la fase.

## 8. Pendiente de incorporación

Pendiente de documentar en el punto 8 de la fase.
