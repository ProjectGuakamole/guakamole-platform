.PHONY: help install setup backend-install backend-lint backend-format-check backend-mypy backend-quality backend-pytest backend-test-unit backend-test-db backend-test-security backend-test backend-check backend-run backend-seed backend-bootstrap backend-seed-demo backend-seed-clear backend-rebaseline-iam docker-config docker-up docker-down docker-ps docker-logs docker-db-migrate docker-db-current docker-db-check docker-deploy postgres-up postgres-logs postgres-down psql db-provision-roles db-upgrade db-current db-history db-downgrade health-check ready-check

BACKEND_DIR := backend
ENV_FILE ?= .env
ENV_FILE_PATH := $(if $(filter /%,$(ENV_FILE)),$(ENV_FILE),./$(ENV_FILE))
COMPOSE_BASE := docker compose --env-file $(ENV_FILE) -f docker-compose.yml
COMPOSE_LOCAL := $(COMPOSE_BASE) -f docker-compose.local.yml
COMPOSE ?= $(COMPOSE_LOCAL)
API_BASE_URL ?= http://localhost:8000

help: ## Muestra los comandos disponibles.
	@printf 'Comandos disponibles:\n'
	@printf '  ENV_FILE ?= .env (configuración local activa, no versionada)\n'
	@printf '  API_BASE_URL ?= http://localhost:8000\n'
	@printf '  make install               Instala/prepara dependencias del backend.\n'
	@printf '  make backend-quality       Ejecuta lint, formato y mypy en backend.\n'
	@printf '  make backend-test-unit     Ejecuta tests unitarios y de arquitectura en backend.\n'
	@printf '  make backend-test-db       Reconstruye la DB de pruebas y ejecuta tests de base de datos e integración.\n'
	@printf '  make backend-test-security Ejecuta tests de seguridad sin dependencia de base de datos en backend.\n'
	@printf '  make backend-test          Ejecuta quality y grupos de tests backend alineados con CI.\n'
	@printf '  make backend-check         Consulta health y ready del backend levantado.\n'
	@printf '  make backend-run           Arranca FastAPI local con recarga.\n'
	@printf '  make backend-bootstrap     Inserta catálogos IAM canónicos en un destino dedicado.\n'
	@printf '  make backend-seed-demo CONFIRM=SEED_DEMO_IAM     Reemplaza sólo la demo; ejecuta antes backend-bootstrap.\n'
	@printf '  make backend-seed-clear CONFIRM=CLEAR_DEMO_IAM   Elimina sólo la demo (también requiere --yes interno).\n'
	@printf '  make backend-rebaseline-iam CONFIRM=REBASELINE_IAM Reconstruye IAM en test/desarrollo.\n'
	@printf '  make docker-up             Levanta el stack manual de desarrollo (puede no estar listo sin migrar).\n'
	@printf '  make docker-db-migrate     Aplica upgrade head con el migrador aislado.\n'
	@printf '  make docker-db-current     Consulta la revisión Alembic con el migrador aislado.\n'
	@printf '  make docker-db-check       Verifica que la revisión Alembic actual coincide con head mediante el migrador aislado.\n'
	@printf '  make docker-deploy         Aplica migraciones y levanta el stack base de despliegue.\n'
	@printf '  make db-provision-roles CONFIRM=PROVISION_DATABASE_ROLES Provisiona roles en un volumen existente.\n'
	@printf '  make docker-down           Detiene y elimina servicios de Docker Compose.\n'
	@printf '  make docker-logs           Muestra logs de Docker Compose.\n'
	@printf '  make psql                  Abre psql dentro del contenedor PostgreSQL.\n'
	@printf '  make db-upgrade            Ejecuta Alembic upgrade head con $$(ENV_FILE).\n'
	@printf '  make db-current            Muestra revisión actual Alembic con $$(ENV_FILE).\n'

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

backend-quality: backend-lint backend-format-check backend-mypy ## Ejecuta lint, formato y mypy del backend.

backend-pytest: ## Ejecuta pytest del backend.
	cd $(BACKEND_DIR) && uv run pytest

backend-test-unit: ## Ejecuta tests unitarios y de arquitectura del backend.
	cd $(BACKEND_DIR) && uv run pytest -m "test_unit or architecture"

backend-test-db: ## Ejecuta tests de base de datos e integración del backend.
	@test -f "$(ENV_FILE_PATH)" || { printf 'Falta ENV_FILE.\n' >&2; exit 1; }
	@set -a; . "$(ENV_FILE_PATH)"; set +a; test -n "$$TEST_DATABASE_URL" || { printf 'TEST_DATABASE_URL es obligatoria.\n' >&2; exit 1; }; cd $(BACKEND_DIR) && env -u JWT_SECRET -u DATABASE_URL APP_ENV=test TEST_DATABASE_URL="$$TEST_DATABASE_URL" uv run python -c 'from app.core.test_database import get_test_database_url; import os; get_test_database_url(os.environ)'
	@set -a; . "$(ENV_FILE_PATH)"; set +a; cd $(BACKEND_DIR) && env -u JWT_SECRET -u DATABASE_URL APP_ENV=test TEST_DATABASE_URL="$$TEST_DATABASE_URL" uv run python -m scripts.rebaseline_iam --confirm REBASELINE_IAM
	@set -a; . "$(ENV_FILE_PATH)"; set +a; cd $(BACKEND_DIR) && env -u JWT_SECRET -u DATABASE_URL APP_ENV=test DATABASE_URL="$$TEST_DATABASE_URL" TEST_DATABASE_URL="$$TEST_DATABASE_URL" uv run pytest -m "db or integration"

backend-test-security: ## Ejecuta tests de seguridad sin dependencia de base de datos del backend.
	cd $(BACKEND_DIR) && uv run pytest -m "security and not db"

backend-test: backend-quality backend-test-unit backend-test-db backend-test-security ## Ejecuta quality y grupos de tests backend alineados con CI.

backend-check: health-check ready-check ## Comprueba el servicio backend levantado.

backend-run: ## Arranca el servidor FastAPI local en primer plano.
	@test -f "$(ENV_FILE_PATH)" || (printf 'Falta ENV_FILE; crea .env desde .env.example.\n' >&2; exit 1)
	@set -a; . "$(ENV_FILE_PATH)"; set +a; unset JWT_SECRET; cd $(BACKEND_DIR) && uv run uvicorn app.main:app --reload

backend-seed: ## Obsoleto: use backend-bootstrap y backend-seed-demo.
	@printf 'backend-seed está obsoleto; usa backend-bootstrap y backend-seed-demo.\n' >&2; exit 1

backend-bootstrap:
	@test -f "$(ENV_FILE_PATH)" || { printf 'Falta ENV_FILE.\n' >&2; exit 1; }
	@set -a; . "$(ENV_FILE_PATH)"; set +a; cd $(BACKEND_DIR) && env -u DATABASE_URL -u JWT_SECRET uv run python -m scripts.bootstrap_iam

backend-seed-demo:
	@test -f "$(ENV_FILE_PATH)" || { printf 'Falta ENV_FILE.\n' >&2; exit 1; }
	@test "$(CONFIRM)" = "SEED_DEMO_IAM" || { printf 'Confirma con CONFIRM=SEED_DEMO_IAM.\n' >&2; exit 1; }
	@set -a; . "$(ENV_FILE_PATH)"; set +a; cd $(BACKEND_DIR) && env -u DATABASE_URL -u JWT_SECRET uv run python -m scripts.seed_demo_iam --yes

backend-seed-clear: ## Elimina únicamente las claves demo gestionadas usando $(ENV_FILE).
	@test -f "$(ENV_FILE_PATH)" || (printf 'Falta ENV_FILE.\n' >&2; exit 1)
	@test "$(CONFIRM)" = "CLEAR_DEMO_IAM" || { printf 'Confirma con CONFIRM=CLEAR_DEMO_IAM.\n' >&2; exit 1; }
	@set -a; . "$(ENV_FILE_PATH)"; set +a; cd $(BACKEND_DIR) && env -u DATABASE_URL -u JWT_SECRET uv run python -m scripts.seed_demo_iam --clear --yes

backend-rebaseline-iam:
	@test -f "$(ENV_FILE_PATH)" || { printf 'Falta ENV_FILE.\n' >&2; exit 1; }
	@test "$(CONFIRM)" = "REBASELINE_IAM" || { printf 'Confirma con CONFIRM=REBASELINE_IAM.\n' >&2; exit 1; }
	@set -a; . "$(ENV_FILE_PATH)"; set +a; cd $(BACKEND_DIR) && env -u DATABASE_URL -u JWT_SECRET uv run python -m scripts.rebaseline_iam --confirm REBASELINE_IAM

docker-config: ## Renderiza la configuración Compose local usando $(ENV_FILE).
	@test -f "$(ENV_FILE_PATH)" || { printf 'Falta ENV_FILE.\n' >&2; exit 1; }
	$(COMPOSE) config --quiet

docker-up: ## Levanta el stack manual de desarrollo local; no ejecuta migraciones.
	@test -f "$(ENV_FILE_PATH)" || { printf 'Falta ENV_FILE.\n' >&2; exit 1; }
	$(COMPOSE) up --build -d

docker-db-migrate: ## Ejecuta upgrade head en el servicio migrador aislado.
	@test -f "$(ENV_FILE_PATH)" || { printf 'Falta ENV_FILE.\n' >&2; exit 1; }
	$(COMPOSE) --profile migration run --build --rm migrate

docker-db-current: ## Consulta el estado Alembic mediante el servicio aislado.
	@test -f "$(ENV_FILE_PATH)" || { printf 'Falta ENV_FILE.\n' >&2; exit 1; }
	$(COMPOSE) --profile migration run --build --rm migrate python -m scripts.migrate current

docker-db-check: ## Verifica que la revisión Alembic actual coincide con head mediante el servicio aislado.
	@test -f "$(ENV_FILE_PATH)" || { printf 'Falta ENV_FILE.\n' >&2; exit 1; }
	$(COMPOSE) --profile migration run --build --rm migrate python -m scripts.migrate check

docker-deploy: ## Despliega base: migra explícitamente antes de iniciar servicios normales.
	@$(MAKE) docker-db-migrate ENV_FILE="$(ENV_FILE)" COMPOSE='$(COMPOSE_BASE)'
	$(COMPOSE_BASE) up --build -d

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

db-provision-roles: ## Provisiona explícitamente roles/privilegios en una base existente.
	@test -f "$(ENV_FILE_PATH)" || { printf 'Falta ENV_FILE.\n' >&2; exit 1; }
	@test "$(CONFIRM)" = "PROVISION_DATABASE_ROLES" || { printf 'Confirma con CONFIRM=PROVISION_DATABASE_ROLES.\n' >&2; exit 1; }
	@set -a; . "$(ENV_FILE_PATH)"; set +a; case "$$APP_ENV" in staging|production) test "$$ROLE_PROVISION_ALLOW_PROTECTED" = "yes" || { printf 'Staging/producción requieren ROLE_PROVISION_ALLOW_PROTECTED=yes.\n' >&2; exit 1; };; esac; case "$$ADMIN_DATABASE_URL" in postgresql+psycopg://*) ADMIN_DATABASE_URL=postgresql://$${ADMIN_DATABASE_URL#postgresql+psycopg://};; postgresql://*) ;; *) printf 'ADMIN_DATABASE_URL debe usar el esquema PostgreSQL.\n' >&2; exit 1;; esac; case "$$ROLE_PROVISION_EXPECTED_ADMIN_DATABASE_URL" in postgresql+psycopg://*) ROLE_PROVISION_EXPECTED_ADMIN_DATABASE_URL=postgresql://$${ROLE_PROVISION_EXPECTED_ADMIN_DATABASE_URL#postgresql+psycopg://};; postgresql://*) ;; *) printf 'La URL esperada debe usar el esquema PostgreSQL.\n' >&2; exit 1;; esac; case "$$ADMIN_DATABASE_URL" in postgresql://*@localhost/*|postgresql://*@localhost:*/*|postgresql://*@127.0.0.1/*|postgresql://*@127.0.0.1:*/*) ;; *) printf 'ADMIN_DATABASE_URL debe apuntar al PostgreSQL local del contenedor.\n' >&2; exit 1;; esac; $(COMPOSE) up -d --wait postgres; $(COMPOSE) exec -T -e ADMIN_DATABASE_URL -e ROLE_PROVISION_EXPECTED_ADMIN_DATABASE_URL -e MIGRATION_DB_PASSWORD -e APP_DB_PASSWORD -e ROLE_PROVISION_ALLOWED_DATABASES -e ROLE_PROVISION_EXPECTED_DB_USER postgres sh /opt/guakamole-postgres/provision-roles.sh

db-upgrade: ## Ejecuta migraciones Alembic hasta head usando $(ENV_FILE).
	@test -f "$(ENV_FILE_PATH)" || { printf 'Falta ENV_FILE.\n' >&2; exit 1; }
	@set -a; . "$(ENV_FILE_PATH)"; set +a; cd $(BACKEND_DIR) && env -u DATABASE_URL -u JWT_SECRET uv run python -m scripts.migrate upgrade head

db-current: ## Muestra la revisión Alembic actual usando $(ENV_FILE).
	@test -f "$(ENV_FILE_PATH)" || { printf 'Falta ENV_FILE.\n' >&2; exit 1; }
	@set -a; . "$(ENV_FILE_PATH)"; set +a; cd $(BACKEND_DIR) && env -u DATABASE_URL -u JWT_SECRET uv run python -m scripts.migrate current

db-history: ## Obsoleto y no operativo: el migrador seguro no admite histórico.
	@printf 'db-history está obsoleto: el migrador seguro no admite histórico. Usa docker-db-current o docker-db-check.\n' >&2; exit 1

db-downgrade: ## Obsoleto y no operativo: no existe una política Docker de downgrade.
	@printf 'db-downgrade está obsoleto: el migrador seguro rechaza downgrades y no hay política Docker de downgrade.\n' >&2; exit 1

health-check: ## Consulta el endpoint de liveness sin asumir que el servidor esté levantado.
	curl -i $(API_BASE_URL)/api/health

ready-check: ## Consulta el endpoint de readiness; puede devolver 503 por diseño conservador.
	curl -i $(API_BASE_URL)/api/ready
