---
name: guakamole-testing-quality
description: Use when adding or reviewing backend tests, pytest coverage, ruff, mypy strict, QA checks, edge cases and security validation.
---

# Guakamole Testing And Quality

Usa esta skill para crear o revisar tests y calidad del backend.

Checks objetivo:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict .
uv run pytest
```

Reglas de testing:

- Todo codigo funcional nuevo debe tener tests.
- Cubre casos positivos y negativos.
- Cubre edge cases relevantes.
- En seguridad, incluye pruebas de autorizacion y aislamiento multi-tenant.
- Si hay endpoints FastAPI, usa tests HTTP con cliente apropiado.
- Si hay base de datos, evita tests dependientes de estado compartido.
- Los tests deben ser legibles y mantenibles.

Reglas de revision:

- Si falta test para codigo funcional nuevo, el cambio queda bloqueado.
- Si `mypy --strict` falla, el cambio queda bloqueado.
- Si `ruff` falla, el cambio queda bloqueado.
- Si hay riesgo de fuga cross-tenant, el cambio queda bloqueado.
- Si se modifica `frontend/` sin autorizacion explicita, el cambio queda bloqueado.
