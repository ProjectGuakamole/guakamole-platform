# Repository & Git Strategy v0.1 (PENDING)

**Estado propuesto:** APPROVED tras validación
**Objetivo:** permitir que cinco personas trabajen simultáneamente con trazabilidad ClickUp → GitHub → Staging, evitando conflictos y protegiendo `main`.

## 1. Dos repositorios principales

Usaría solamente **dos repositorios durante el MVP**:

```text
GitHub Organization
│
├── guakamole-platform
│
└── guakamole-scenarios
```

### `guakamole-platform`

Será un **monorepo técnico**:

```text
guakamole-platform/
│
├── frontend/
│   └── React + Vite
│
├── backend/
│   └── FastAPI
│
├── infrastructure/
│   ├── docker/
│   ├── nginx/
│   ├── observability/
│   └── scripts/
│
├── tests/
│   ├── integration/
│   └── security/
│
├── docs/
│   ├── architecture/
│   ├── adr/
│   ├── api/
│   └── operations/
│
├── docker-compose.yml
├── .env.example
└── README.md
```

Aquí vivirán juntos React, FastAPI, Docker y la infraestructura porque en este MVP **cambian conjuntamente**.

Por ejemplo:

> Carlos crea `/api/scenarios`, Jordi adapta React y Miguel modifica Docker.

Con un monorepo pueden coordinarlo en un único PR si tiene sentido.

---

## 2. `guakamole-scenarios`

Separaría el contenido porque ya hemos decidido:

> **GitHub = Content Source of Truth.**

```text
guakamole-scenarios/
│
├── scenarios/
│   │
│   ├── phishing-001/
│   │   ├── scenario.yaml
│   │   ├── README.md
│   │   ├── documentation/
│   │   ├── playbooks/
│   │   ├── assets/
│   │   ├── datasets/
│   │   └── lab/
│   │
│   └── ssh-001/
│
├── schemas/
│   └── scenario.schema.json
│
├── templates/
│   └── scenario-template/
│
└── README.md
```

Esto proporciona una frontera muy limpia:

```text
PLATFORM
código

SCENARIOS
contenido
```

Y posteriormente el Scenario Editor podrá hablar directamente con el repositorio de escenarios.

---

# 3. Importante: escenario público ≠ repositorio público

Esto debemos explicárselo a los alumnos.

Cuando el Domain Model dice:

```text
PLATFORM_PUBLIC
```

significa:

> visible para todas las empresas dentro de Guakamole.

No significa:

> público en github.com.

Durante el MVP yo mantendría **ambos repositorios privados**.

Especialmente porque los escenarios pueden contener datasets, configuración de laboratorio y detalles técnicos que no queremos exponer todavía.

---

# 4. ¿Dónde van las soluciones?

Nunca aquí:

```yaml
expected_answer: TRUE_POSITIVE
flag: GUAK{something}
```

dentro de un repositorio accesible a alumnos/usuarios finales.

El repositorio puede contener:

```yaml
id: phishing-001
name: Phishing Investigation
difficulty: beginner
```

pero:

```text
EvaluationRule
Correct answers
Secret flags
Sensitive validation logic
```

permanecen en el backend/PostgreSQL o almacenamiento privado equivalente.

---

# 5. No usaría GitFlow

Para este proyecto **no quiero**:

```text
main
develop
release
hotfix
feature
```

Nos añade burocracia innecesaria.

Utilizaremos una variante sencilla de **GitHub Flow / trunk-based development**:

```text
main
 │
 ├── feature/...
 ├── fix/...
 ├── spike/...
 └── chore/...
```

Todas las ramas son cortas.

Todas terminan en Pull Request hacia:

```text
main
```

---

# 6. `main` siempre debe ser estable

Regla:

> **Nadie hace `git push` directamente a `main`.**

Ni Sergi.

Ni tú.

Ni yo recomendaría hacerlo aunque algo sea urgente.

Flujo:

```text
ClickUp
   │
   ▼
Branch
   │
   ▼
Development
   │
   ▼
Pull Request
   │
   ▼
CI
   │
   ▼
Review
   │
   ▼
Merge
   │
   ▼
main
   │
   ▼
STAGING
```

`main` representa:

> código potencialmente desplegable.

---

# 7. Protección de `main`

En GitHub activaría:

```text
Require pull request
✓

Require approvals
✓

Require status checks
✓

Require conversation resolution
✓

Block force pushes
✓

Block branch deletion
✓
```

Y si GitHub permite configurarlo en vuestro plan:

```text
Require branch to be up to date
```

también.

---

# 8. Convención de tickets

Todos los tickets tendrán ID:

```text
GUAK-001
GUAK-002
GUAK-003
...
```

ClickUp será el dueño de esa numeración.

Ejemplo:

```text
GUAK-042
Implementar aislamiento multi-tenant
```

---

# 9. Convención de ramas

Siempre incluirán el ticket.

```text
feature/GUAK-042-tenant-isolation

feature/GUAK-073-alert-queue

fix/GUAK-081-lab-timeout

spike/GUAK-012-guacamole-dynamic

chore/GUAK-025-ci-pipeline
```

Tipos iniciales:

| Prefijo    | Uso                             |
| ---------- | ------------------------------- |
| `feature/` | Nueva funcionalidad             |
| `fix/`     | Corrección                      |
| `spike/`   | Investigación técnica timeboxed |
| `chore/`   | Infraestructura/mantenimiento   |
| `docs/`    | Documentación                   |

No necesitamos veinte categorías.

---

# 10. Flujo completo de una tarea

Ejemplo real:

### ClickUp

```text
GUAK-042
Crear aislamiento de Organization
```

Yuri comienza la tarea.

Crea:

```bash
git checkout -b feature/GUAK-042-tenant-isolation
```

Trabaja y realiza commits.

Después abre:

```text
Pull Request

[GUAK-042] Implement tenant isolation
```

Carlos revisa.

CI ejecuta tests.

Se corrigen comentarios.

Carlos aprueba.

Merge.

ClickUp:

```text
DONE
```

---

# 11. Commits

No complicaría demasiado los mensajes, pero sí exigiría que sean descriptivos.

Correctos:

```text
feat(auth): add TOTP enrollment

fix(labs): prevent expired lab extension

test(tenant): add cross-organization access tests
```

Podemos incluir el ticket:

```text
GUAK-042 feat(tenant): enforce organization scope
```

Lo importante es que nunca tengamos:

```text
update

cambios

funciona

final

final2

arreglo definitivo
```

🙂

---

# 12. Merge strategy

Usaría:

> **Squash and Merge**

Una rama puede tener:

```text
fix typo
tests
oops
fix tests
final
```

pero `main` recibe solamente:

```text
GUAK-042 Enforce organization isolation
```

Resultado:

```text
main

GUAK-040 Add organization model
GUAK-041 Add memberships
GUAK-042 Enforce tenant isolation
GUAK-043 Add RBAC
```

Mucho más fácil de auditar.

---

# 13. Pull Request obligatorio

Todo cambio necesita PR.

Incluso:

```text
Docker
Nginx
Markdown
Scenario
CI
Documentation importante
```

Esto es especialmente útil en un curso de ciberseguridad porque les fuerza a practicar revisión.

---

# 14. PR Template

Crearía `.github/pull_request_template.md`.

Algo así:

```markdown
## Ticket

GUAK-XXX

## Qué cambia

Descripción breve.

## Cómo probarlo

1.
2.
3.

## Criterios de aceptación

- [ ] ...
- [ ] ...

## Tests

- [ ] Unit
- [ ] Integration
- [ ] Manual

## Seguridad

- [ ] Autorización revisada
- [ ] No se añaden secretos
- [ ] Validación de inputs revisada
- [ ] No afecta aislamiento multi-tenant

## Documentación

- [ ] Actualizada
- [ ] No aplica
```

Esto les obliga a pensar antes de pedir una revisión.

---

# 15. Code Review

Aquí quiero una norma bastante fuerte:

> **El desarrollador no puede aprobar su propio trabajo.**

Mínimo:

```text
1 reviewer
```

Para componentes críticos:

```text
2 revisiones
```

Por ejemplo:

```text
AUTH
RBAC
TENANT ISOLATION
LAB ENGINE
SECRETS
NETWORKING
```

No necesariamente dos personas para cada CSS.

---

# 16. Especialista ≠ propietario exclusivo

Podemos definir propietarios principales:

```text
Backend / Architecture
Sergi

Backend / Database
Carlos

Frontend
Jordi

IAM / RBAC
Yuri

DevOps
Miguel
```

Pero eso significa:

> reviewer natural / referente.

No:

> solo esa persona puede tocarlo.

---

# 17. CODEOWNERS

Implementaría:

```text
.github/CODEOWNERS
```

Conceptualmente:

```text
/backend/app/auth/           Yuri + Sergi
/backend/app/labs/           Sergi
/backend/migrations/         Carlos
/frontend/                   Jordi
/infrastructure/             Miguel + Sergi
/docs/architecture/          Sergi
```

No hace falta automatizar toda la gobernanza el primer día, pero es una práctica muy buena.

---

# 18. Reviews cruzadas

Quiero deliberadamente algo como:

```text
Autor       Reviewer habitual

Sergi   → Carlos / Yuri
Carlos  → Sergi
Jordi   → Yuri / Carlos
Yuri    → Carlos / Sergi
Miguel  → Sergi / Jordi
```

Y los security reviews pueden rotar.

Esto evita los silos.

---

# 19. Draft Pull Requests

Los usaría mucho.

Ejemplo:

Sergi lleva dos horas trabajando en:

```text
LabProvider
```

No necesita esperar a terminar.

Abre:

```text
Draft PR
```

Entonces Carlos puede ver hacia dónde va antes de que Sergi haya escrito 800 líneas.

Esto reduce muchísimo los problemas de integración.

---

# 20. Tamaño de PR

Regla orientativa:

> **PR pequeño > PR gigantesco**

Ideal:

```text
100-400 líneas relevantes
```

No lo convertiría en prohibición matemática.

Pero un PR con:

```text
5.000 líneas
```

normalmente significa que el ticket estaba mal dividido.

---

# 21. CI mínimo

Cada PR a `main` debería lanzar automáticamente:

```text
BACKEND
├── lint
├── tests
└── migration validation

FRONTEND
├── lint
├── build
└── tests básicos

SECURITY
├── secret scan
└── dependency checks

SCENARIOS
└── schema validation
```

No tenemos que implantar todo durante la primera hora.

Pero ese es el objetivo.

---

# 22. Especialmente importante: Secret Scanning

Quiero prevenir commits como:

```text
POSTGRES_PASSWORD=Admin123!

JWT_SECRET=abc123

GITHUB_TOKEN=...

AWS_ACCESS_KEY=...
```

El repositorio tendrá:

```text
.env.example
```

pero **jamás**:

```text
.env
```

`.gitignore` desde el minuto 1.

---

# 23. `.env.example`

Sí contendrá:

```text
POSTGRES_HOST=
POSTGRES_PORT=
POSTGRES_DB=

REDIS_HOST=

JWT_ALGORITHM=
```

Pero no credenciales reales.

De forma que un alumno pueda hacer:

```bash
cp .env.example .env
```

y completar su entorno local.

---

# 24. GitHub Secrets

Cuando montemos CI/CD:

```text
STAGING_SSH_KEY
STAGING_HOST
...
```

irán en GitHub Actions Secrets/Environments.

Nunca en código.

---

# 25. Staging deployment

Propongo:

```text
PR
 ↓
Merge main
 ↓
GitHub Actions
 ↓
STAGING
```

Inicialmente podemos incluso hacer deployment manual.

Pero quiero terminar las prácticas con:

```text
main
  │
  ▼
automatic staging deployment
```

si el tiempo lo permite.

---

# 26. No necesitamos production branch

Durante las prácticas:

```text
DEV
local

MAIN
stable

STAGING
servidor
```

No existe todavía una producción comercial real.

Por tanto no necesitamos:

```text
production
prod
stable
release
```

Cuando llegue ese momento podremos introducir releases.

---

# 27. Releases

Sí utilizaría tags para hitos.

Por ejemplo:

```text
v0.1.0-alpha
v0.1.0-beta
v0.1.0-mvp
```

Podríamos tener:

```text
v0.1.0-alpha
Golden Path parcial

v0.1.0-beta
Golden Path completo

v0.1.0-mvp
Demo final
```

Eso nos dará hitos técnicos muy visibles.

---

# 28. Repository de escenarios: mismo flujo

No quiero que alguien edite directamente:

```text
phishing-001/scenario.yaml
```

en `main`.

También:

```text
ClickUp
   ↓
branch
   ↓
scenario change
   ↓
PR
   ↓
validation
   ↓
review
   ↓
merge
```

Ejemplo:

```text
content/GUAK-140-phishing-timeline
```

o, para no añadir otro prefijo:

```text
feature/GUAK-140-phishing-timeline
```

---

# 29. Validación automática de escenarios

Aquí tenemos una oportunidad fantástica.

Nuestro:

```text
scenario.yaml
```

tendrá un schema.

Entonces CI puede validar:

```text
scenario ID
name
duration
difficulty
lab provider
assets
rutas
```

Ejemplo:

```text
phishing-001
      │
      ▼
scenario.yaml
      │
      ▼
JSON Schema validation
      │
      ├── VALID
      │
      └── INVALID → PR FAIL
```

Así ningún Scenario Editor podrá publicar accidentalmente un manifiesto roto.

---

# 30. Escenario versionado mediante Git

Cuando hacemos:

```text
merge
```

obtenemos:

```text
commit SHA
```

Por ejemplo:

```text
8a7fb92
```

Entonces `ScenarioVersion` puede guardar:

```text
scenario:
phishing-001

version:
1

git_commit_sha:
8a7fb92
```

Así podemos saber exactamente:

> qué contenido vio Ana cuando realizó su assessment.

Esto es especialmente valioso en selección.

---

# 31. No borrar histórico

Otra regla:

> **No reescribir historia de contenido publicado.**

Si:

```text
phishing-001 v1
```

ya ha sido utilizado en un assessment y encontramos un error:

no hacemos desaparecer el hecho de que existió.

Creamos:

```text
v2
```

Esto conecta perfectamente con nuestro Domain Model.

---

# 32. Documentación como código

Quiero que:

```text
Architecture
ADR
Runbooks
Security
Setup
```

también estén en Git.

Ejemplo:

```text
docs/
├── architecture/
│   ├── architecture-v0.1.md
│   └── domain-model-v0.1.md
│
├── adr/
│   ├── ADR-001-fastapi.md
│   ├── ADR-002-docker-provider.md
│   └── ...
│
├── security/
│   ├── threat-model.md
│   └── hardening.md
│
└── operations/
    ├── staging.md
    └── incident-response.md
```

Esto convierte el repositorio en la documentación técnica real del producto.

---

# 33. README obligatorio

`guakamole-platform/README.md` debe permitir que un desarrollador nuevo haga:

```text
clone
   ↓
configurar .env
   ↓
docker compose up
   ↓
Project Guakamole funcionando
```

Si necesita una explicación oral de tres horas para levantarlo:

> tenemos deuda técnica.

---

# 34. Política de ramas caducadas

Una rama debería vivir:

```text
horas
o
pocos días
```

no:

```text
3 semanas
```

Cuanto más vive una rama:

```text
más conflictos
más divergencia
más integración tardía
```

Para 125 horas quiero integración continua.

---

# 35. WIP limit

Aunque tendremos cinco personas, no quiero:

```text
cada alumno
5 tickets abiertos
```

Yo limitaría:

> **1 tarea principal `IN PROGRESS` por persona.**

Puede haber un pequeño ticket bloqueado/side-task, pero la regla general:

```text
START
↓
FINISH
↓
NEXT
```

Esto será importante cuando construyamos ClickUp.

---

# 36. Estados ClickUp y GitHub

Más adelante lo configuraría aproximadamente:

```text
BACKLOG
   ↓
READY
   ↓
IN PROGRESS
   ↓
IN REVIEW
   ↓
READY FOR STAGING
   ↓
DONE
```

Relación:

```text
Branch creada
→ IN PROGRESS

PR abierta
→ IN REVIEW

PR merged
→ READY FOR STAGING

Validación staging
→ DONE
```

Puede automatizarse después, pero primero que entiendan el proceso.

---

# 37. Bugs

Un bug encontrado después de merge no se arregla silenciosamente.

Se crea:

```text
GUAK-218
Fix cross-tenant group access
```

y:

```text
fix/GUAK-218-cross-tenant-groups
```

Eso mantiene trazabilidad.

---

# 38. Security bug

Si encontramos algo serio, por ejemplo:

```text
Usuario ACME puede leer CyberCorp
```

la prioridad cambia inmediatamente.

Tendrá algo como:

```text
SECURITY
IMPACT 5
PRIORITY CRITICAL
```

Luego definiremos esto en nuestra matriz de priorización de ClickUp.

---

# 39. SPIKES también dejan evidencia

Un spike no significa:

> Sergi prueba cosas durante seis horas y después nos cuenta lo que recuerda.

Ejemplo:

```text
GUAK-015
SPIKE — Dynamic Guacamole Provisioning
```

Resultado obligatorio:

```text
docs/spikes/GUAK-015-guacamole.md
```

con:

```text
Pregunta
Experimento
Resultado
Problemas
Recomendación
Decisión
```

Así el aprendizaje permanece dentro de la empresa.

---

# 40. Estructura final

Nuestra estrategia queda:

```text
GitHub Organization
│
│
├── guakamole-platform
│   │
│   ├── frontend
│   ├── backend
│   ├── infrastructure
│   ├── tests
│   └── docs
│
└── guakamole-scenarios
    │
    ├── scenarios
    ├── templates
    └── schemas
```

Flujo:

```text
CLICKUP
   │
   ▼
GUAK-XXX
   │
   ▼
FEATURE BRANCH
   │
   ▼
DEVELOPMENT
   │
   ▼
DRAFT PR
   │
   ▼
TESTS + CI
   │
   ▼
CODE REVIEW
   │
   ▼
SQUASH MERGE
   │
   ▼
MAIN
   │
   ▼
STAGING
   │
   ▼
VALIDATION
   │
   ▼
DONE
```

---

# Repository & Git Strategy — decisiones congeladas

| Decisión                   | Estado |
| -------------------------- | ------ |
| GitHub Organization        | ✅      |
| 2 repos MVP                | ✅      |
| Platform monorepo          | ✅      |
| Scenarios separado         | ✅      |
| Repos privados             | ✅      |
| GitHub Flow                | ✅      |
| No `develop`               | ✅      |
| `main` protegido           | ✅      |
| Ticket en branch           | ✅      |
| PR obligatorio             | ✅      |
| Review obligatorio         | ✅      |
| Squash merge               | ✅      |
| CI por PR                  | ✅      |
| Secrets fuera de Git       | ✅      |
| Scenario schema validation | ✅      |
| Docs as Code               | ✅      |
| Tags para releases         | ✅      |
| Short-lived branches       | ✅      |
| Spikes documentados        | ✅      |
