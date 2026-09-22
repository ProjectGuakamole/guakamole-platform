# PART 1 – NÚMERO DE TABLAS / CAMPOS

## 1. `TABLA_EMPRESA`: ahora mismo está demasiado detallada

Tenéis:

```text
ID_empresa
Nombre_Empresa
Razon_Social
CIF
Estado_ID
Fecha_Creacion
Pais_ID
Provincia_ID
Ciudad_ID
Direccion
C_Postal
```



Para una plataforma B2B tiene sentido tener `Empresa`, pero yo me preguntaría si para el Alpha necesitamos saber dónde está físicamente la empresa.

Para crear una empresa en Guakamole me bastaría inicialmente con algo parecido a:

```text
ORGANIZATION

id
name
slug
status
created_at
```

Y quizá:

```text
tax_id
```

si realmente queréis mostrar información fiscal.

Todo esto:

```text
Pais
Provincia
Ciudad
Dirección
Código Postal
```

lo dejaría fuera hasta que tengamos facturación o exista una necesidad funcional concreta.

Además, si el producto pretende poder venderse fuera de España, `CIF` ya es un concepto demasiado español. Mejor algo neutral como:

```text
tax_id
```

aunque esto tampoco es imprescindible para el MVP.

---

## 2. `TABLA_USUARIO`: aquí tenemos justo el problema contrario

Actualmente tenéis nombre, apellido, email, fecha de nacimiento y otra vez toda la dirección. 

Hay información que Guakamole probablemente **no necesita**:

```text
Fecha_Nacimiento
Pais
Provincia
Ciudad
Dirección
Código Postal
```

y, sin embargo, faltan campos que sí son esenciales:

```text
email
password_hash
status
created_at
last_login_at
```

Y sobre todo falta responder:

> **¿A qué empresa pertenece ese usuario?**

Ahora mismo `Usuario` no está relacionado con `Empresa`.

Eso sí es crítico para un B2B.

Conceptualmente necesitamos:

```text
EMPRESA
   │
   ├── Usuario Ana
   ├── Usuario Carlos
   └── Usuario Marta
```

Y además necesitamos saber qué puede hacer cada uno:

```text
COMPANY_ADMIN
GROUP_MANAGER
EMPLOYEE
```

No necesitamos necesariamente una enorme arquitectura RBAC para empezar, pero **la relación Usuario ↔ Empresa y el rol sí tienen que existir**.

---

## 3. `TABLA_ESTADO`: yo la eliminaría

Tenéis una tabla genérica:

```text
ID_Estado
Nombre_Estado
```



En apariencia es elegante:

```text
Usuario → Estado
Empresa → Estado
Scenario → Estado
Roadmap → Estado
```

pero realmente los estados de esas entidades no significan lo mismo.

Una empresa puede estar:

```text
ACTIVE
SUSPENDED
```

un usuario:

```text
ACTIVE
DISABLED
INVITED
```

un escenario:

```text
DRAFT
PUBLISHED
ARCHIVED
```

y un intento:

```text
CREATED
IN_PROGRESS
COMPLETED
TIMEOUT
```

Meter todo eso en una única `TABLA_ESTADO` acaba creando cosas raras.

Para el MVP lo haría mucho más sencillo:

```text
Organization.status
User.status
Scenario.status
LabSession.status
ScenarioAttempt.status
```

mediante valores controlados desde la aplicación/PostgreSQL.

---

## 4. `SCENARIOS`: la base está bastante bien

Aquí vais mejor.

Tenéis:

```text
ID_Scenarios
Slug
Scenario_Name
Difficulty
Pub_Priv
Status
Max_Time
Description
```



La idea es correcta.

Solo veo varias correcciones.

### `Max_Time`

Está definido como:

```text
DATE
```

pero no representa una fecha.

Si el escenario dura:

```text
60 minutos
```

yo guardaría:

```text
max_time_minutes INTEGER
```

Por ejemplo:

```text
60
90
120
```

### `Pub_Priv`

Un booleano puede funcionar:

```text
true / false
```

pero pierde claridad.

Preferiría conceptualmente:

```text
visibility

PLATFORM
ORGANIZATION
```

De momento no hace falta construir una tabla para ello.

### Dificultad

Perfectamente puede ser:

```text
difficulty INTEGER
```

y establecer:

```text
1 - 10
```

---

## 5. `ROADMAP`: aquí sí veo confusión

En la hoja aparece como PK:

```text
ID_Grupo
```

para `TABLA_ROADMAP`. 

Supongo que simplemente es un error al construir la hoja y debería ser:

```text
ID_Roadmap
```

Después aparecen conceptos como:

```text
Owner_ID
RoadMap_Name
Description
Difficulty (AVG)
Status
```

Aquí simplificaría.

```text
ROADMAP

id
organization_id
name
description
status
created_at
```

Y eliminaría:

```text
Difficulty AVG
```

porque es un valor calculable a partir de sus escenarios.

No guardaría en BBDD algo que puede derivarse fácilmente:

```text
Scenario 1 difficulty = 4
Scenario 2 difficulty = 6

AVG = 5
```

porque mañana cambias la dificultad de un escenario y puedes acabar con información inconsistente.

---

## 6. Os falta una relación muy importante: Roadmap ↔ Scenario

Un Roadmap tiene varios escenarios:

```text
SOC Analyst Starter

1. Phishing Investigation
2. Suspicious Login
3. SSH Investigation
```

Y potencialmente un escenario puede formar parte de más de un Roadmap.

Por tanto necesitamos algo parecido a:

```text
ROADMAP
   │
   │ 1:N
   ▼
ROADMAP_SCENARIO
   │
   ▼
SCENARIO
```

La tabla intermedia podría contener:

```text
roadmap_id
scenario_id
position
```

Por ejemplo:

```text
roadmap_id | scenario_id | position
-----------------------------------
1          | 7           | 1
1          | 12          | 2
```

Esta sí es una tabla necesaria.

---

## 7. Falta `GROUP`

Curiosamente ya aparece `ID_Grupo` en vuestro Roadmap, pero no veo una tabla de grupos definida.

Para el B2B necesitamos algo como:

```text
EMPRESA ACME
│
├── Grupo SOC Junior
│   ├── Ana
│   ├── Jordi
│   └── Marta
│
└── Grupo SOC Senior
    ├── Carlos
    └── Sergi
```

Por tanto:

```text
GROUP

id
organization_id
name
description
```

y una relación:

```text
GROUP_MEMBER

group_id
user_id
```

---

## 8. Falta la asignación

Tenemos:

```text
Roadmap
```

y:

```text
Grupo
```

pero necesitamos poder decir:

> Asignar `SOC Analyst Starter` al grupo `SOC Junior`.

Por tanto habrá que guardar esa relación.

Algo como:

```text
ROADMAP_ASSIGNMENT

id
roadmap_id
group_id
assigned_at
assigned_by
```

Para el MVP yo simplificaría muchísimo esto.

Inicialmente:

> **Roadmaps se asignan a grupos.**

No intentaría soportar desde el primer día:

```text
Roadmap → usuario
Roadmap → grupo
Scenario → usuario
Scenario → grupo
Scenario → empresa
etc.
```

Eso fue una de las cosas que hizo crecer demasiado nuestro modelo anterior.

---

## 9. Y ahora vienen las tablas realmente importantes que todavía no aparecen

Aquí es donde vuestro modelo todavía no representa el producto que acabamos de definir.

Cuando Ana hace:

```text
Start Scenario
```

necesitamos registrar:

```text
ANA
está realizando
PHISHING SCENARIO
```

Eso es un:

## `SCENARIO_ATTEMPT`

Algo como:

```text
id
user_id
scenario_id
status
started_at
finished_at
score
```

Esto es fundamental.

Si Ana hace el escenario tres veces:

```text
Ana
├── Attempt #1 → 60
├── Attempt #2 → 75
└── Attempt #3 → 92
```

no debemos sobrescribir el resultado anterior.

---

## 10. `LAB_SESSION`

Con nuestra nueva arquitectura, esta tabla es también imprescindible.

Cuando se inicia un escenario:

```text
ScenarioAttempt
       │
       ▼
LabSession
```

Por ejemplo:

```text
LAB_SESSION

id
scenario_attempt_id

provider
status

started_at
expires_at
destroyed_at
```

Luego quizá tenga información de recursos:

```text
AD instance
Workstation instance
Wazuh agents
remote access
```

pero no intentaría diseñar todo eso todavía.

---

## 11. `ALERT_CASE`

Esta es especialmente importante con el cambio que acabamos de hacer.

Un escenario ya no tiene simplemente:

> “una respuesta”.

Tiene:

```text
Phishing Scenario

├── Alert 1 → TP
├── Alert 2 → FP
├── Alert 3 → TP
├── Alert 4 → FP
└── Alert 5 → TP
```

Por tanto necesitamos representar los casos que llegan a nuestra:

```text
Alert Queue
```

Algo parecido a:

```text
ALERT_CASE

id
scenario_attempt_id
external_alert_id
title
severity
status
created_at
```

`external_alert_id` podría permitirnos relacionarlo con Wazuh.

---

## 12. `CASE_REPORT`

Y finalmente:

```text
AlertCase
    │
    ▼
CaseReport
```

Aquí el alumno responde:

```text
classification = TRUE_POSITIVE
severity = HIGH
rationale = "..."
remediation = "..."
```

Por ejemplo:

```text
CASE_REPORT

id
alert_case_id
classification
severity
rationale
remediation
submitted_at
```

Para nuestro MVP esta tabla es mucho más importante que:

```text
Provincia
Ciudad
Código Postal
Fecha de nacimiento
```

Y creo que este contraste muestra muy bien dónde se estaba desviando el modelo.

---

# Si hacemos zoom out, el Domain Model MVP empezaría a verse así

Todavía **no digo que estas sean las tablas finales**.

Pero conceptualmente:

```text
                    ORGANIZATION
                         │
                ┌────────┴─────────┐
                │                  │
              USER               GROUP
                                   │
                                   │
                               GROUP_MEMBER


                    ROADMAP
                       │
                       ▼
                ROADMAP_SCENARIO
                       │
                       ▼
                    SCENARIO


              ROADMAP_ASSIGNMENT
                 GROUP → ROADMAP


                     USER
                       │
                       ▼
                SCENARIO_ATTEMPT
                       │
              ┌────────┴──────────┐
              │                   │
              ▼                   ▼
         LAB_SESSION          ALERT_CASE
                                  │
                                  ▼
                             CASE_REPORT
```

Y observa que ya podemos explicar prácticamente todo el producto con ese dibujo.

---

# PART 2 – Modelo de BBDD

Voy a asumir provisionalmente estas reglas para no disparar la complejidad:

```text
1 usuario → 1 empresa
1 usuario → 1 rol principal
Roadmaps → se asignan a grupos
Contenido del escenario → GitHub
Datos operativos → PostgreSQL
Wazuh → compartido
Lab → individual por intento
```

Podemos cambiar cualquiera de estas decisiones después de revisarlas con el equipo.

## Modelo general propuesto

```text
ORGANIZATION
     │
     ├──────────── USER ──────────── ROLE
     │                │
     │                │
     │              GROUP
     │                │
     │          GROUP_MEMBER
     │
     └──── ROADMAP
              │
        ROADMAP_SCENARIO
              │
           SCENARIO
              │
              │
       SCENARIO_ATTEMPT
              │
       ┌──────┴────────┐
       │               │
   LAB_SESSION     ALERT_CASE
       │               │
  LAB_RESOURCE      CASE_REPORT
```

Y además:

```text
GROUP
  │
  └── ROADMAP_ASSIGNMENT ── ROADMAP
```

---

## 1. `organization`

Representa una empresa cliente.

| Campo        | Tipo orientativo    | Descripción         |
| ------------ | ------------------- | ------------------- |
| `id`         | BIGINT / INT        | PK                  |
| `name`       | VARCHAR(100)        | Nombre visible      |
| `slug`       | VARCHAR(100) UNIQUE | Identificador URL   |
| `status`     | VARCHAR / ENUM      | ACTIVE, SUSPENDED   |
| `created_at` | TIMESTAMP           | Fecha creación      |
| `updated_at` | TIMESTAMP           | Última modificación |

Ejemplo:

```text
id: 1
name: ACME Cybersecurity
slug: acme-cybersecurity
status: ACTIVE
```

Yo eliminaría del MVP:

```text
razón social
país
provincia
ciudad
dirección
código postal
```

que actualmente tenéis en `TABLA_EMPRESA`. 

Podrían volver cuando tengamos facturación.

---

## 2. `role`

Catálogo de roles.

| Campo         | Tipo               | Descripción    |
| ------------- | ------------------ | -------------- |
| `id`          | INT                | PK             |
| `name`        | VARCHAR(50) UNIQUE | Nombre técnico |
| `description` | TEXT               | Descripción    |

Inicialmente:

```text
PLATFORM_ADMIN
COMPANY_ADMIN
GROUP_MANAGER
EMPLOYEE
```

No empezaría creando un sistema de permisos con 30 tablas.

---

## 3. `user`

Representa una cuenta de Guakamole.

| Campo             | Tipo           | Descripción         |
| ----------------- | -------------- | ------------------- |
| `id`              | BIGINT         | PK                  |
| `organization_id` | FK             | Empresa             |
| `role_id`         | FK             | Rol                 |
| `first_name`      | VARCHAR(50)    | Nombre              |
| `last_name`       | VARCHAR(100)   | Apellidos           |
| `email`           | VARCHAR(255)   | Email               |
| `password_hash`   | VARCHAR(255)   | Contraseña hasheada |
| `status`          | VARCHAR / ENUM | ACTIVE, DISABLED    |
| `created_at`      | TIMESTAMP      | Alta                |
| `last_login_at`   | TIMESTAMP NULL | Último acceso       |

Restricción importante:

```text
UNIQUE (organization_id, email)
```

o incluso `email UNIQUE` si decidimos que una cuenta nunca puede pertenecer a más de una empresa.

De vuestra tabla actual quitaría por ahora:

```text
Fecha_Nacimiento
País
Provincia
Ciudad
Dirección
Código Postal
```

porque aparecen actualmente pero no aportan funcionalidad al MVP. 

---

## 4. `group`

Grupo de empleados dentro de una empresa.

| Campo             | Tipo         | Descripción |
| ----------------- | ------------ | ----------- |
| `id`              | BIGINT       | PK          |
| `organization_id` | FK           | Empresa     |
| `name`            | VARCHAR(100) | Nombre      |
| `description`     | TEXT NULL    | Descripción |
| `created_at`      | TIMESTAMP    | Creación    |

Ejemplo:

```text
ACME
├── SOC Junior
├── SOC L1
└── SOC L2
```

---

## 5. `group_member`

Relación usuario ↔ grupo.

| Campo       | Tipo      |
| ----------- | --------- |
| `group_id`  | FK        |
| `user_id`   | FK        |
| `joined_at` | TIMESTAMP |

PK o UNIQUE:

```text
(group_id, user_id)
```

Esto permite:

```text
SOC Junior
├── Ana
├── Carlos
└── Jordi
```

---

## 6. `scenario`

Metadata del escenario.

El contenido detallado seguiría estando en:

```text
guakamole-scenarios
```

GitHub.

La BBDD guarda lo necesario para que la plataforma funcione.

| Campo              | Tipo                | Descripción                  |
| ------------------ | ------------------- | ---------------------------- |
| `id`               | BIGINT              | PK                           |
| `organization_id`  | FK NULL             | NULL = escenario oficial     |
| `slug`             | VARCHAR(180) UNIQUE | Identificador                |
| `name`             | VARCHAR(100)        | Nombre                       |
| `description`      | TEXT                | Descripción                  |
| `difficulty`       | INT                 | Ej. 1-10                     |
| `visibility`       | VARCHAR / ENUM      | PLATFORM / ORGANIZATION      |
| `status`           | VARCHAR / ENUM      | DRAFT / PUBLISHED / ARCHIVED |
| `max_time_minutes` | INT                 | Duración máxima              |
| `repository_path`  | VARCHAR(255)        | Ruta en repo scenarios       |
| `created_at`       | TIMESTAMP           | Creación                     |

Vuestra tabla actual ya tiene buena parte de estos conceptos: slug, nombre, dificultad, público/privado, estado, tiempo máximo y descripción. 

Solo cambiaría, por ejemplo:

```text
Max_Time DATE
```

por:

```text
max_time_minutes INTEGER
```

---

## 7. `roadmap`

Colección ordenada de escenarios.

| Campo             | Tipo           |
| ----------------- | -------------- |
| `id`              | BIGINT         |
| `organization_id` | FK NULL        |
| `name`            | VARCHAR(100)   |
| `description`     | TEXT           |
| `status`          | VARCHAR / ENUM |
| `created_at`      | TIMESTAMP      |

Ejemplo:

```text
SOC Analyst Starter Path
```

No guardaría:

```text
Difficulty AVG
```

porque puede calcularse.

Además, en vuestra hoja aparece `ID_Grupo` como PK del Roadmap, que entiendo que es simplemente un error y debería ser `ID_Roadmap`. 

---

## 8. `roadmap_scenario`

Relaciona Roadmap con Scenario.

| Campo         | Tipo |
| ------------- | ---- |
| `roadmap_id`  | FK   |
| `scenario_id` | FK   |
| `position`    | INT  |

Ejemplo:

```text
SOC Analyst Starter Path

position 1 → Phishing Investigation
position 2 → Suspicious Login
```

Restricción:

```text
UNIQUE (roadmap_id, scenario_id)
```

---

## 9. `roadmap_assignment`

Dice qué grupo tiene asignado qué Roadmap.

| Campo         | Tipo           |
| ------------- | -------------- |
| `id`          | BIGINT         |
| `group_id`    | FK             |
| `roadmap_id`  | FK             |
| `assigned_by` | FK User        |
| `assigned_at` | TIMESTAMP      |
| `due_at`      | TIMESTAMP NULL |
| `status`      | VARCHAR / ENUM |

Por ejemplo:

```text
SOC Junior
       │
       ▼
SOC Analyst Starter Path
```

Con esto no necesitamos inicialmente una compleja tabla de enrolments.

---

## 10. `scenario_attempt`

Una de las tablas más importantes.

Representa:

> Un usuario realizando un escenario.

| Campo          | Tipo               |
| -------------- | ------------------ |
| `id`           | BIGINT             |
| `user_id`      | FK                 |
| `scenario_id`  | FK                 |
| `status`       | VARCHAR / ENUM     |
| `started_at`   | TIMESTAMP          |
| `submitted_at` | TIMESTAMP NULL     |
| `finished_at`  | TIMESTAMP NULL     |
| `score`        | DECIMAL / INT NULL |

Estados iniciales:

```text
CREATED
IN_PROGRESS
SUBMITTED
COMPLETED
TIMEOUT
FAILED
```

Esto nos permite conservar historial:

```text
Ana
└── Phishing
    ├── Attempt #1 → 52
    ├── Attempt #2 → 78
    └── Attempt #3 → 91
```

Nunca sobrescribimos intentos anteriores.

---

## 11. `lab_session`

Representa el laboratorio temporal del intento.

| Campo                 | Tipo           |
| --------------------- | -------------- |
| `id`                  | BIGINT         |
| `scenario_attempt_id` | FK             |
| `provider`            | VARCHAR        |
| `provider_lab_id`     | VARCHAR NULL   |
| `status`              | VARCHAR / ENUM |
| `requested_at`        | TIMESTAMP      |
| `started_at`          | TIMESTAMP NULL |
| `expires_at`          | TIMESTAMP NULL |
| `destroyed_at`        | TIMESTAMP NULL |

Estados:

```text
REQUESTED
PROVISIONING
READY
ACTIVE
EXPIRED
DESTROYED
FAILED
```

Ejemplo:

```text
ScenarioAttempt #81
       │
       ▼
LabSession #32
```

---

## 12. `lab_resource`

Esta tabla creo que nos conviene mucho con la nueva arquitectura.

En vez de poner:

```text
dc_instance_id
workstation_instance_id
```

dentro de `lab_session`, hacemos que una sesión pueda contener N recursos.

| Campo                  | Tipo           |
| ---------------------- | -------------- |
| `id`                   | BIGINT         |
| `lab_session_id`       | FK             |
| `resource_type`        | VARCHAR / ENUM |
| `name`                 | VARCHAR        |
| `provider_resource_id` | VARCHAR        |
| `private_ip`           | VARCHAR NULL   |
| `wazuh_agent_id`       | VARCHAR NULL   |
| `remote_access_ref`    | VARCHAR NULL   |
| `status`               | VARCHAR / ENUM |

Ejemplo:

```text
LabSession 32

├── LAB_RESOURCE
│   type = DOMAIN_CONTROLLER
│   name = ANA-DC
│
└── LAB_RESOURCE
    type = WORKSTATION
    name = ANA-PC
```

Esto nos deja crecer mañana a:

```text
LINUX_SERVER
FIREWALL
MAIL_SERVER
```

sin cambiar la estructura de BBDD.

Para mí esta pequeña abstracción **sí merece la pena**.

---

## 13. `scenario_alert_definition`

Como ahora queremos que cada escenario tenga varias alertas, necesitamos definir qué tipos de casos forman parte de él.

| Campo                     | Tipo         |
| ------------------------- | ------------ |
| `id`                      | BIGINT       |
| `scenario_id`             | FK           |
| `alert_key`               | VARCHAR      |
| `title`                   | VARCHAR      |
| `description`             | TEXT         |
| `default_severity`        | VARCHAR      |
| `wazuh_rule_id`           | VARCHAR NULL |
| `expected_classification` | VARCHAR      |
| `score_weight`            | INT          |

Ejemplo:

```text
phishing-powershell
Suspicious PowerShell Execution
Wazuh Rule 92001
Expected: TRUE_POSITIVE
Weight: 20
```

Importante:

`expected_classification` es información **servidor-side**.

React nunca debería recibir:

```text
expected_classification = TRUE_POSITIVE
```

antes de que el alumno responda.

---

## 14. `alert_case`

Es la instancia real de una alerta dentro del intento del alumno.

No confundamos:

```text
scenario_alert_definition
```

con:

```text
alert_case
```

La primera dice:

> Este escenario puede generar esta alerta.

La segunda dice:

> Ana ha recibido esta alerta durante su intento.

Campos:

| Campo                 | Tipo           |
| --------------------- | -------------- |
| `id`                  | BIGINT         |
| `scenario_attempt_id` | FK             |
| `alert_definition_id` | FK NULL        |
| `external_alert_id`   | VARCHAR NULL   |
| `title`               | VARCHAR        |
| `severity`            | VARCHAR        |
| `status`              | VARCHAR / ENUM |
| `created_at`          | TIMESTAMP      |
| `opened_at`           | TIMESTAMP NULL |
| `closed_at`           | TIMESTAMP NULL |

Estados:

```text
AWAITING_ACTION
OPENED
CLOSED
```

Ejemplo:

```text
Attempt Ana

├── Case 1001 → PowerShell
├── Case 1002 → Failed Logins
├── Case 1003 → Admin Login
└── Case 1004 → Group Change
```

---

## 15. `case_report`

Respuesta del alumno a un Alert Case.

| Campo            | Tipo           |
| ---------------- | -------------- |
| `id`             | BIGINT         |
| `alert_case_id`  | FK UNIQUE      |
| `classification` | VARCHAR / ENUM |
| `severity`       | VARCHAR        |
| `rationale`      | TEXT           |
| `remediation`    | TEXT NULL      |
| `submitted_at`   | TIMESTAMP      |

Clasificación MVP:

```text
TRUE_POSITIVE
FALSE_POSITIVE
```

Aquí guardamos lo que **el alumno responde**, no cuál era la respuesta correcta.

---

# Entonces el núcleo serían 15 tablas

```text
01 organization
02 role
03 user

04 group
05 group_member

06 scenario

07 roadmap
08 roadmap_scenario
09 roadmap_assignment

10 scenario_attempt

11 lab_session
12 lab_resource

13 scenario_alert_definition
14 alert_case
15 case_report
```

Eso es bastante asumible para vuestro equipo.

---

## Lo que deliberadamente NO pondría todavía

Comparándolo con el Domain Model anterior, aparcaría:

```text
OrganizationMembership
MembershipRole
GroupManager
RoadmapEnrollment
ScenarioEnrollment
ScenarioAssignment
ScenarioVersion
AttemptPolicy
EvaluationRule
CaseEvaluation
Invitation
```

No porque estén mal diseñadas.

Porque **todavía no necesitamos esa complejidad**.

Por ejemplo, la evaluación inicial puede hacerse directamente comparando:

```text
CASE_REPORT.classification
```

contra:

```text
SCENARIO_ALERT_DEFINITION.expected_classification
```

y calculando el `ScenarioAttempt.score`.

No necesitamos inmediatamente una tabla `CaseEvaluation`.

---

## Tampoco crearía `TABLA_ESTADO`

Actualmente tenéis una tabla genérica `TABLA_ESTADO`. 

Yo la quitaría.

Cada entidad tiene su propio concepto de estado:

```text
User.status
Organization.status
Scenario.status
ScenarioAttempt.status
LabSession.status
AlertCase.status
```

Que FastAPI/SQLAlchemy controle sus valores válidos.

---

# Modelo relacional completo del MVP

Yo llevaría **este dibujo** a la reunión con los alumnos:

```text
┌──────────────────┐
│   ORGANIZATION   │
└────────┬─────────┘
         │
         │ 1:N
         ▼
┌──────────────────┐       ┌─────────────┐
│       USER       │──────▶│    ROLE     │
└────────┬─────────┘       └─────────────┘
         │
         │
         ▼
┌──────────────────┐
│   GROUP_MEMBER   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│      GROUP       │
└────────┬─────────┘
         │
         ▼
┌──────────────────────┐
│ ROADMAP_ASSIGNMENT   │
└──────────┬───────────┘
           │
           ▼
     ┌───────────┐
     │  ROADMAP  │
     └─────┬─────┘
           │
           ▼
┌─────────────────────┐
│  ROADMAP_SCENARIO   │
└──────────┬──────────┘
           │
           ▼
     ┌────────────┐
     │  SCENARIO  │
     └──────┬─────┘
            │
            ├───────────────┐
            │               │
            ▼               ▼
┌──────────────────┐  ┌──────────────────────────┐
│ SCENARIO_ATTEMPT │  │ SCENARIO_ALERT_DEFINITION│
└────────┬─────────┘  └──────────────────────────┘
         │
    ┌────┴───────────────┐
    │                    │
    ▼                    ▼
┌───────────────┐   ┌──────────────┐
│  LAB_SESSION  │   │  ALERT_CASE  │
└───────┬───────┘   └──────┬───────┘
        │                  │
        ▼                  ▼
┌───────────────┐   ┌──────────────┐
│ LAB_RESOURCE  │   │ CASE_REPORT  │
└───────────────┘   └──────────────┘
```

---

# PART 3 – FUNCIONES DE LOS CAMPOS

Claro. De hecho, este nivel de detalle creo que es justo el que os conviene antes de empezar a crear modelos SQLAlchemy: **que cada alumno pueda mirar un campo y saber por qué existe**.

Mantendría por ahora las 15 tablas que acabamos de definir.

## 1. `organization`

Representa una empresa cliente de Guakamole.

| Campo        | Función                                                                                          |
| ------------ | ------------------------------------------------------------------------------------------------ |
| `id`         | Identificador único de la empresa. Es la PK.                                                     |
| `name`       | Nombre que verá el usuario, por ejemplo `ACME Cybersecurity`.                                    |
| `slug`       | Nombre único simplificado pensado para URLs e identificadores, por ejemplo `acme-cybersecurity`. |
| `status`     | Indica si la empresa puede utilizar la plataforma. Por ejemplo `ACTIVE` o `SUSPENDED`.           |
| `created_at` | Fecha y hora en que se creó la empresa.                                                          |
| `updated_at` | Fecha y hora de la última modificación de la empresa.                                            |

Ejemplo:

```text
id          12
name        ACME Cybersecurity
slug        acme-cybersecurity
status      ACTIVE
created_at  2026-09-22 10:00
updated_at  2026-09-22 10:00
```

El `slug` nos puede servir, por ejemplo, para:

```text
guakamole.io/company/acme-cybersecurity
```

---

## 2. `role`

Define qué función tiene un usuario dentro de Guakamole.

| Campo         | Función                                                              |
| ------------- | -------------------------------------------------------------------- |
| `id`          | Identificador único del rol.                                         |
| `name`        | Nombre técnico del rol. Ej. `COMPANY_ADMIN`.                         |
| `description` | Explica qué representa el rol y qué tipo de usuario debería tenerlo. |

Ejemplos:

```text
1  PLATFORM_ADMIN
2  COMPANY_ADMIN
3  GROUP_MANAGER
4  EMPLOYEE
```

En esta primera versión el rol nos ayuda a decidir cosas como:

```text
EMPLOYEE
→ hacer escenarios

GROUP_MANAGER
→ consultar resultados de su grupo

COMPANY_ADMIN
→ gestionar usuarios/grupos
```

---

## 3. `user`

Representa una cuenta de usuario.

| Campo             | Función                                                                  |
| ----------------- | ------------------------------------------------------------------------ |
| `id`              | Identificador único del usuario.                                         |
| `organization_id` | FK que indica a qué empresa pertenece.                                   |
| `role_id`         | FK que indica qué rol tiene.                                             |
| `first_name`      | Nombre del usuario.                                                      |
| `last_name`       | Apellidos.                                                               |
| `email`           | Dirección utilizada para identificar/iniciar sesión.                     |
| `password_hash`   | Hash de la contraseña. Nunca se guarda la contraseña original.           |
| `status`          | Indica si la cuenta está activa, deshabilitada, etc.                     |
| `created_at`      | Momento en que se creó la cuenta.                                        |
| `last_login_at`   | Último inicio de sesión correcto. Puede ser `NULL` si nunca ha accedido. |

Ejemplo:

```text
id               53
organization_id  12
role_id           4
first_name        Ana
last_name         García
email             ana@acme.com
password_hash     ...
status            ACTIVE
created_at        ...
last_login_at     ...
```

Muy importante:

```text
password_hash
```

no es:

```text
Password123!
```

sino algo derivado mediante un algoritmo seguro de hashing.

---

## 4. `group`

Representa un grupo de empleados dentro de una empresa.

| Campo             | Función                               |
| ----------------- | ------------------------------------- |
| `id`              | Identificador único del grupo.        |
| `organization_id` | Empresa a la que pertenece el grupo.  |
| `name`            | Nombre del grupo.                     |
| `description`     | Explica para qué se utiliza el grupo. |
| `created_at`      | Fecha de creación.                    |

Ejemplo:

```text
id               8
organization_id  12
name             SOC Junior
description      Analistas SOC en formación
```

Una empresa podría tener:

```text
ACME
├── SOC Junior
├── SOC L1
└── SOC L2
```

---

## 5. `group_member`

Relaciona usuarios con grupos.

Es una tabla intermedia.

| Campo       | Función                                 |
| ----------- | --------------------------------------- |
| `group_id`  | Grupo al que pertenece el usuario.      |
| `user_id`   | Usuario que forma parte del grupo.      |
| `joined_at` | Momento en el que fue añadido al grupo. |

Ejemplo:

```text
group_id  user_id
8         53
8         61
8         72
```

Significaría:

```text
SOC Junior
├── User 53
├── User 61
└── User 72
```

Esta tabla permite además que en el futuro un usuario pueda formar parte de varios grupos si lo necesitamos.

---

## 6. `scenario`

Representa un escenario disponible dentro de Guakamole.

No contiene necesariamente todo el contenido del escenario; gran parte seguirá en `guakamole-scenarios`.

| Campo              | Función                                                                            |
| ------------------ | ---------------------------------------------------------------------------------- |
| `id`               | Identificador único del escenario.                                                 |
| `organization_id`  | Empresa propietaria si es un escenario privado. `NULL` si es oficial de Guakamole. |
| `slug`             | Identificador único legible para URLs/configuración.                               |
| `name`             | Nombre visible del escenario.                                                      |
| `description`      | Explica de qué trata.                                                              |
| `difficulty`       | Dificultad, por ejemplo de 1 a 10.                                                 |
| `visibility`       | Indica quién puede utilizarlo.                                                     |
| `status`           | Estado editorial del escenario.                                                    |
| `max_time_minutes` | Tiempo máximo permitido para realizarlo.                                           |
| `repository_path`  | Ubicación del contenido dentro de `guakamole-scenarios`.                           |
| `created_at`       | Fecha de creación.                                                                 |

Ejemplo:

```text
id                7
organization_id   NULL
slug              phishing-investigation
name              Phishing Investigation
difficulty        6
visibility        PLATFORM
status            PUBLISHED
max_time_minutes  90
repository_path   scenarios/phishing-001
```

### `visibility`

Podría contener:

```text
PLATFORM
ORGANIZATION
```

`PLATFORM`:

> disponible para clientes de Guakamole.

`ORGANIZATION`:

> pertenece únicamente a una empresa concreta.

### `status`

Podría ser:

```text
DRAFT
PUBLISHED
ARCHIVED
```

---

## 7. `roadmap`

Representa una ruta formativa.

Ejemplo:

```text
SOC Analyst Starter Path
```

| Campo             | Función                                                            |
| ----------------- | ------------------------------------------------------------------ |
| `id`              | Identificador único del Roadmap.                                   |
| `organization_id` | Empresa propietaria. `NULL` si es un Roadmap oficial de Guakamole. |
| `name`            | Nombre del Roadmap.                                                |
| `description`     | Explicación de qué se aprenderá.                                   |
| `status`          | Indica si está disponible, en borrador, archivado, etc.            |
| `created_at`      | Fecha de creación.                                                 |

Ejemplo:

```text
SOC Analyst Starter Path

Introducción práctica al trabajo de un analista SOC.
```

---

## 8. `roadmap_scenario`

Indica qué escenarios forman parte de un Roadmap y en qué orden.

| Campo         | Función                     |
| ------------- | --------------------------- |
| `roadmap_id`  | Roadmap al que pertenece.   |
| `scenario_id` | Escenario incluido.         |
| `position`    | Posición dentro de la ruta. |

Ejemplo:

```text
roadmap_id  scenario_id  position
1           7            1
1           13           2
1           18           3
```

Resultado:

```text
SOC Analyst Starter Path

1. Phishing Investigation
2. Suspicious Login
3. SSH Investigation
```

`position` es importante porque una relación N:M por sí sola no sabría cuál va primero.

---

## 9. `roadmap_assignment`

Registra que una empresa ha asignado un Roadmap a un grupo.

| Campo         | Función                              |
| ------------- | ------------------------------------ |
| `id`          | Identificador de la asignación.      |
| `group_id`    | Grupo que debe completar el Roadmap. |
| `roadmap_id`  | Roadmap asignado.                    |
| `assigned_by` | Usuario que realizó la asignación.   |
| `assigned_at` | Fecha en la que fue asignado.        |
| `due_at`      | Fecha límite opcional.               |
| `status`      | Estado de la asignación.             |

Ejemplo:

```text
SOC Junior
       ↓
SOC Analyst Starter Path
```

`assigned_by` permite saber, por ejemplo:

> El administrador Carlos asignó este Roadmap.

Puede ser útil tanto para auditoría como para mostrarlo en la aplicación.

---

## 10. `scenario_attempt`

Representa **una ejecución concreta de un escenario por parte de un usuario**.

Esta es una de las tablas centrales.

| Campo          | Función                                       |
| -------------- | --------------------------------------------- |
| `id`           | Identificador del intento.                    |
| `user_id`      | Usuario que está realizando el escenario.     |
| `scenario_id`  | Escenario que está realizando.                |
| `status`       | Estado actual del intento.                    |
| `started_at`   | Cuándo empezó.                                |
| `submitted_at` | Cuándo el alumno entregó su trabajo.          |
| `finished_at`  | Cuándo se considera completamente finalizado. |
| `score`        | Puntuación final obtenida.                    |

Ejemplo:

```text
Ana
└── Phishing Investigation
    ├── Attempt #101 → 65
    ├── Attempt #152 → 78
    └── Attempt #203 → 92
```

Por eso necesitamos una tabla de intentos en vez de guardar simplemente:

```text
User.score
```

### `status`

Podría tener:

```text
CREATED
IN_PROGRESS
SUBMITTED
COMPLETED
TIMEOUT
FAILED
```

`submitted_at` y `finished_at` pueden parecer iguales, pero conceptualmente no tienen por qué serlo.

Ejemplo:

```text
14:32 → alumno pulsa Submit
         submitted_at

14:32 → backend corrige/calcula resultados

14:33 → attempt COMPLETED
         finished_at
```

---

## 11. `lab_session`

Representa el laboratorio temporal asociado a un intento.

| Campo                 | Función                                             |
| --------------------- | --------------------------------------------------- |
| `id`                  | Identificador del laboratorio.                      |
| `scenario_attempt_id` | Intento al que pertenece.                           |
| `provider`            | Tecnología/proveedor donde se ejecuta.              |
| `provider_lab_id`     | Identificador que el proveedor da al laboratorio.   |
| `status`              | Estado del laboratorio.                             |
| `requested_at`        | Momento en que Guakamole solicitó crearlo.          |
| `started_at`          | Momento en que realmente quedó disponible/iniciado. |
| `expires_at`          | Momento máximo hasta el que puede utilizarse.       |
| `destroyed_at`        | Momento en que se eliminó.                          |

Ejemplo:

```text
provider:
OCI
```

Mañana podría ser:

```text
AWS
LOCAL_KVM
```

sin cambiar el resto del producto.

### `provider_lab_id`

Por ejemplo Oracle podría decir:

```text
ocid1.instancepool.xxxxx
```

o nosotros podríamos manejar algún identificador que permita localizar los recursos asociados.

No es un dato que tenga que ver el alumno.

---

## 12. `lab_resource`

Representa cada máquina/recurso que contiene un LabSession.

Esto evita que `lab_session` dependa de que siempre tengamos dos máquinas.

| Campo                  | Función                                           |
| ---------------------- | ------------------------------------------------- |
| `id`                   | Identificador del recurso.                        |
| `lab_session_id`       | Laboratorio al que pertenece.                     |
| `resource_type`        | Qué tipo de recurso es.                           |
| `name`                 | Nombre asignado al recurso.                       |
| `provider_resource_id` | ID que le da OCI/AWS/etc.                         |
| `private_ip`           | IP interna de la máquina.                         |
| `wazuh_agent_id`       | Identificador del agente asociado en Wazuh.       |
| `remote_access_ref`    | Referencia necesaria para abrir la sesión remota. |
| `status`               | Estado actual del recurso.                        |

Ejemplo:

```text
LAB_SESSION 32

Resource 81
type = DOMAIN_CONTROLLER
name = ANA-DC

Resource 82
type = WORKSTATION
name = ANA-PC
```

### `resource_type`

En el MVP:

```text
DOMAIN_CONTROLLER
WORKSTATION
```

En el futuro podría aparecer:

```text
LINUX_SERVER
FIREWALL
MAIL_SERVER
```

sin cambiar la tabla.

### `provider_resource_id`

Nos permite decir:

> destruye esta instancia concreta en OCI.

### `wazuh_agent_id`

Relaciona:

```text
ANA-PC de Guakamole
```

con:

```text
Agent 057 de Wazuh
```

Esto será muy importante para saber qué eventos pertenecen a qué laboratorio.

### `remote_access_ref`

No guardaría aquí contraseñas.

Guardaría una referencia como:

```text
guacamole_connection_id = 472
```

o equivalente.

---

## 13. `scenario_alert_definition`

Describe las alertas/casos que forman parte del diseño del escenario.

Podemos pensar en ella como la **plantilla de una alerta**.

| Campo                     | Función                                           |
| ------------------------- | ------------------------------------------------- |
| `id`                      | Identificador de la definición.                   |
| `scenario_id`             | Escenario al que pertenece.                       |
| `alert_key`               | Identificador interno único dentro del escenario. |
| `title`                   | Nombre que puede aparecer en la Alert Queue.      |
| `description`             | Explicación del tipo de alerta.                   |
| `default_severity`        | Severidad prevista inicialmente.                  |
| `wazuh_rule_id`           | Regla de Wazuh relacionada, si existe.            |
| `expected_classification` | Respuesta correcta esperada.                      |
| `score_weight`            | Peso de esta alerta sobre la puntuación.          |

Ejemplo:

```text
alert_key:
suspicious-powershell

title:
Suspicious PowerShell Execution

wazuh_rule_id:
92001

expected_classification:
TRUE_POSITIVE

score_weight:
20
```

### `alert_key`

Nos permite tener un identificador estable que no dependa del nombre visible.

Mejor:

```text
suspicious-powershell
```

que depender de:

```text
"Suspicious PowerShell Execution"
```

que puede cambiar o traducirse.

### `expected_classification`

Este dato es **sensible desde el punto de vista del ejercicio**.

Nunca debe aparecer en el frontend antes de que el alumno haya respondido.

Si no:

```text
GET /api/alert
```

y el alumno podría descubrir:

```json
{
  "expected_classification": "TRUE_POSITIVE"
}
```

y arruinamos el ejercicio.

---

## 14. `alert_case`

Representa una alerta concreta que recibe el alumno durante un intento.

La diferencia con la tabla anterior es importante:

```text
scenario_alert_definition
=
qué alerta puede existir
```

mientras:

```text
alert_case
=
la alerta concreta que ha recibido Ana
```

| Campo                 | Función                                      |
| --------------------- | -------------------------------------------- |
| `id`                  | Identificador del caso.                      |
| `scenario_attempt_id` | Intento en el que apareció.                  |
| `alert_definition_id` | Definición de escenario que originó el caso. |
| `external_alert_id`   | Identificador equivalente en Wazuh.          |
| `title`               | Título mostrado al alumno.                   |
| `severity`            | Severidad del caso concreto.                 |
| `status`              | Estado dentro de la Alert Queue.             |
| `created_at`          | Momento en que apareció.                     |
| `opened_at`           | Momento en que el alumno empezó a revisarlo. |
| `closed_at`           | Momento en que lo cerró.                     |

Ejemplo:

```text
id                   1001
scenario_attempt_id  203
alert_definition_id  8
external_alert_id     wazuh-778912
title                 Suspicious PowerShell
severity              HIGH
status                OPENED
```

### ¿Por qué copiamos `title` y `severity`?

Aunque ya existen en `scenario_alert_definition`, puede interesarnos conservar cómo era exactamente el caso durante ese intento.

Por ejemplo, la definición podría cambiar en el futuro.

El intento histórico debería seguir mostrando lo que Ana realmente vio.

---

## 15. `case_report`

Es el análisis que entrega el alumno para un Alert Case.

| Campo            | Función                                        |
| ---------------- | ---------------------------------------------- |
| `id`             | Identificador del informe.                     |
| `alert_case_id`  | Caso que se está respondiendo.                 |
| `classification` | Decisión TP o FP del alumno.                   |
| `severity`       | Severidad que considera que tiene.             |
| `rationale`      | Explicación de por qué ha tomado esa decisión. |
| `remediation`    | Medidas correctivas realizadas o propuestas.   |
| `submitted_at`   | Momento de entrega.                            |

Ejemplo:

```text
classification:
TRUE_POSITIVE

severity:
HIGH

rationale:
El proceso powershell.exe fue ejecutado por WINWORD.exe
después de abrir el documento recibido por correo...

remediation:
Se deshabilitó la cuenta comprometida y se eliminó...
```

La diferencia fundamental es:

```text
scenario_alert_definition.expected_classification
```

es:

> la solución que conoce Guakamole.

Mientras:

```text
case_report.classification
```

es:

> lo que respondió el alumno.

Entonces FastAPI puede comparar:

```text
TRUE_POSITIVE == TRUE_POSITIVE

✓ Correcto
```

---

# Visto desde una historia completa

Creo que esta es la mejor manera de que los alumnos entiendan para qué sirven las tablas.

Imaginemos:

```text
ACME
```

Se crea en:

```text
organization
```

---

Creamos:

```text
Ana García
```

en:

```text
user
```

que pertenece a:

```text
organization = ACME
role = EMPLOYEE
```

---

Ana pertenece al grupo:

```text
SOC Junior
```

mediante:

```text
group
+
group_member
```

---

A SOC Junior le asignamos:

```text
SOC Analyst Starter
```

mediante:

```text
roadmap_assignment
```

---

Ese Roadmap contiene:

```text
1. Phishing Investigation
2. Suspicious Login
```

mediante:

```text
roadmap
+
roadmap_scenario
+
scenario
```

---

Ana pulsa:

```text
START
```

Guakamole crea:

```text
scenario_attempt
```

---

Después crea:

```text
lab_session
```

que contiene:

```text
lab_resource

├── ANA-DC
└── ANA-PC
```

---

El Scenario Event Generator provoca:

```text
PowerShell sospechoso
```

Wazuh detecta:

```text
alert 778912
```

y Guakamole crea:

```text
alert_case
```

basándose en:

```text
scenario_alert_definition
```

---

Ana investiga:

```text
Alert Queue
   ↓
Wazuh
   ↓
ANA-PC
   ↓
ANA-DC
```

y entrega:

```text
case_report
```

con:

```text
TRUE_POSITIVE
HIGH
rationale
remediation
```

---

Y finalmente:

```text
scenario_attempt.score = 85
```

Ese recorrido demuestra algo importante: **todas las tablas tienen ahora una razón funcional clara para existir**.

Yo usaría precisamente este criterio con el equipo antes de empezar SQLAlchemy: cada alumno debería poder explicar no solo los campos, sino contar esta historia de principio a fin. Si pueden hacerlo, el modelo está suficientemente entendido como para empezar a construirlo.

# PART 4 – SCHEMAS

Un `schema` de PostgreSQL es básicamente un **namespace/carpeta lógica dentro de la misma base de datos**:

```text
guakamole_db
│
├── iam
├── content
├── training
└── lab
```

No son cuatro bases de datos distintas. Todas pueden relacionarse mediante FK.

## 1. Los schemas que propondría

Para el MVP me quedaría únicamente con **4 schemas**.

| Schema     | Responsabilidad                                  |
| ---------- | ------------------------------------------------ |
| `iam`      | Empresas, usuarios, roles y grupos               |
| `content`  | Roadmaps, escenarios y definición de las alertas |
| `training` | Actividad realizada por los alumnos              |
| `lab`      | Infraestructura temporal de los escenarios       |

Y más adelante podríamos añadir:

```text
audit
```

cuando implementemos los eventos de auditoría.

La BBDD quedaría así:

```text
guakamole_db
│
├── iam
│   ├── organizations
│   ├── roles
│   ├── users
│   ├── user_credentials
│   ├── user_groups
│   └── group_members
│
├── content
│   ├── scenarios
│   ├── roadmaps
│   ├── roadmap_scenarios
│   └── scenario_alert_definitions
│
├── training
│   ├── roadmap_assignments
│   ├── scenario_attempts
│   ├── alert_cases
│   └── case_reports
│
└── lab
    ├── lab_sessions
    └── lab_resources
```

Eso me parece ya muy limpio.

---

## 2. `iam`

**Identity & Access Management**.

Aquí guardamos quién utiliza Guakamole y a qué empresa pertenece.

```text
iam
│
├── organizations
├── roles
├── users
├── user_credentials
├── user_groups
└── group_members
```

### `iam.organizations`

```text
ACME
CyberCorp
OpenAI Security Training
...
```

### `iam.users`

```text
Ana
Carlos
Jordi
...
```

### `iam.roles`

```text
PLATFORM_ADMIN
COMPANY_ADMIN
GROUP_MANAGER
EMPLOYEE
```

### `iam.user_groups`

Lo llamaría así y no simplemente `group`, porque `GROUP` forma parte del lenguaje SQL (`GROUP BY`) y es mejor evitar nombres que puedan generar confusión.

```text
SOC Junior
SOC L1
SOC L2
```

### `iam.group_members`

Relaciona:

```text
Usuario ↔ Grupo
```

---

## 3. `content`

Aquí está la **definición del contenido formativo**.

```text
content
│
├── scenarios
├── roadmaps
├── roadmap_scenarios
└── scenario_alert_definitions
```

Por ejemplo:

```text
content.scenarios

Phishing Investigation
Suspicious SSH Activity
```

Y:

```text
content.roadmaps

SOC Analyst Starter Path
```

Mientras:

```text
content.roadmap_scenarios
```

dice:

```text
SOC Analyst Starter Path
├── 1. Phishing Investigation
└── 2. Suspicious SSH Activity
```

Y:

```text
content.scenario_alert_definitions
```

define las alertas que hemos diseñado para un escenario.

---

## 4. `training`

Este schema contiene algo diferente: **lo que realmente hacen los alumnos**.

```text
training
│
├── roadmap_assignments
├── scenario_attempts
├── alert_cases
└── case_reports
```

Esto permite separar claramente:

```text
content.scenarios
```

> Define cómo es Phishing Investigation.

de:

```text
training.scenario_attempts
```

> Ana está haciendo Phishing Investigation.

Y también:

```text
content.scenario_alert_definitions
```

> En este escenario existe una alerta de PowerShell.

frente a:

```text
training.alert_cases
```

> Ana ha recibido una instancia de esa alerta.

Esta separación me gusta especialmente.

---

## 5. `lab`

Aquí dejamos exclusivamente la infraestructura.

```text
lab
│
├── lab_sessions
└── lab_resources
```

Por ejemplo:

```text
lab.lab_sessions

Session #427
Usuario Ana
Scenario Attempt #52
OCI
ACTIVE
```

y:

```text
lab.lab_resources

Session #427
├── ANA-DC
└── ANA-PC
```

Así FastAPI sabe qué infraestructura corresponde a cada intento.

---

## 6. Relaciones entre schemas

No hay ningún problema en hacer:

```text
training.scenario_attempts.user_id
```

como FK hacia:

```text
iam.users.id
```

Por ejemplo:

```text
iam.users
    │
    │
    ▼
training.scenario_attempts
    │
    │
    ▼
lab.lab_sessions
```

Y al otro lado:

```text
content.scenarios
       │
       ▼
training.scenario_attempts
```

Eso es precisamente lo bueno de utilizar schemas: **separación lógica sin separar la información en distintas bases de datos**.

---

## Sobre sacar `password_hash` de `users`

Sí, **me gusta vuestra idea**, con un matiz importante.

Podemos pasar de:

```text
iam.users

id
organization_id
role_id
first_name
last_name
email
password_hash       ← aquí
status
...
```

a:

```text
iam.users

id
organization_id
role_id
first_name
last_name
email
status
created_at
last_login_at
```

y crear:

```text
iam.user_credentials
```

con:

| Campo           | Función                                    |
| --------------- | ------------------------------------------ |
| `user_id`       | Usuario al que pertenecen las credenciales |
| `password_hash` | Hash seguro de su contraseña               |

Por ejemplo:

```text
iam.users

id = 52
email = ana@acme.com
```

y:

```text
iam.user_credentials

user_id = 52
password_hash = $argon2id$...
```

Relación:

```text
USERS
  1
  │
  │
  1
  ▼
USER_CREDENTIALS
```

---

## ¿Por qué me gusta separarlo?

Conceptualmente queda muy limpio:

```text
iam.users
=
quién es el usuario
```

mientras:

```text
iam.user_credentials
=
cómo se autentica
```

Además mañana podríais evolucionar a:

```text
Password
TOTP
SSO
Microsoft Entra ID
Google
etc.
```

sin convertir `users` en una tabla llena de datos de autenticación.

También permite que determinadas consultas internas trabajen con:

```text
iam.users
```

sin necesitar tocar las credenciales.

---

# Pero una advertencia importante

Separarlo **no hace mágicamente más segura la contraseña**.

Si FastAPI utiliza una cuenta PostgreSQL que tiene permiso para hacer:

```sql
SELECT * FROM iam.users;
```

y también:

```sql
SELECT * FROM iam.user_credentials;
```

un compromiso total de esa cuenta podría seguir permitiendo consultar ambos.

La principal ventaja ahora mismo sería:

> **separación de responsabilidades y mejor diseño**, no una barrera criptográfica adicional.

Más adelante podríamos aplicar permisos distintos si fuese necesario.

---

## Yo incluso añadiría un tercer campo

En vez de:

```text
user_id
password_hash
```

haría:

```text
user_id
password_hash
password_updated_at
```

porque es barato y nos puede resultar útil.

| Campo                 | Función                  |
| --------------------- | ------------------------ |
| `user_id`             | Identifica al usuario    |
| `password_hash`       | Hash de contraseña       |
| `password_updated_at` | Última vez que se cambió |

Por ejemplo:

```text
user_id              52
password_hash         $argon2id$v=19$...
password_updated_at   2026-09-22 18:20:12
```

Puede servir posteriormente para cosas como:

```text
"Contraseña cambiada hace..."
```

o invalidar determinadas sesiones después de un cambio.

No añadiría ahora:

```text
password_history
security_questions
password_expiration
etc.
```

Eso sería volver a complicarnos.

---

### Y no necesitamos guardar un `salt` separado

Si utilizamos un algoritmo moderno como Argon2id o bcrypt, el valor almacenado normalmente ya contiene los parámetros y el salt necesarios.

Por ejemplo:

```text
$argon2id$v=19$m=65536,t=3,p=4$...$...
```

Por tanto no crearía:

```text
password_hash
password_salt
```

para vuestro diseño.

Simplemente:

```text
password_hash
```

---

# Así actualizaría nuestras 16 tablas

Con esta decisión pasamos técnicamente de 15 a **16 tablas**:

```text
IAM
────────────────────────
01 organizations
02 roles
03 users
04 user_credentials
05 user_groups
06 group_members


CONTENT
────────────────────────
07 scenarios
08 roadmaps
09 roadmap_scenarios
10 scenario_alert_definitions


TRAINING
────────────────────────
11 roadmap_assignments
12 scenario_attempts
13 alert_cases
14 case_reports


LAB
────────────────────────
15 lab_sessions
16 lab_resources
```

Y creo que queda bastante coherente.

## Incluso visualmente

```text
                        GUAKAMOLE DB

 ┌──────────────────────────────────────────────────────┐
 │ IAM                                                  │
 │                                                      │
 │ Organization ── Users ── UserCredentials             │
 │                   │                                  │
 │                  Roles                               │
 │                   │                                  │
 │            GroupMembers ── UserGroups                │
 └──────────────────────────────────────────────────────┘

 ┌──────────────────────────────────────────────────────┐
 │ CONTENT                                              │
 │                                                      │
 │ Roadmaps ── RoadmapScenarios ── Scenarios            │
 │                                  │                   │
 │                                  └─ AlertDefinitions │
 └──────────────────────────────────────────────────────┘

 ┌──────────────────────────────────────────────────────┐
 │ TRAINING                                             │
 │                                                      │
 │ RoadmapAssignments                                   │
 │ ScenarioAttempts                                     │
 │        │                                             │
 │        └── AlertCases ── CaseReports                 │
 └──────────────────────────────────────────────────────┘

 ┌──────────────────────────────────────────────────────┐
 │ LAB                                                  │
 │                                                      │
 │ LabSessions ── LabResources                          │
 └──────────────────────────────────────────────────────┘
```

Este nivel de separación me parece **ideal para vuestro MVP**: suficientemente profesional para que PostgreSQL esté bien organizado, pero sin llegar a crear una arquitectura de BBDD que los alumnos no puedan entender.

Y hay además una consecuencia práctica que merece la pena aplicar desde el principio: en SQLAlchemy yo ya definiría los modelos con su schema explícito, por ejemplo `iam.users`, `content.scenarios`, `training.scenario_attempts`, etc., para que Alembic genere las migraciones respetando esta estructura.

# PART 5 – FOTOS Y VIDEO

- [FOTO Y VIDEO](https://drive.google.com/drive/folders/1-E2AEVgfcjxgAXMvZ5vjWws9e9-RdLV5?usp=sharing)