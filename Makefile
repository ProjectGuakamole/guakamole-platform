.PHONY: help install setup backend-install backend-lint backend-format-check backend-mypy backend-pytest backend-test backend-check backend-run backend-seed backend-seed-clear docker-config docker-up docker-down docker-ps docker-logs postgres-up postgres-logs postgres-down psql db-upgrade db-current db-history db-downgrade health-check ready-check

BACKEND_DIR := backend
ENV_FILE ?= .env.example
ENV_FILE_PATH := $(if $(filter /%,$(ENV_FILE)),$(ENV_FILE),./$(ENV_FILE))
COMPOSE := docker compose --env-file $(ENV_FILE)
API_BASE_URL ?= http://localhost:8000
REVISION ?= -1

help: ## Muestra los comandos disponibles.
	@printf 'Comandos disponibles:\n'
	@printf '  ENV_FILE ?= .env.example\n'
	@printf '  REVISION ?= -1\n'
	@printf '  API_BASE_URL ?= http://localhost:8000\n'
	@printf '  make install               Instala/prepara dependencias del backend.\n'
	@printf '  make backend-test          Ejecuta lint, formato, mypy y pytest en backend.\n'
	@printf '  make backend-check         Consulta health y ready del backend levantado.\n'
	@printf '  make backend-run           Arranca FastAPI local con recarga.\n'
	@printf '  make backend-seed          DESTRUCTIVO: trunca sch_iam gestionado e inserta seed demo con $$(ENV_FILE).\n'
	@printf '  make backend-seed-clear    DESTRUCTIVO: trunca sch_iam gestionado sin reinsertar con $$(ENV_FILE).\n'
	@printf '  make docker-up             Levanta Docker Compose con build.\n'
	@printf '  make docker-down           Detiene y elimina servicios de Docker Compose.\n'
	@printf '  make docker-logs           Muestra logs de Docker Compose.\n'
	@printf '  make psql                  Abre psql dentro del contenedor PostgreSQL.\n'
	@printf '  make db-upgrade            Ejecuta Alembic upgrade head con $$(ENV_FILE).\n'
	@printf '  make db-current            Muestra revisión actual Alembic con $$(ENV_FILE).\n'
	@printf '  make db-history            Muestra histórico Alembic con $$(ENV_FILE).\n'
	@printf '  make db-downgrade          Ejecuta Alembic downgrade $$(REVISION) con $$(ENV_FILE).\n'

install: ## Instala/prepara dependencias del proyecto dentro del alcance backend.
	cd $(BACKEND_DIR) && uv sync

setup: install ## Prepara el entorno local sin crear ni modificar .env.
	@printf 'Setup completado. Revisa .env.example y crea .env manualmente solo si lo necesitas.\n'

backend-install: install ## Alias oculto para instalar dependencias del backend.

backend-lint: ## Ejecuta lint del backend.
	cd $(BACKEND_DIR) && uv run ruff check .

backend-format-check: ## Comprueba formato del backend.
	cd $(BACKEND_DIR) && uv run ruff format --check .

backend-mypy: ## Ejecuta mypy strict del backend.
	cd $(BACKEND_DIR) && uv run mypy --strict .

backend-pytest: ## Ejecuta pytest del backend.
	cd $(BACKEND_DIR) && uv run pytest

backend-test: backend-lint backend-format-check backend-mypy backend-pytest ## Ejecuta todas las comprobaciones de calidad backend.

backend-check: health-check ready-check ## Comprueba el servicio backend levantado.

backend-run: ## Arranca el servidor FastAPI local en primer plano.
	cd $(BACKEND_DIR) && uv run uvicorn app.main:app --reload

backend-seed: ## DESTRUCTIVO: trunca tablas IAM gestionadas e inserta datos demo usando $(ENV_FILE).
	set -a; . $(ENV_FILE_PATH); set +a; cd $(BACKEND_DIR) && uv run python scripts/seed_demo_iam.py --yes

backend-seed-clear: ## DESTRUCTIVO: trunca tablas IAM gestionadas sin reinsertar usando $(ENV_FILE).
	set -a; . $(ENV_FILE_PATH); set +a; cd $(BACKEND_DIR) && uv run python scripts/seed_demo_iam.py --clear --yes

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

psql: ## Abre psql dentro del contenedor PostgreSQL.
	$(COMPOSE) up -d postgres
	$(COMPOSE) exec postgres sh -c 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

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
