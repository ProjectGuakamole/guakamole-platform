# PROJECT CHARTER — PROJECT GUAKAMOLE

**Versión:** 0.1
**Estado:** Draft para validación
**Fase:** MVP / Product Validation
**Duración:** 125 horas por miembro
**Capacidad bruta:** 625 horas
**Herramientas de trabajo:** ClickUp · GitHub · Slack


## Nombre del proyecto

**Project Guakamole**

Nombre provisional de una plataforma B2B de entrenamiento práctico en operaciones de ciberseguridad y simulación de un Security Operations Center.

## Visión

Crear una plataforma que permita a empresas entrenar y evaluar a sus equipos de ciberseguridad mediante **escenarios SOC prácticos y temporales**, en los que los usuarios deban comportarse como analistas reales:

```text
Recibir alerta → Investigar → Consultar SIEM / evidencias / endpoint → Determinar True Positive / False Positive → Documentar el incidente → Cerrar el caso → Obtener resultado y progreso
```

La plataforma debe permitir a la empresa saber no solamente qué formación ha realizado un empleado, sino **cómo se desempeña ante situaciones prácticas de seguridad**.

## Problema que queremos resolver

> ¿Puede esta persona trabajar como analista cuando aparece una alerta real?

Project Guakamole pretende aproximarse a esa pregunta mediante simulaciones SOC controladas.

## Propuesta de valor

- **Asignar entrenamiento práctico, observar el progreso de sus equipos y medir cómo investigan y gestionan incidentes de seguridad.**
- **Practicar tareas similares a las de un SOC real utilizando herramientas, evidencias y laboratorios aislados.**

> Crear una plataforma reutilizable sobre la que posteriormente puedan desarrollarse múltiples roadmaps y escenarios sin reconstruir la infraestructura.

---

# OBJETIVO MVP

Al terminar las 125 horas debemos disponer de un producto demostrable que permita realizar de extremo a extremo este flujo:

```text
EMPRESA
   │
   ├── crea organización
   ├── invita usuarios
   ├── crea grupos
   ├── asigna Manager
   └── asigna Roadmap
              │
              ▼
           USUARIO
              │
              ├── accede al Roadmap
              ├── inicia escenario
              ├── recibe laboratorio
              ├── investiga alertas
              ├── utiliza SIEM / VM
              ├── clasifica TP / FP
              ├── redacta Case Report
              └── finaliza escenario
                        │
                        ▼
                   MANAGER
                        │
                        └── consulta resultado
                            y progreso
```

Si podemos hacer esta demostración **sin operaciones manuales ocultas**, consideraremos validado el MVP.


## Usuarios del sistema

| Perfil                 | Responsabilidad                                      |
| ---------------------- | ---------------------------------------------------- |
| **Platform Admin**     | Administra globalmente Project Guakamole.            |
| **Company Admin**      | Administra una única organización.                   |
| **Group Manager**      | Gestiona determinados grupos y supervisa resultados. |
| **Scenario Editor**    | Crea y modifica escenarios autorizados.              |
| **Employee / Learner** | Realiza roadmaps, escenarios y simulaciones.         |

Los permisos deberán diseñarse mediante **RBAC** y no mediante un único campo rígido de tipo de usuario.

Una persona podrá eventualmente disponer de varios roles.


### Modelo B2B

La plataforma será **multiempresa desde el MVP**.

```text
PROJECT GUAKAMOLE
│
├── Organization A
│   ├── Company Admin
│   ├── Managers
│   ├── Groups
│   └── Employees
│
├── Organization B
│   ├── Company Admin
│   ├── Managers
│   ├── Groups
│   └── Employees
│
└── Organization N
```

Requisito fundamental:

> Los datos y recursos de una organización no deben ser accesibles desde otra organización.

El aislamiento multi-tenant será considerado tanto requisito funcional como requisito de seguridad.


## Roadmap

**MVP Roadmap**

```text
SOC ANALYST — STARTER PATH

          ●
          │
          ▼
┌──────────────────────────┐
│ Phishing Investigation   │
│ Flagship Scenario        │
└─────────────┬────────────┘
              │
              ▼
┌──────────────────────────┐
│ Suspicious Activity      │
│ Secondary Scenario       │
└──────────────────────────┘
```

La organización podrá asignarlo a usuarios o grupos.


## Escenario SOC

Un escenario representa una simulación práctica.

No será simplemente:

```text
teoría → pregunta → flag
```

sino:

```text
contexto
   ↓
alertas
   ↓
investigación
   ↓
evidencias
   ↓
decisión
   ↓
case report
   ↓
evaluación
```

Un escenario podrá contener:

| Componente  | Función                                        |
| ----------- | ---------------------------------------------- |
| Metadata    | Nombre, descripción, dificultad, XP, duración. |
| Contenido   | Markdown, documentación y recursos.            |
| Alerts      | Alertas que debe investigar el alumno.         |
| SIEM        | Consulta de eventos/evidencias.                |
| Analyst VM  | Entorno del analista.                          |
| Lab         | Infraestructura específica del escenario.      |
| Case Report | Informe final.                                 |
| Evaluation  | Resultado, TP/FP, evidencias, tiempo.          |


---

# SOC Simulator

El corazón diferencial del producto será el **SOC Simulator**.

El usuario deberá disponer como mínimo de:

```text
Dashboard
Alert Queue
SIEM
Analyst VM
Documentation
Case Reports
```

El objetivo es conseguir una experiencia suficientemente auténtica para que el usuario tenga que:

* analizar información;
* correlacionar evidencias;
* tomar una decisión;
* justificarla.

## Gestión de alertas

Cada alerta deberá poder contener como mínimo:

```text
Alert ID
Alert Rule
Description
Severity
Incident Type
Timestamp
Status
```

El usuario deberá poder abrirla y posteriormente determinar: *TRUE POSITIVE o FALSE POSITIVE*


La decisión deberá acompañarse de un **Closure Rationale / Incident Report**.


## Case Report

El Case Report será parte obligatoria de los escenarios SOC.

Como mínimo deberá recoger:

- Clasificación: TP / FP
- Tiempo de actividad
- Severidad
- Justificación del cierre


En fases posteriores podrá evolucionar hacia:

```text
Incident Timeline
IOC
Affected Assets
Attack Vector
MITRE ATT&CK
Containment Actions
Lessons Learned
```

## Estrategia de escenarios

### Escenario 01 — Flagship

**Phishing Investigation / Incident Response**

Será el escenario principal para demostrar el producto.

Podrá incluir:

```text
correo sospechoso → endpoint → actividad sospechosa → PowerShell / ejecución → eventos SIEM → IOC → investigación → TP / FP → Case Report
```

Debe quedar especialmente cuidado.

### Escenario 02 — Secondary

Escenario técnicamente más sencillo que reutilice el mismo motor.

Por ejemplo:

**Suspicious SSH / Process Activity Investigation**


## Laboratorios

Las sesiones serán:

```text
INDIVIDUALES
TEMPORALES
AISLADAS
DESECHABLES
```

Cada usuario tendrá su propia `LabSession`.

Estados previstos:

```text
REQUESTED → QUEUED → PROVISIONING → READY → ACTIVE → EXPIRED → DESTROYING → DESTROYED
```

```text
FAILED
```

### Duración del laboratorio

Configuración inicial propuesta:

```text
Default:
60 minutos

Extension:
+30 minutos

Máximo:
120 minutos
```

La política deberá ser configurable.

Al llegar al tiempo máximo:

> **la sesión deberá destruirse, no simplemente apagarse.**

El siguiente usuario debe recibir un entorno nuevo y limpio.

### Concurrencia

El software debe soportar múltiples `LabSession` independientes.

La infraestructura física actual podrá limitar la cantidad simultánea.

Ejemplo:

```text
MAX_ACTIVE_LABS = 2
```

Los usuarios adicionales podrán permanecer:

```text
QUEUED
```

La limitación será de capacidad física, no del modelo de aplicación.


# Infraestructura del MVP

Durante esta fase:

```text
DEV
Ordenador de cada desarrollador

STAGING
Servidor Ubuntu disponible

SOURCE OF TRUTH
GitHub
```

Docker será utilizado para maximizar portabilidad.

## Stack tecnológico inicial

| Componente         | Tecnología                                            |
| ------------------ | ------------------------------------------------------- |
| Frontend           | React + Vite                                            |
| Backend            | FastAPI — monolito modular                              |
| ORM                | SQLAlchemy                                              |
| Migraciones        | Alembic                                                 |
| Base de datos      | PostgreSQL                                              |
| Cola/Cache         | Redis                                                   |
| Worker             | RQ                                                      |
| Contenedores       | Docker / Docker Compose                                 |
| Remote Labs        | Apache Guacamole                                        |
| Contenido          | GitHub + Markdown                                       |
| Observabilidad     | Grafana + Loki + Alloy                                  |
| SIEM escenario     | Spike técnico; preferencia Wazuh                        |
| Virtualización MVP | Docker primero, VMware cuando sea necesario             |
| Reverse Proxy      | **Todavía sí lo dejaría pendiente** entre Nginx/Traefik |


# Seguridad

El MVP deberá contemplar:

```text
2FA / TOTP
RBAC
aislamiento multiempresa
validación server-side
rate limiting
protección contra fuerza bruta
TLS
gestión de secretos
hardening servidor
seguridad Docker
logs
auditoría
principio de mínimo privilegio
```

```text
No secrets en frontend
No flags en frontend
No respuestas correctas en frontend
No lógica crítica exclusivamente cliente
```


## Auditoría y observabilidad

Toda acción relevante deberá generar eventos auditables.

Ejemplos:

```text
LOGIN_SUCCESS
LOGIN_FAILED
MFA_SUCCESS
USER_CREATED
USER_DISABLED
ROLE_CHANGED
GROUP_CREATED
ROADMAP_ASSIGNED
SCENARIO_STARTED
ALERT_OPENED
CASE_SUBMITTED
LAB_REQUESTED
LAB_STARTED
LAB_EXTENDED
LAB_DESTROYED
```

Además se centralizarán logs técnicos del sistema.

Objetivo del MVP:

> poder observar Project Guakamole desde un SIEM o plataforma de logging.

Esto hará que los propios alumnos tengan que desarrollar, securizar y monitorizar la plataforma.


# Dashboard B2B

El panel empresarial deberá ofrecer una visión mínima pero real del estado de la organización.

Ejemplo:

```text
Employees            24
Active Employees     19

Groups                 3
Assigned Roadmaps      1

Completed Scenarios   31

Average Progress      64%
```

También deberá poder visualizar progreso por:

```text
grupo
usuario
roadmap
```

No necesitamos un sistema avanzado de Business Intelligence durante el MVP.


# Scenario Editor

El MVP dispondrá de una primera versión administrativa que permita:

```text
crear escenario
editar metadata
añadir contenido
configurar duración
crear alertas
definir resultado esperado
asociar laboratorio
publicar
```

```text
GITHUB
────────────────
Markdown
documentación
playbooks
assets
scenario.yaml
configuración del lab
versionado


POSTGRESQL
────────────────
usuarios
empresas
roles
grupos
asignaciones
progreso
LabSessions
Case Reports
estados de alertas
auditoría
resultados
```


---

# Priorización del producto

Utilizaremos tres categorías.

### MUST

Sin esto no existe MVP:

```text
Multiempresa
Usuarios / Roles
Grupos
Roadmap
Escenarios
Alert Queue
TP / FP
Case Report
LabSession
Guacamole
Destrucción automática
Progreso
Dashboard empresa
Audit Log
Hardening
```

### SHOULD

Debe desarrollarse si el núcleo evoluciona correctamente:

```text
XP
mejoras visuales
colas de capacidad
métricas más avanzadas
Scenario Editor mejorado
mayor integración SIEM
```

### STRETCH

Solo cuando MUST + SHOULD prioritarios sean estables:

```text
IA
evaluación semántica del Case Report
gamificación avanzada
certificaciones
CRM / HubSpot
AWS
SSO empresarial
```

---
# ORGANIZACIÓN

## Equipo de desarrollo

Los cinco alumnos trabajarán como:

> **Guakamole Junior Engineering Team**

No trabajarán mediante ejercicios académicos aislados.

Trabajarán mediante tickets reales.

Responsabilidades iniciales previstas:

| Miembro    | Especialidad inicial                         |
| ---------- | -------------------------------------------- |
| **Sergi**  | Arquitectura backend / orquestación / Python |
| **Carlos** | Backend / PostgreSQL / testing               |
| **Jordi**  | Frontend / UX / integración                  |
| **Yuri**   | IAM / RBAC / usuarios                        |
| **Miguel** | DevOps / infraestructura / logging / QA      |

Estas son **especialidades principales, no silos**.

Todos deberán participar en:

```text
Git
Docker
seguridad
testing
code review
documentación
deploy
```

## Metodología de trabajo

Herramientas:

| Herramienta | Uso                                                 |
| ----------- | --------------------------------------------------- |
| **ClickUp** | Backlog, planificación, responsables y seguimiento. |
| **GitHub**  | Código, ramas, PR, Issues técnicos y documentación. |
| **Slack**   | Comunicación del equipo.                            |

Una tarea seguirá aproximadamente:

```text
ClickUp Ticket
      ↓
Branch Git
      ↓
Development
      ↓
Tests
      ↓
Pull Request
      ↓
Code Review
      ↓
Security / Functional validation
      ↓
Staging
      ↓
DONE
```


### Definition of Done

Una tarea **no está terminada porque funcione en el portátil del alumno**.

Para considerarse `DONE` deberá cumplir, cuando aplique:


- Funcionalidad implementada
- Tests realizados
- Seguridad revisada
- Código versionado
- Pull Request
- Code Review
- Documentación
- Desplegado / validado en staging
- Criterios de aceptación cumplidos


### MVP


1. Se crea / configura una empresa.
2. La empresa accede con su administrador.
3. Crea un grupo.
4. Invita usuarios.
5. Asigna un Manager.
6. Asigna un Roadmap.
7. Un empleado inicia sesión.
8. Consulta su Roadmap.
9. Inicia un escenario.
10. Project Guakamole crea su LabSession.
11. El usuario accede al SOC Simulator.
12. Consulta Alert Queue.
13. Investiga SIEM / VM.
14. Determina TP / FP.
15. Redacta Case Report.
16. Cierra el caso.
17. Se registra el resultado.
18. Se actualiza su progreso.
19. El Manager consulta ese resultado.
20. Al expirar el laboratorio, la infraestructura se destruye.
21. Las acciones relevantes pueden observarse en nuestros logs / SIEM.


### Objetivo comercial de la demo

La demo debe transmitir tres mensajes.

1. Existe producto: No es un PowerPoint ni un prototipo visual.
2. Existe una necesidad empresarial identificable: entrenar, asignar, medir y supervisar equipos SOC.
3. Existe una arquitectura sobre la que seguir invirtiendo: Los dos escenarios demostrarán que el motor puede reutilizarse.
