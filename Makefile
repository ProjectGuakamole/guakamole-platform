.PHONY: help install setup backend-install backend-lint backend-format-check backend-mypy backend-test backend-check backend-run docker-config docker-up docker-down docker-ps docker-logs postgres-up postgres-logs postgres-down db-upgrade db-current db-history db-downgrade health-check ready-check

BACKEND_DIR := backend
ENV_FILE ?= .env.example
ENV_FILE_PATH := $(if $(filter /%,$(ENV_FILE)),$(ENV_FILE),./$(ENV_FILE))
COMPOSE := docker compose --env-file $(ENV_FILE)
API_BASE_URL ?= http://localhost:8000
REVISION ?= -1

help: ## Muestra los comandos disponibles.
	@printf 'Comandos disponibles:\n'
	@printf '  ENV_FILE ?= .env.example  Archivo de entorno para Docker Compose y Alembic.\n'
	@printf '  Ejemplos: make docker-up ENV_FILE=.env | make db-upgrade ENV_FILE=.env\n'
	@printf '  make install               Instala/prepara dependencias del backend.\n'
	@printf '  make setup                 Prepara el entorno local sin modificar .env.\n'
	@printf '  make backend-install       Instala dependencias del backend con uv sync.\n'
	@printf '  make backend-lint          Ejecuta ruff check en backend.\n'
	@printf '  make backend-format-check  Comprueba formato ruff en backend.\n'
	@printf '  make backend-mypy          Ejecuta mypy strict en backend.\n'
	@printf '  make backend-test          Ejecuta pytest en backend.\n'
	@printf '  make backend-check         Ejecuta lint, formato, mypy y tests de backend.\n'
	@printf '  make backend-run           Arranca FastAPI local con recarga.\n'
	@printf '  make docker-config         Renderiza Docker Compose con $$(ENV_FILE).\n'
	@printf '  make docker-up             Levanta Docker Compose con build.\n'
	@printf '  make docker-down           Detiene y elimina servicios de Docker Compose.\n'
	@printf '  make docker-ps             Lista servicios de Docker Compose.\n'
	@printf '  make docker-logs           Muestra logs de Docker Compose.\n'
	@printf '  make postgres-up           Levanta solo PostgreSQL.\n'
	@printf '  make postgres-logs         Muestra logs de PostgreSQL.\n'
	@printf '  make postgres-down         Detiene PostgreSQL.\n'
	@printf '  make db-upgrade            Ejecuta Alembic upgrade head con $$(ENV_FILE).\n'
	@printf '  make db-current            Muestra revisión actual Alembic con $$(ENV_FILE).\n'
	@printf '  make db-history            Muestra histórico Alembic con $$(ENV_FILE).\n'
	@printf '  make db-downgrade          Ejecuta Alembic downgrade $$(REVISION) con $$(ENV_FILE).\n'
	@printf '  make health-check          Consulta $(API_BASE_URL)/api/health.\n'
	@printf '  make ready-check           Consulta $(API_BASE_URL)/api/ready.\n'

install: backend-install ## Instala/prepara dependencias del proyecto dentro del alcance backend.

setup: install ## Prepara el entorno local sin crear ni modificar .env.
	@printf 'Setup completado. Revisa .env.example y crea .env manualmente solo si lo necesitas.\n'

backend-install: ## Instala dependencias del backend usando uv.
	cd $(BACKEND_DIR) && uv sync

backend-lint: ## Ejecuta lint del backend.
	cd $(BACKEND_DIR) && uv run ruff check .

backend-format-check: ## Comprueba formato del backend.
	cd $(BACKEND_DIR) && uv run ruff format --check .

backend-mypy: ## Ejecuta mypy strict del backend.
	cd $(BACKEND_DIR) && uv run mypy --strict .

backend-test: ## Ejecuta tests del backend.
	cd $(BACKEND_DIR) && uv run pytest

backend-check: backend-lint backend-format-check backend-mypy backend-test ## Ejecuta todas las comprobaciones de calidad backend.

backend-run: ## Arranca el servidor FastAPI local en primer plano.
	cd $(BACKEND_DIR) && uv run uvicorn app.main:app --reload

docker-config: ## Renderiza la configuración Compose usando $(ENV_FILE).
	$(COMPOSE) config

docker-up: ## Levanta el entorno local con build usando $(ENV_FILE).
	$(COMPOSE) up --build -d

docker-down: ## Detiene y elimina el entorno local usando $(ENV_FILE).
	$(COMPOSE) down

docker-ps: ## Lista servicios Compose usando $(ENV_FILE).
	$(COMPOSE) ps

docker-logs: ## Muestra logs Compose usando $(ENV_FILE).
	$(COMPOSE) logs

postgres-up: ## Levanta solo el servicio PostgreSQL usando $(ENV_FILE).
	$(COMPOSE) up -d postgres

postgres-logs: ## Muestra logs del servicio PostgreSQL usando $(ENV_FILE).
	$(COMPOSE) logs postgres

postgres-down: ## Detiene solo el servicio PostgreSQL usando $(ENV_FILE).
	$(COMPOSE) stop postgres

db-upgrade: ## Ejecuta migraciones Alembic hasta head usando $(ENV_FILE).
	set -a; . $(ENV_FILE_PATH); set +a; cd $(BACKEND_DIR) && uv run alembic upgrade head

db-current: ## Muestra la revisión Alembic actual usando $(ENV_FILE).
	set -a; . $(ENV_FILE_PATH); set +a; cd $(BACKEND_DIR) && uv run alembic current

db-history: ## Muestra el histórico de migraciones Alembic usando $(ENV_FILE).
	set -a; . $(ENV_FILE_PATH); set +a; cd $(BACKEND_DIR) && uv run alembic history

db-downgrade: ## Revierte una revisión Alembic usando $(ENV_FILE).
	set -a; . $(ENV_FILE_PATH); set +a; cd $(BACKEND_DIR) && uv run alembic downgrade $(REVISION)

health-check: ## Consulta el endpoint de liveness sin asumir que el servidor esté levantado.
	curl -i $(API_BASE_URL)/api/health

ready-check: ## Consulta el endpoint de readiness; puede devolver 503 por diseño conservador.
	curl -i $(API_BASE_URL)/api/ready
