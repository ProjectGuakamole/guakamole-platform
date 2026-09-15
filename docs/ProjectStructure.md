# Project Breakdown Structure — MVP v0.1

**Proyecto:** Project Guakamole
**Duración:** 125 h × 5 personas = **625 horas brutas**
**Objetivo:** MVP funcional, securizado y demostrable
**Metodología:** desarrollo incremental mediante vertical slices


```text
Capacidad total                 625 h

Trabajo planificable          ~455 h
Reserva / contingencia        ~170 h
```

# E00 — Project Foundation & Engineering Rules

**Objetivo:** que el proyecto pueda empezar de forma ordenada y todos trabajen de la misma manera.

**Resultado esperado:** los cinco alumnos pueden clonar los repositorios, comprender cómo se trabaja y comenzar tickets sin improvisar procesos.

| Elemento              | Alcance                |
| --------------------- | ---------------------- |
| GitHub Organization   | Configuración inicial  |
| `guakamole-platform`  | Creación               |
| `guakamole-scenarios` | Creación               |
| Protección `main`     | Obligatoria            |
| PR Template           | Configurado            |
| CODEOWNERS            | Configurado            |
| Branch naming         | Definido               |
| ClickUp ↔ GitHub      | Convención establecida |
| Slack                 | Canales definidos      |
| README inicial        | Disponible             |
| `.env.example`        | Disponible             |
| ADRs                  | Documentados           |

**Responsabilidad inicial:** Sergi + Miguel
**Estimación presupuestaria:** ~20 h
**Prioridad:** MUST

# E01 — Platform Skeleton & Developer Environment
# E02 — Identity, Authentication & Multi-Tenant Security
# E03 — B2B Organization & Team Management
# E04 — Content, Scenario & Roadmap Engine
# E05 — SOC Simulator Core
# E06 — Lab Engine & Remote Access
# E07 — Progress, Results & B2B Dashboard
# E08 — Audit, Observability & Security Hardening
# E09 — Flagship Scenario
# E10 — Secondary Scenario
# E11 — Integration, Security Validation & MVP Release


## Distribución presupuestaria inicial

| Epic                         | Horas objetivo |
| ---------------------------- | -------------: |
| E00 Foundation               |             20 |
| E01 Platform Skeleton        |             30 |
| E02 IAM / Multi-Tenant       |             50 |
| E03 B2B / Groups             |             35 |
| E04 Content / Roadmaps       |             45 |
| E05 SOC Simulator Core       |             45 |
| E06 Lab Engine               |             70 |
| E07 Progress / Dashboard     |             35 |
| E08 Observability / Security |             45 |
| E09 Flagship Scenario        |             35 |
| E10 Secondary Scenario       |             15 |
| E11 Integration / Release    |             30 |
| **Planificado**              |      **455 h** |
| **Reserva**                  |      **170 h** |
| **Total disponible**         |      **625 h** |
