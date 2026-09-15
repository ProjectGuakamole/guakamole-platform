# Architecture MVP v0.1 — Project Guakamole

```text
                    PROJECT GUAKAMOLE

            ┌──────────────────────────┐
            │      CONTROL PLANE       │
            │                          │
            │ Empresas                 │
            │ Usuarios / RBAC          │
            │ Roadmaps                 │
            │ Escenarios               │
            │ Alertas                  │
            │ Case Reports             │
            │ Progreso                 │
            │ Auditoría                │
            └────────────┬─────────────┘
                         │
                    crea / destruye
                         │
                         ▼
            ┌──────────────────────────┐
            │        LAB PLANE         │
            │                          │
            │ LabSession               │
            │ Docker / VMware          │
            │ Redes aisladas           │
            │ Analyst VM               │
            │ SIEM / Evidencias        │
            │ Guacamole                │
            └──────────────────────────┘
```

Esta separación es probablemente **la decisión arquitectónica más importante del proyecto**.

El Control Plane gestiona el producto.

El Lab Plane ejecuta infraestructura potencialmente peligrosa, temporal y desechable.

## Arquitectura general inicial

```text
                           INTERNET
                               │
                               ▼
                            NGINX
                      Reverse Proxy / TLS
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
            ▼                  ▼                  ▼
        FRONTEND            FASTAPI          GUACAMOLE
      React + Vite       Modular Monolith        │
                               │                 │
                    ┌──────────┼──────────┐      │
                    │          │          │      │
                    ▼          ▼          ▼      │
               PostgreSQL    Redis      GitHub   │
                    │          │                 │
                    │          ▼                 │
                    │          RQ                │
                    │          │                 │
                    │          ▼                 │
                    │      LAB WORKER            │
                    │          │                 │
                    │          ▼                 │
                    │     LAB ENGINE             │
                    │          │                 │
                    │          ▼                 │
                    │      LabProvider            │
                    │          │                 │
                    │     ┌────┴────┐            │
                    │     ▼         ▼            │
                    │   Docker    VMware         │
                    │    MVP      opcional       │
                    │     │                       │
                    │     ▼                       │
                    │  LAB SESSION ◄──────────────┘
                    │
                    ▼
                Audit Events
                    │
                    ▼
                  Alloy
                    │
                    ▼
                   Loki
                    │
                    ▼
                 Grafana
```

## Nginx 

```text
Internet
   │
   ▼
Nginx
   │
   ├── /           → React
   ├── /api/       → FastAPI
   ├── /guacamole/ → Guacamole
   └── TLS
```

Y además Nginx nos permite enseñar:

```text
TLS
headers
rate limiting
reverse proxy
logs
hardening
```

lo cual tiene mucho valor formativo.

**ADR-005 — Reverse Proxy: Nginx.**

## FastAPI

```text
guakamole-api/

app/
│
├── auth/
├── organizations/
├── users/
├── groups/
├── roadmaps/
├── scenarios/
├── soc/
│   ├── alerts/
│   └── cases/
├── labs/
├── progress/
├── audit/
├── integrations/
└── core/
```

## PostgreSQL

Inicialmente **un único servidor PostgreSQL**, pero no necesariamente una única base de datos.

```text
PostgreSQL
│
├── guakamole
│
│   usuarios
│   empresas
│   grupos
│   progreso
│   labs
│   case reports
│   ...
│
└── guacamole
    │
    usuarios/conexiones necesarias
    por Apache Guacamole
```

Esto reduce muchísimo el consumo de recursos.

### GitHub y PostgreSQL

Queda como principio oficial:

> **GitHub = Content Source of Truth**

> **PostgreSQL = Operational Source of Truth**

Ejemplo:

```text
GitHub
│
└── scenarios/
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

Mientras PostgreSQL guarda:

```text
Organization ACME
Ana pertenece a SOC-L1
SOC-L1 tiene Roadmap A
Ana inició escenario phishing-001
LabSession = 123
Alert 1035 = FALSE POSITIVE
Case Report enviado
Resultado = 87%
```

## Scenario Manifest

```text
scenario.yaml
```

Cada escenario tendrá un manifiesto.


```yaml
id: phishing-001

name: Phishing Investigation

difficulty: beginner

duration:
  default: 60
  maximum: 120
  extension: 30

skills:
  - phishing-analysis
  - log-analysis
  - incident-response

lab:
  provider: docker
  template: phishing-lab

features:
  siem: true
  analyst_vm: true
```

### El Lab Engine

FastAPI **no debe crear directamente contenedores**. La App no tiene que saber dónde se está ejecutando la máquina.

Debe decir:

```text
Lab Engine
   │
   ▼
LabProvider
```

Y este ofrecerá conceptualmente:

```python
create()
start()
status()
extend()
destroy()
```

Durante el MVP:

```text
LabProvider
     │
     ▼
DockerProvider
```

En escenarios que realmente lo necesiten:

```text
LabProvider
     │
     ▼
VMwareProvider
```

### Una idea importante para los escenarios

Por ahora NO necesitamos ejecutar todo el ataque en tiempo real.

Para el escenario de Phishing podemos haber generado previamente y cargarlos como dataset del escenario.

```text
Sysmon
Windows Event Logs
PowerShell Logs
Network Logs
correo .eml
IOC
hash
procesos
```

El usuario seguirá teniendo que hacer:

```text
correlación
investigación
búsqueda
análisis
```

### LabSession

Cuando Ana pulse:

```text
INICIAR ESCENARIO
```

FastAPI no esperará 30 segundos a que Docker haga cosas.

Creará:

```text
LabSession

id: 1842
user: Ana
scenario: phishing-001
status: REQUESTED
```

y enviará un trabajo a Redis:

```text
provision_lab(1842)
```

El flujo:

```text
FASTAPI
   │
   ▼
Redis
   │
   ▼
RQ Worker
   │
   ▼
LabEngine
   │
   ▼
DockerProvider
```

FastAPI puede responder inmediatamente:

```json
{
  "session_id": 1842,
  "status": "REQUESTED"
}
```

El frontend irá consultando:

```text
REQUESTED

QUEUED

PROVISIONING

READY
```

Hasta que aparezca:

```text
[ ABRIR SOC SIMULATOR ]
```


### Lab Reaper

Algo tiene que garantizar: pasan 120 minutos → laboratorio destruido.

Y esto no puede depender:

* del navegador;
* de que el alumno siga conectado;
* de JavaScript;
* de que pulse salir.

Crearemos conceptualmente otro pequeño proceso:

```text
LAB REAPER
```

Cada cierto intervalo:

```text
buscar:

LabSession
status = ACTIVE
expires_at <= NOW()
```

Entonces:

```text
enqueue destroy_lab()
```

y el worker ejecuta:

```text
ACTIVE
   ↓
EXPIRED
   ↓
DESTROYING
   ↓
DESTROYED
```

### Aislamiento de cada laboratorio

Cada LabSession debe tener su propia red.

Por ejemplo:

```text
lab_1842_network

├── analyst_1842
├── target_1842
└── service_1842
```

Mientras otra:

```text
lab_1927_network

├── analyst_1927
├── target_1927
└── service_1927
```

No deben poder comunicarse.

Y el alumno **no debería acceder directamente a esas IPs desde Internet**.

La entrada será:

```text
Browser
   │
   ▼
Guacamole
   │
   ▼
Lab
```

### Guacamole no será el Lab Engine

- Guacamole = REMOTE ACCESS GATEWAY
- Guacamole ≠ virtualización

Por tanto:

```text
Lab Engine | crea recurso
       ↓
Guacamole Adapter | crea/configura conexión
       ↓
Alumno | accede
```

Interfaz conceptual:

```text
RemoteAccessProvider
        │
        ▼
GuacamoleProvider
```

### SPIKE

La **integración dinámica con Guacamole**.

```text
FastAPI
   │
   ▼
crear lab
   │
   ▼
registrar/acceder conexión Guacamole
   │
   ▼
usuario ve su máquina
```

> **SPIKE — Provisionar dinámicamente un laboratorio Docker y hacerlo accesible mediante Guacamole.**

Timebox probablemente:

```text
4-8 horas
```

## Observabilidad

Nuestros servicios escribirán preferentemente logs estructurados:

```text
FastAPI
Docker
Nginx
Guacamole
Worker
Linux
```

Entonces:

```text
logs
 │
 ▼
Alloy
 │
 ▼
Loki
 │
 ▼
Grafana
```

Dashboards de logs

```text
Authentication

LOGIN_SUCCESS     123
LOGIN_FAILED       17
MFA_FAILED          4
```

```text
Labs

ACTIVE              2
QUEUED              3
FAILED              1
```

### Audit Trail ≠ Logs técnicos

El `AuditEvent`:

```text
- actor: ana@acme.com
- organization: ACME
- action: CASE_SUBMITTED
- scenario: phishing-001
- case: 1035
- timestamp: ...
```

Arquitectura del AuditEnvent

```text
AuditEvent
       │
       ├── PostgreSQL
       │
       └── structured log
                 │
                 ▼
                Loki
```

## SIEM del alumno

Vamos a realizar el spike:

```text
Wazuh
```

y medir:

```text
RAM
CPU
almacenamiento
tiempo de arranque
complejidad
UX
```

Si funciona:

```text
SOC Simulator
│
├── Alert Queue Guakamole
├── Wazuh
└── Analyst VM
```

Si no:

```text
SOC Simulator
│
├── Alert Queue
├── Evidence / Log Explorer
└── Analyst VM
```

# STAGING


```text
                    UBUNTU STAGING

┌───────────────────────────────────────────┐
│                                           │
│ Docker Compose                            │
│                                           │
│ Nginx                                     │
│ Frontend                                  │
│ FastAPI                                   │
│ PostgreSQL                                │
│ Redis                                     │
│ RQ Worker                                 │
│ Guacamole                                 │
│ guacd                                     │
│ Grafana                                   │
│ Loki                                      │
│ Alloy                                     │
│                                           │
│ + Labs dinámicos                          │
│                                           │
└───────────────────────────────────────────┘
```

Las piezas pesadas se activarán solamente cuando sean necesarias.

Especialmente:

```text
Wazuh
VMware VM
```


## Arquitectura de red del servidor

Quiero que lleguemos posteriormente a algo parecido a:

```text
                     INTERNET
                         │
                         ▼
                    NGINX
                         │
                FRONT NETWORK
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
          Frontend                 FastAPI
                                     │
                              BACKEND NETWORK
                                     │
                     ┌───────────────┼──────────┐
                     ▼               ▼          ▼
                 PostgreSQL        Redis       Worker
                                                   │
                                                   ▼
                                              LAB NETWORK
                                                   │
                                            ┌──────┴──────┐
                                            ▼             ▼
                                        Guacamole       Labs
```


# Flujo completo


```text
EMPRESA
   │
   ▼
React
   │
   ▼
FastAPI
   │
   ▼
PostgreSQL
Organization / Groups / Roadmap

────────────────────────────────

ALUMNO
   │
   ▼
START SCENARIO
   │
   ▼
FastAPI
   │
   ├── verifica RBAC
   ├── verifica Organization
   ├── verifica assignment
   └── crea LabSession
             │
             ▼
           Redis
             │
             ▼
          RQ Worker
             │
             ▼
          LabEngine
             │
             ▼
      DockerLabProvider
             │
             ▼
        Lab creado
             │
             ▼
        Guacamole
             │
             ▼
          Alumno
             │
             ▼
       investigación
             │
             ▼
        Case Report
             │
             ▼
          FastAPI
             │
       ┌─────┴─────┐
       ▼           ▼
  PostgreSQL    AuditEvent
                    │
                    ▼
                   Loki

────────────────────────────────

expires_at
    │
    ▼
Lab Reaper
    │
    ▼
RQ
    │
    ▼
destroy()
```