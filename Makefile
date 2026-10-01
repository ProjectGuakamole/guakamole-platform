.PHONY: help install setup backend-install backend-lint backend-format-check backend-mypy backend-test backend-check backend-run docker-config docker-up docker-down docker-ps docker-logs postgres-up postgres-logs postgres-down health-check ready-check

BACKEND_DIR := backend
COMPOSE := docker compose --env-file .env.example
API_BASE_URL ?= http://localhost:8000

help: ## Muestra los comandos disponibles.
	@printf 'Comandos disponibles:\n'
	@printf '  make install               Instala/prepara dependencias del backend.\n'
	@printf '  make setup                 Prepara el entorno local sin modificar .env.\n'
	@printf '  make backend-install       Instala dependencias del backend con uv sync.\n'
	@printf '  make backend-lint          Ejecuta ruff check en backend.\n'
	@printf '  make backend-format-check  Comprueba formato ruff en backend.\n'
	@printf '  make backend-mypy          Ejecuta mypy strict en backend.\n'
	@printf '  make backend-test          Ejecuta pytest en backend.\n'
	@printf '  make backend-check         Ejecuta lint, formato, mypy y tests de backend.\n'
	@printf '  make backend-run           Arranca FastAPI local con recarga.\n'
	@printf '  make docker-config         Renderiza Docker Compose con .env.example.\n'
	@printf '  make docker-up             Levanta Docker Compose con build.\n'
	@printf '  make docker-down           Detiene y elimina servicios de Docker Compose.\n'
	@printf '  make docker-ps             Lista servicios de Docker Compose.\n'
	@printf '  make docker-logs           Muestra logs de Docker Compose.\n'
	@printf '  make postgres-up           Levanta solo PostgreSQL.\n'
	@printf '  make postgres-logs         Muestra logs de PostgreSQL.\n'
	@printf '  make postgres-down         Detiene PostgreSQL.\n'
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

docker-config: ## Renderiza la configuración Compose usando .env.example.
	$(COMPOSE) config

docker-up: ## Levanta el entorno local con build usando .env.example.
	$(COMPOSE) up --build -d

docker-down: ## Detiene y elimina el entorno local usando .env.example.
	$(COMPOSE) down

docker-ps: ## Lista servicios Compose usando .env.example.
	$(COMPOSE) ps

docker-logs: ## Muestra logs Compose usando .env.example.
	$(COMPOSE) logs

postgres-up: ## Levanta solo el servicio PostgreSQL usando .env.example.
	$(COMPOSE) up -d postgres

postgres-logs: ## Muestra logs del servicio PostgreSQL usando .env.example.
	$(COMPOSE) logs postgres

postgres-down: ## Detiene solo el servicio PostgreSQL usando .env.example.
	$(COMPOSE) stop postgres

health-check: ## Consulta el endpoint de liveness sin asumir que el servidor esté levantado.
	curl -i $(API_BASE_URL)/api/health

ready-check: ## Consulta el endpoint de readiness; puede devolver 503 por diseño conservador.
	curl -i $(API_BASE_URL)/api/ready
