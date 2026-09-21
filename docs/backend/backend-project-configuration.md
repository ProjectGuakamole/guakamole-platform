# backend/project-configuration

## Objetivo

Configurar la base inicial de trabajo del backend y la configuracion de OpenCode para que el equipo pueda desarrollar sobre `backend/` con agentes, skills y controles de calidad consistentes.

## Cambios realizados

- Se ha creado `opencode.json` con instrucciones del proyecto y ruta de skills.
- Se han creado agentes de OpenCode para implementacion Python, QA, arquitectura API, documentacion y orquestacion.
- Se han creado skills de backend, seguridad API, testing/calidad y documentacion backend.
- Se ha creado la carpeta `docs/backend/` para documentacion tecnica backend por branch.
- Se ha configurado `backend/pyproject.toml` con dependencias runtime y grupo `dev`.
- Se ha configurado `ruff`, `mypy --strict` y `pytest`.
- Se ha generado `backend/uv.lock`.
- Se ha configurado GitHub Actions en `.github/workflows/backend-ci.yml` para validar el backend.
- Se ha anadido un test minimo inicial para validar la configuracion de pytest.

## Justificacion tecnica

El backend necesita una base reproducible antes de implementar funcionalidad. La configuracion centralizada en `pyproject.toml` permite mantener dependencias, linting, tipado y tests bajo el mismo punto de control.

El workflow de GitHub Actions se ubica en la raiz del repositorio, como requiere GitHub, pero ejecuta todos los comandos desde `backend/` para no interferir con el frontend.

Los agentes y skills de OpenCode quedan versionados para que el equipo comparta las mismas reglas de trabajo, calidad, seguridad y documentacion.

## Decisiones tomadas

- Usar FastAPI como framework backend.
- Usar Python 3.12.
- Usar `uv` para entorno y dependencias.
- Usar `ruff` para lint y comprobacion de formato.
- Usar `mypy --strict` para tipado estricto.
- Usar `pytest` para tests.
- Mantener el trabajo backend limitado a `backend/` y la documentacion tecnica backend a `docs/backend/`.
- No modificar `frontend/` desde tareas backend.
- Nombrar la documentacion de branch sustituyendo `/` por `-`.

## Tests ejecutados

Desde `backend/` se han ejecutado correctamente:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict .
uv run pytest
```

Resultado: todos los checks pasan.

## Riesgos o deuda tecnica

- El backend aun no implementa una aplicacion FastAPI real; `main.py` sigue siendo el punto de entrada minimo generado inicialmente.
- La configuracion de Alembic esta pendiente de inicializar cuando se cree la capa de base de datos.
- La integracion real con PostgreSQL todavia no esta implementada.
- La proteccion de ramas debe configurarse en GitHub.

## Relacion con el backend

Esta branch establece la base de calidad, dependencias, agentes y CI para el desarrollo posterior del backend de Project Guakamole.
