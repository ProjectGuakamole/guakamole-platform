# backend/project-structure

## Objetivo

Crear la estructura base modular del backend FastAPI para separar el punto de entrada de la aplicación, routers versionados, configuración, modelos, schemas, servicios y capa de base de datos.

## Cambios realizados

- Se ha movido el punto de entrada desde `backend/main.py` a `backend/app/main.py`.
- Se ha creado el paquete `app/` con subpaquetes `api`, `core`, `models`, `schemas`, `services` y `db`.
- Se ha creado `app/api/v1/router.py` como router principal versionado.
- Se ha creado `app/api/v1/health.py` con el endpoint `GET /api/v1/health`.
- Se han actualizado los tests para validar el endpoint de salud mediante `TestClient`.
- Se ha generado `requirements.txt` desde `uv.lock` para compatibilidad con Docker.
- Se ha creado `backend/Dockerfile` para ejecutar la API con Uvicorn.
- Se han añadido caches de herramientas Python al `.gitignore`.

## Justificación técnica

La estructura modular facilita que el backend crezca sin mezclar responsabilidades. El versionado bajo `app/api/v1/` permite evolucionar la API sin romper contratos futuros con el frontend.

Mantener `pyproject.toml` y `uv.lock` como fuente principal de dependencias conserva la configuración acordada con `uv`, mientras que `requirements.txt` permite construir imágenes Docker de forma sencilla.

## Decisiones tomadas

- Exponer la aplicación FastAPI como `app.main:app`.
- Usar `create_app()` para facilitar futuros tests y configuraciones.
- Crear un endpoint inicial de salud en `/api/v1/health`.
- Mantener `requirements.txt` generado desde `uv.lock`.
- Usar un usuario no root dentro del contenedor Docker.

## Tests ejecutados

Desde `backend/` se han ejecutado correctamente:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict .
uv run pytest
```

Resultado: todos los checks pasan. `pytest` muestra dos warnings de dependencias internas de FastAPI/Starlette TestClient, sin fallo de test.

## Riesgos o deuda tecnica

- La configuración de Docker todavía no está integrada en `docker-compose.yml`.
- La conexión real con PostgreSQL queda pendiente para una branch posterior.
- Alembic todavía no está inicializado.

## Relación con el backend

Esta estructura establece la base del backend FastAPI sobre la que se implementarán autenticación, base de datos, módulos de dominio, SOC Simulator y futuros endpoints versionados.
