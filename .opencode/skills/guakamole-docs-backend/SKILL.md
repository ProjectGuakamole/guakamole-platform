---
name: guakamole-docs-backend
description: Use when documenting backend branch, commit or PR changes in docs/backend using Spanish documentation and branch-name markdown files.
---

# Guakamole Backend Documentation

Usa esta skill para documentar cambios backend por branch, commit o PR.

Ubicacion:

- La documentacion backend vive en `docs/backend/`.

Nombre del archivo:

- Usa el nombre de la branch.
- Sustituye `/` por `-`.
- Ejemplo: `feature/GUAK-020-healthcheck` -> `docs/backend/feature-GUAK-020-healthcheck.md`.

Idioma:

- Castellano de Espana.

Estructura obligatoria:

```markdown
# <nombre de la branch>

## Objetivo

## Cambios realizados

## Justificacion tecnica

## Decisiones tomadas

## Tests ejecutados

## Riesgos o deuda tecnica

## Relacion con el backend
```

Reglas:

- No inventes tests no ejecutados.
- No documentes cambios fuera del alcance backend salvo que afecten directamente al backend.
- Explica el porque de las decisiones, no solo la lista de archivos.
- Mantiene trazabilidad para commits y PRs.
