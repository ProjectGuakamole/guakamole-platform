# Objetivo

El Domain Model define **qué elementos existen dentro de Project Guakamole, qué responsabilidad tiene cada uno y cómo se relacionan**.

Todavía no representa las tablas SQL definitivas. Servirá como base para diseñar posteriormente PostgreSQL, SQLAlchemy, Alembic, los endpoints FastAPI y los permisos RBAC.

El modelo se basa en cinco separaciones fundamentales:


- USER ≠ ORGANIZATION
- CONTENIDO ≠ ACTIVIDAD DEL USUARIO
- SCENARIO ≠ SCENARIO ATTEMPT
- SCENARIO ATTEMPT ≠ LAB SESSION
- CASE REPORT ≠ CASE EVALUATION

# Visión global del dominio

```text
                              USER
                                │
                                ▼
                  ORGANIZATION MEMBERSHIP
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
                  ROLES                   GROUPS
                                            │
                                  ┌─────────┴─────────┐
                                  ▼                   ▼
                            GROUP MEMBER        GROUP MANAGER


                ┌─────────────────────────────────────────────────┐
                │               CONTENT                           │
                │                                                 │
                │   ROADMAP                    SCENARIO           │
                │      │                          │               │
                │      ▼                          ▼               │
                │ ROADMAP ITEM            SCENARIO VERSION        │
                │                                 │               │
                │                     ┌───────────┴──────┐        │
                │                     ▼                  ▼        │
                │              ALERT DEFINITION   EVALUATION RULE │
                └─────────────────────────────────────────────────┘

                                │
                                ▼

                       ASSIGNMENT LAYER

                      ┌─────────┴─────────┐
                      ▼                   ▼
              ROADMAP ASSIGNMENT   SCENARIO ASSIGNMENT
                      │                   │
                      ▼                   │
              ROADMAP ENROLLMENT          │
                      │                   │
                      └─────────┬─────────┘
                                ▼
                      SCENARIO ENROLLMENT
                                │
                         ATTEMPT POLICY
                                │
                                ▼
                       SCENARIO ATTEMPT
                                │
                   ┌────────────┼────────────┐
                   ▼            ▼            ▼
              LAB SESSION   ALERT CASE    PROGRESS
                                │
                                ▼
                           CASE REPORT
                                │
                                ▼
                         CASE EVALUATION


      CUALQUIER ACCIÓN RELEVANTE
                  │
                  ▼
              AUDIT EVENT
```

# CLIENTES

## User

`User` representa una persona física que accede a Project Guakamole B2C.

No representa una empresa y tampoco determina directamente el rol de la persona.

```text
User

id
email
password_hash
display_name
status
created_at
last_login_at
```

Una misma cuenta podrá pertenecer a varias organizaciones.

Ejemplo:

```text
ana@email.com

├── ACME
│   └── EMPLOYEE
│
└── CyberCorp
    └── SCENARIO_EDITOR
```

## Organization

`Organization` representa al cliente B2B.

```text
Organization

id
name
slug
status
created_at
```

Ejemplo:

```text
ORG-001 → ACME
ORG-002 → CyberCorp
ORG-003 → IronHack
```

### OrganizationMembership

Representa la relación entre una persona y una organización.

```text
User
   │
   ▼
OrganizationMembership
   │
   ▼
Organization
```

Conceptualmente:

```text
OrganizationMembership

id
user_id
organization_id
status
joined_at
```

#### Roles y MembershipRole

Los roles iniciales serán:

| Rol               | Alcance                          |
| ----------------- | -------------------------------- |
| `PLATFORM_ADMIN`  | Global                           |
| `COMPANY_ADMIN`   | Organización                     |
| `GROUP_MANAGER`   | Organización/grupos determinados |
| `SCENARIO_EDITOR` | Organización/contenido           |
| `EMPLOYEE`        | Organización                     |

Una persona podrá tener varios roles simultáneamente.

```text
OrganizationMembership
        │
        ├── COMPANY_ADMIN
        └── SCENARIO_EDITOR
```

Por tanto necesitaremos conceptualmente:

```text
Role
MembershipRole
```

`PLATFORM_ADMIN` tendrá un tratamiento global y no estará limitado a una única organización.

### Group

Representa un equipo de empleados dentro de una empresa.

```text
ACME

├── SOC L1
├── SOC L2
└── Blue Team Junior
```

Modelo conceptual:

```text
Group

id
organization_id
name
description
status
created_at
```

Un usuario puede pertenecer a más de un grupo.

#### GroupManager

El rol `GROUP_MANAGER` no implica automáticamente poder administrar todos los grupos de una organización.

Necesitamos controlar el ámbito.

```text
Marta
GROUP_MANAGER

├── SOC L1
└── Blue Team Junior

NO:
SOC L2
```

Por tanto existirá conceptualmente:

```text
GroupManager

membership_id
group_id
```

### Invitation

Permitirá que una empresa invite usuarios sin intervención manual del Platform Admin.

```text
Invitation

id
organization_id
email
role
invited_by
token_hash
expires_at
accepted_at
status
```

Flujo:

```text
Company Admin
      │
      ▼
Invite Employee
      │
      ▼
Email / Link
      │
      ▼
Register / Login
      │
      ▼
OrganizationMembership
```

# Roadmap

Representa un itinerario compuesto por escenarios.

Podrán existir dos tipos conceptuales:

```text
PLATFORM ROADMAP
```

Creado por Project Guakamole y disponible para las empresas.

Y:

```text
ORGANIZATION ROADMAP
```

Creado de forma privada por una empresa.

Modelo:

```text
Roadmap

id
owner_organization_id
name
description
status
created_by
created_at
```

Si:

```text
owner_organization_id = NULL
```

es contenido oficial de Project Guakamole.

Si:

```text
owner_organization_id = ACME
```

es un Roadmap privado de ACME.


## RoadmapItem

Relaciona escenarios con un Roadmap.

```text
SOC Analyst Starter

1. Phishing Investigation
2. Suspicious Activity
```

Conceptualmente:

```text
RoadmapItem

id
roadmap_id
scenario_id
position
```

## RoadmapDependency

Permite definir requisitos entre escenarios.

MVP:

```text
Scenario 01
     │
     ▼
Scenario 02
```

Futuro:

```text
                 INTRO
                   │
                   ▼
                PHISHING
                /      \
               ▼        ▼
          WINDOWS      LINUX
               \        /
                ▼      ▼
                INCIDENT
```

Modelo:

```text
RoadmapDependency

roadmap_item_id
requires_item_id
```


## Scenario

`Scenario` representa la identidad lógica de una simulación SOC.

Por ejemplo:

```text
phishing-investigation
```

No representa que Ana lo esté realizando. Eso será un `ScenarioAttempt`.

Modelo conceptual:

```text
Scenario

id
slug
name
owner_organization_id
visibility
status
repository
repository_path
created_by
created_at
```

## Visibilidad de escenarios

Para MVP tendremos dos tipos:

```text
PLATFORM_PUBLIC
```

Escenarios oficiales de Project Guakamole que pueden utilizar las empresas.

Y:

```text
ORGANIZATION_PRIVATE
```

Escenarios creados por una organización y visibles solamente dentro de ella.

Ejemplo:

```text
PROJECT GUAKAMOLE

PUBLIC
├── Phishing Investigation
├── SSH Investigation
└── Windows Incident

ACME PRIVATE
├── ACME VPN Incident
└── ACME SOC Assessment
```

Un marketplace de escenarios queda fuera del MVP.

### ScenarioVersion

Los escenarios deberán ser versionables.

```text
Scenario
   │
   ├── Version 1
   ├── Version 2
   └── Version 3
```

Si Ana comienza `Version 1`, publicar `Version 2` no puede modificar su intento en curso.

Modelo:

```text
ScenarioVersion

id
scenario_id
version
git_commit_sha
manifest_checksum
status
published_at
```

Esto enlaza PostgreSQL con el contenido real almacenado en GitHub.

### Scenario Content

GitHub será el **Content Source of Truth**.

Ejemplo:

```text
scenarios/
│
├── phishing-001/
│   ├── scenario.yaml
│   ├── README.md
│   ├── documentation/
│   ├── playbooks/
│   ├── assets/
│   └── lab/
│
└── ssh-001/
```

En GitHub estarán:

| GitHub                        |
| ----------------------------- |
| Markdown                      |
| documentación                 |
| imágenes                      |
| playbooks                     |
| datasets                      |
| configuración no sensible     |
| assets                        |
| configuración del laboratorio |
| versionado                    |

PostgreSQL almacenará referencias e información operacional.

### EvaluationRule

Las respuestas correctas, criterios de evaluación, flags y secretos **no deberán estar accesibles al alumno en GitHub**.

Para ello tendremos:

```text
EvaluationRule

id
scenario_version_id
alert_key
expected_classification
expected_evidence
score_weight
configuration
```

Ejemplo:

```text
Alert:
PHISH-001

Expected classification:
TRUE_POSITIVE

Expected IOC:
185.x.x.x
```

Estas reglas estarán exclusivamente en backend/PostgreSQL o almacenamiento privado equivalente.

### RoadmapAssignment

Una empresa podrá asignar un Roadmap a:

```text
USER
```

o:

```text
GROUP
```

Modelo conceptual:

```text
RoadmapAssignment

id
organization_id
roadmap_id

user_id      nullable
group_id     nullable

assigned_by
assigned_at
due_at
status
```

Debe existir `user_id` o `group_id`, pero no los dos simultáneamente.

### RoadmapEnrollment

`RoadmapAssignment` representa:

> el Grupo SOC Junior tiene asignado este Roadmap.

`RoadmapEnrollment` representa:

> Ana está realizando ese Roadmap.

```text
RoadmapAssignment
       │
       ├──── Ana → RoadmapEnrollment
       ├── Carlos → RoadmapEnrollment
       └── Miguel → RoadmapEnrollment
```

Modelo:

```text
RoadmapEnrollment

id
organization_id
user_id
roadmap_id
source_assignment_id
status
started_at
completed_at
```

### ScenarioAssignment

Los escenarios también podrán asignarse directamente sin utilizar un Roadmap.

Esto es especialmente importante para assessments y selección.

```text
Company
   │
   ▼
Scenario
   │
   ▼
Candidate / Employee
```

Ejemplo:

```text
Phishing Investigation
        ↓
Ana
Attempts: 1
Mode: ASSESSMENT
```

Podrá asignarse igualmente a un grupo.

### ScenarioEnrollment

Esta entidad unifica el acceso efectivo del usuario a un escenario.

El origen puede ser:

```text
ROADMAP
```

o:

```text
DIRECT ASSIGNMENT
```

Ejemplo:

```text
ScenarioEnrollment

user:
Ana

scenario:
Phishing Investigation

source:
DIRECT_ASSIGNMENT

mode:
ASSESSMENT
```

A partir de aquí aparecerán los intentos individuales.

# Training vs Assessment

El mismo motor deberá poder utilizarse para:

```text
TRAINING
```

y:

```text
ASSESSMENT
```

No construiremos dos sistemas distintos.

### Training

Orientado a:

```text
aprender
repetir
practicar
mejorar
```

### Assessment

Orientado a:

```text
evaluar
limitar intentos
controlar tiempo
mantener evidencia auditable
```

Esto permite utilizar Project Guakamole posteriormente tanto para formación como para procesos de selección.

No construiremos un ATS completo durante el MVP.

## AttemptPolicy

Los intentos no pertenecerán rígidamente al escenario.

El mismo escenario puede tener políticas distintas según la asignación.

Ejemplo formación:

```text
Phishing Investigation

max_attempts = unlimited
score_policy = BEST
mode = TRAINING
```

Ejemplo selección:

```text
Phishing Investigation

max_attempts = 1
score_policy = FIRST
mode = ASSESSMENT
```

Conceptualmente:

```text
AttemptPolicy

max_attempts
score_policy
availability_from
availability_until
mode
```

`max_attempts = NULL` significará ilimitado.

Políticas de resultado iniciales:

```text
BEST
LATEST
FIRST
```

Para MVP no es obligatorio que `AttemptPolicy` sea una tabla independiente. Puede implementarse como configuración dentro de la asignación/enrollment si simplifica el desarrollo.

El concepto, sin embargo, debe existir.

---

# 25. ScenarioAttempt

Representa un intento concreto de un usuario.

```text
Scenario
Phishing Investigation
        │
        ▼
ScenarioEnrollment
        │
        ├── Attempt #1
        ├── Attempt #2
        └── Attempt #3
```

Modelo:

```text
ScenarioAttempt

id
organization_id
scenario_enrollment_id
scenario_version_id
user_id

status

started_at
submitted_at
completed_at

score
result
```

Todos los intentos deberán conservarse.

Nunca se sobrescribirá un intento anterior.

---

# 26. Estados de ScenarioAttempt

Estados iniciales:

```text
CREATED
   │
   ▼
IN_PROGRESS
   │
   ├──── SUBMITTED ───► COMPLETED
   │
   ├──── TIMEOUT
   │
   ├──── ABANDONED
   │
   └──── INVALIDATED
```

`INVALIDATED` se utilizará cuando un intento no deba contabilizarse.

Ejemplo:

```text
Infrastructure Failure
Server Failure
Lab Provisioning Error
Administrative Decision
```

El intento no se borra.

Se conserva para auditoría.

---

# 27. Cuándo consume un intento

No consumiremos un intento simplemente porque el usuario pulse:

```text
START
```

Si ocurre:

```text
REQUESTED
QUEUED
PROVISIONING
FAILED
```

el intento no deberá consumirse.

Lo consideraremos efectivo cuando el laboratorio haya llegado correctamente a:

```text
ACTIVE
```

y el usuario haya comenzado la sesión.

Una vez iniciado realmente:

```text
abandono
timeout
cierre
```

sí contará como intento, salvo invalidación administrativa.

---

# 28. Histórico de resultados

Project Guakamole conservará todos los intentos.

Ejemplo:

```text
Ana
Phishing Investigation

Attempt #1
Score: 43

Attempt #2
Score: 72

Attempt #3
Score: 91
```

Podremos obtener:

```text
FIRST   43
BEST    91
LATEST  91
```

Sin destruir información histórica.

---

# 29. ScenarioAttempt ≠ LabSession

Es una separación fundamental.

```text
ScenarioAttempt
=
actividad pedagógica/evaluativa
```

Mientras:

```text
LabSession
=
infraestructura temporal
```

Ejemplo:

```text
ScenarioAttempt #123
      │
      ├── LabSession #900
      │      FAILED
      │
      └── LabSession #901
             ACTIVE
```

Un error de infraestructura no debe destruir el progreso del usuario.

---

# 30. LabSession

Representa una instancia temporal del laboratorio.

Modelo conceptual:

```text
LabSession

id
organization_id
scenario_attempt_id

provider
provider_reference

status

requested_at
started_at
expires_at
max_expires_at
destroyed_at

extension_count

remote_access_reference
```

Las credenciales temporales no deberán guardarse en texto plano.

---

# 31. Estados de LabSession

```text
REQUESTED
    ↓
QUEUED
    ↓
PROVISIONING
    ↓
READY
    ↓
ACTIVE
    ↓
EXPIRED
    ↓
DESTROYING
    ↓
DESTROYED
```

También:

```text
FAILED
```

La sesión tendrá inicialmente:

```text
Default     60 minutos
Extension   +30 minutos
Maximum     120 minutos
```

La política será configurable.

---

# 32. LabProvider

El dominio no debe depender directamente de Docker.

Conceptualmente:

```text
LabEngine
    │
    ▼
LabProvider
    │
    ├── DockerProvider     MVP
    ├── VMwareProvider     opcional
    └── AWSProvider        futuro
```

`LabProvider` deberá ofrecer operaciones similares a:

```text
create
start
status
extend
destroy
```

El MVP implementará principalmente `DockerProvider`.

---

# 33. AlertDefinition

Representa una alerta diseñada como parte del escenario.

Ejemplo:

```text
Alert ID:
PHISH-1035

Rule:
Suspicious Email From External Domain

Severity:
LOW

Incident Type:
PHISHING
```

Pertenece a una versión concreta del escenario.

```text
ScenarioVersion
      │
      ├── AlertDefinition 01
      └── AlertDefinition 02
```

---

# 34. AlertCase

`AlertDefinition` representa la alerta del escenario.

`AlertCase` representa **la copia operativa de esa alerta para un intento concreto**.

```text
AlertDefinition
PHISH-1035
       │
       ├── Ana → AlertCase A
       ├── Juan → AlertCase B
       └── Laura → AlertCase C
```

Modelo conceptual:

```text
AlertCase

id
organization_id
scenario_attempt_id
alert_definition_id

status

opened_at
closed_at
```

Cada usuario trabaja sobre su propio caso.

---

# 35. Estados de AlertCase

Inicialmente:

```text
AWAITING_ACTION
OPENED
CLOSED
```

Más adelante podrán aparecer:

```text
ESCALATED
IN_REVIEW
```

pero no son necesarios para MVP 0.1.

---

# 36. CaseReport

Representa **la respuesta del analista**, no su evaluación.

Relación inicial:

```text
AlertCase
    │
    ▼
CaseReport
```

Modelo:

```text
CaseReport

id
alert_case_id

classification
severity
activity_time
closure_rationale

submitted_at
```

Clasificación:

```text
TRUE_POSITIVE
FALSE_POSITIVE
```

El Manager autorizado podrá visualizar el contenido completo.

---

# 37. CaseEvaluation

Representa cómo Project Guakamole evalúa un `CaseReport`.

```text
CaseReport
     │
     ▼
CaseEvaluation
```

Modelo conceptual:

```text
CaseEvaluation

id
case_report_id

classification_correct
score
feedback

evaluator_type
evaluated_at
```

Tipos de evaluador previstos:

```text
RULES
MANUAL
AI
```

Durante el MVP:

```text
RULES
```

será el sistema principal.

Esto permite añadir IA posteriormente sin cambiar el modelo fundamental.

---

# 38. IA futura

El diseño queda preparado para:

```text
CaseReport
    │
    ▼
Evaluation Engine
    │
    ├── Rule Engine
    ├── Human Review
    └── AI Evaluator
```

La IA puede posteriormente evaluar aspectos como:

```text
calidad de investigación
claridad del informe
evidencias utilizadas
cronología
argumentación
IOC mencionados
```

Pero no será dependencia del MVP.

---

# 39. Progress

No almacenaremos inicialmente:

```text
progress = 67%
```

como fuente de verdad.

El progreso se derivará de:

```text
RoadmapEnrollment
        │
        ▼
ScenarioEnrollments
        │
        ▼
ScenarioAttempts
```

Ejemplo:

```text
Roadmap: 2 escenarios

Scenario 1 → COMPLETED
Scenario 2 → PENDING

Progress = 50%
```

Si posteriormente el cálculo resulta costoso podremos añadir caches o materializaciones.

---

# 40. Visibilidad del Manager

Dentro de su ámbito autorizado, el Manager podrá consultar:

| Información          |
| -------------------- |
| usuario              |
| Roadmaps             |
| escenarios asignados |
| número de intentos   |
| intento actual       |
| histórico completo   |
| FIRST score          |
| BEST score           |
| LATEST score         |
| tiempo empleado      |
| clasificación TP/FP  |
| severidad            |
| Case Report completo |
| evaluación           |
| progreso             |

Esto es válido tanto para formación como para assessment.

---

# 41. AuditEvent

Toda acción relevante deberá ser auditable.

Modelo conceptual:

```text
AuditEvent

id
timestamp

organization_id
actor_user_id

action

entity_type
entity_id

ip_address
user_agent

metadata
correlation_id
```

Ejemplo:

```text
actor:
ana@acme.com

organization:
ACME

action:
CASE_SUBMITTED

entity:
AlertCase #1035

metadata:
{
  "classification": "TRUE_POSITIVE"
}
```

---

# 42. AuditEvent ≠ Log técnico

Un log puede decir:

```text
POST /api/cases/1035
200
42 ms
```

Un AuditEvent debe decir:

```text
Ana García
cerró el caso 1035
como TRUE_POSITIVE.
```

Los logs técnicos irán principalmente a:

```text
Loki
```

Los AuditEvents permanecerán en:

```text
PostgreSQL
```

y podrán enviarse también al stack de observabilidad.

---

# 43. Source of Truth

Una regla arquitectónica queda formalmente establecida:

> **GitHub = Content Source of Truth**

> **PostgreSQL = Operational Source of Truth**

Separación:

| Información                       | Source of Truth               |
| --------------------------------- | ----------------------------- |
| Markdown                          | GitHub                        |
| Documentación                     | GitHub                        |
| Playbooks                         | GitHub                        |
| Assets                            | GitHub                        |
| Scenario manifest                 | GitHub                        |
| Configuración no sensible del Lab | GitHub                        |
| Versionado de contenido           | GitHub                        |
| Usuarios                          | PostgreSQL                    |
| Organizations                     | PostgreSQL                    |
| Roles                             | PostgreSQL                    |
| Groups                            | PostgreSQL                    |
| Assignments                       | PostgreSQL                    |
| Enrollments                       | PostgreSQL                    |
| Attempts                          | PostgreSQL                    |
| AttemptPolicy                     | PostgreSQL/config operacional |
| LabSession                        | PostgreSQL                    |
| AlertCase                         | PostgreSQL                    |
| CaseReport                        | PostgreSQL                    |
| EvaluationRule sensible           | PostgreSQL/privado            |
| CaseEvaluation                    | PostgreSQL                    |
| AuditEvent                        | PostgreSQL                    |
| Logs técnicos                     | Loki                          |

---

# 44. Scenario Editor híbrido

El futuro Scenario Editor deberá respetar esta separación.

```text
Scenario Editor
      │
      ▼
    FastAPI
      │
      ├──────────────► GitHub
      │                contenido
      │                Markdown
      │                assets
      │                manifest
      │
      └──────────────► PostgreSQL
                       evaluation rules
                       permisos
                       estado
                       metadata operacional
```

Posteriormente:

```text
Git Commit
    │
    ▼
Scenario Sync
    │
    ▼
ScenarioVersion
```

---

# 45. Multi-tenancy

Las tablas operativas más sensibles incluirán explícitamente:

```text
organization_id
```

cuando resulte útil para garantizar aislamiento y facilitar consultas.

Ejemplos:

```text
ScenarioAttempt
LabSession
RoadmapAssignment
ScenarioAssignment
ScenarioEnrollment
AlertCase
AuditEvent
```

Una petición siempre deberá ejecutarse dentro de un:

```text
Tenant Context
```

Ejemplo:

```text
JWT
 │
 ▼
User
 │
 ▼
OrganizationMembership
 │
 ▼
Organization
 │
 ▼
Tenant Context
 │
 ▼
Authorization
 │
 ▼
Query
```

Nunca se confiará en un `organization_id` enviado por el navegador sin validarlo contra la identidad autenticada.

---

# 46. Reglas mínimas de autorización

Ejemplos de tests obligatorios:

```text
Employee ACME
intenta consultar CyberCorp
→ DENIED


Group Manager SOC-L1
intenta gestionar SOC-L2
→ DENIED


Employee
intenta crear usuarios
→ DENIED


Scenario Editor ACME
intenta editar escenario privado CyberCorp
→ DENIED


Company Admin
intenta convertirse en Platform Admin
→ DENIED
```

Estos tests formarán parte de la seguridad del MVP.

---

# 47. PostgreSQL Row Level Security

Para MVP:

```text
MUST
Aislamiento multi-tenant en FastAPI
+
tests automáticos
```

Como defensa adicional futura:

```text
SHOULD
PostgreSQL Row Level Security
```

No se introducirá RLS si pone en riesgo el tiempo disponible para completar el Golden Path.

---

# 48. Modelo consolidado

```text
USER
 │
 ▼
ORGANIZATION MEMBERSHIP
 │
 ├──── MEMBERSHIP ROLE
 │
 ├──── GROUP MEMBER
 │
 └──── GROUP MANAGER
 │
 ▼
ORGANIZATION


ROADMAP
 │
 ├──── ROADMAP ITEM ──────────► SCENARIO
 │                                  │
 ├──── ROADMAP DEPENDENCY           ▼
 │                            SCENARIO VERSION
 │                                  │
 ▼                                  ├── ALERT DEFINITION
ROADMAP ASSIGNMENT                  │
 │                                  └── EVALUATION RULE
 ▼
ROADMAP ENROLLMENT
 │
 ▼
SCENARIO ENROLLMENT ◄──── SCENARIO ASSIGNMENT
 │
 ├── ATTEMPT POLICY
 │
 ▼
SCENARIO ATTEMPT
 │
 ├──────────────────► LAB SESSION
 │
 └──────────────────► ALERT CASE
                           │
                           ▼
                       CASE REPORT
                           │
                           ▼
                     CASE EVALUATION


ALL RELEVANT ACTIONS
        │
        ▼
    AUDIT EVENT
```

---

# 49. Entidades núcleo del MVP

| Área          | Entidades                                                                            |
| ------------- | ------------------------------------------------------------------------------------ |
| Identity      | `User`                                                                               |
| B2B           | `Organization`, `OrganizationMembership`                                             |
| Authorization | `Role`, `MembershipRole`                                                             |
| Teams         | `Group`, `GroupMember`, `GroupManager`                                               |
| Onboarding    | `Invitation`                                                                         |
| Learning      | `Roadmap`, `RoadmapItem`, `RoadmapDependency`                                        |
| Assignment    | `RoadmapAssignment`, `RoadmapEnrollment`, `ScenarioAssignment`, `ScenarioEnrollment` |
| Policy        | `AttemptPolicy`                                                                      |
| Content       | `Scenario`, `ScenarioVersion`                                                        |
| SOC           | `AlertDefinition`, `AlertCase`                                                       |
| Assessment    | `EvaluationRule`, `CaseReport`, `CaseEvaluation`                                     |
| Runtime       | `ScenarioAttempt`, `LabSession`                                                      |
| Security      | `AuditEvent`                                                                         |

---

# RESUMEN

- User puede pertenecer a múltiples Organizations.
- Organizations están aisladas entre sí.
- Un usuario puede tener múltiples roles.
- Group Manager puede tener scope limitado.
- Hay escenarios oficiales públicos.
- Hay escenarios privados de empresa.
- Hay Roadmaps oficiales y privados.
- Un escenario puede asignarse mediante Roadmap o directamente.
- ScenarioEnrollment representa el acceso efectivo.
- El mismo escenario puede utilizarse para TRAINING o ASSESSMENT.
- Los intentos pueden ser limitados o ilimitados.
- Score Policy puede ser FIRST, BEST o LATEST.
- Nunca se sobrescribe un intento anterior.
- Los intentos INVALIDATED no cuentan.
- Un fallo de infraestructura previo a ACTIVE no consume intento.
- ScenarioAttempt y LabSession son entidades diferentes.
- Los laboratorios son temporales y desechables.
- AlertDefinition y AlertCase son entidades diferentes.
- CaseReport y CaseEvaluation son entidades diferentes.
- El Manager puede consultar todo el histórico y los Case Reports completos dentro de su ámbito.
- GitHub es Content Source of Truth.
- PostgreSQL es Operational Source of Truth.
- Los secretos y soluciones nunca se exponen en contenido accesible al alumno.
- Todas las operaciones críticas son auditables.
