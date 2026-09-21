---
name: guakamole-backend-engineering
description: Use when working on Guakamole backend engineering in backend/: FastAPI, Python 3.12, uv, SOLID, PEP8, modular code, Pydantic, ORM, ruff, mypy strict and pytest.
---

# Guakamole Backend Engineering

Usa esta skill para cualquier tarea de ingenieria backend en Project Guakamole.

Reglas de ambito:

- Trabaja solo en `backend/`.
- La documentacion backend vive en `docs/backend/`.
- No modifiques `frontend/` salvo instruccion explicita del usuario.

Stack acordado:

- Python 3.12.
- FastAPI.
- uv.
- Pydantic.
- SQLAlchemy como ORM.
- Alembic para migraciones.
- ruff para lint y formato.
- mypy en modo strict.
- pytest para tests.

Reglas de codigo:

- Aplica SOLID.
- Respeta PEP8.
- Escribe codigo modular y reutilizable.
- Evita duplicacion; reutiliza con imports.
- Mantiene funciones y clases cortas, con una sola responsabilidad.
- Usa polimorfismo o clases abstractas cuando mejore claramente la estructura.
- Usa type hints completos.
- Evita `Any` y `# type: ignore` salvo justificacion concreta.
- Todo codigo funcional nuevo debe tener tests.
- No introduzcas secretos ni valores sensibles.

Comandos objetivo cuando el backend este configurado:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict .
uv run pytest
```
