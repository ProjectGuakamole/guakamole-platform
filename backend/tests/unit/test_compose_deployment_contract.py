import os
import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.test_unit


def test_base_compose_exposes_only_nginx_and_has_no_duplicate_database_url() -> None:
    content = Path("../docker-compose.yml").read_text(encoding="utf-8")

    backend = content.split("  backend:\n", maxsplit=1)[1].split("  frontend:\n")[0]
    postgres = content.split("  postgres:\n", maxsplit=1)[1].split("  backend:\n")[0]
    assert "ports:" not in backend
    assert "ports:" not in postgres
    assert content.count("DATABASE_URL: ${DOCKER_DATABASE_URL") == 1
    assert content.count("ports:") == 1


def test_local_override_contains_developer_only_service_ports() -> None:
    content = Path("../docker-compose.local.yml").read_text(encoding="utf-8")

    for service in ("postgres", "backend", "frontend"):
        assert f"  {service}:\n    ports:" in content
    assert "# Sólo desarrollo y CI local." in content
    assert "backend_internal:\n    internal: false" in content


def test_base_compose_keeps_backend_network_internal() -> None:
    content = Path("../docker-compose.yml").read_text(encoding="utf-8")

    assert "backend_internal:\n    internal: true" in content


def test_ci_generated_environments_include_docker_database_url() -> None:
    content = Path("../.github/workflows/backend-ci.yml").read_text(encoding="utf-8")
    generated_environment_commands = [
        line
        for line in content.splitlines()
        if "printf '%s\\n'" in line and "> .env.ci" in line
    ]
    app_database_url = (
        "postgresql+psycopg://guakamole_app:ci-app-password@postgres:5432/"
        "guakamole_test"
    )

    assert len(generated_environment_commands) == 2
    for command in generated_environment_commands:
        assert f"'DATABASE_URL={app_database_url}'" in command
        assert f"'DOCKER_DATABASE_URL={app_database_url}'" in command


def test_ci_verifies_the_current_migration_revision_is_at_head() -> None:
    content = Path("../.github/workflows/backend-ci.yml").read_text(encoding="utf-8")
    compose_override = (
        "COMPOSE='docker compose --env-file .env.ci -f docker-compose.yml "
        "-f docker-compose.local.yml'"
    )
    current_command = f"make docker-db-current ENV_FILE=.env.ci {compose_override}"
    check_command = f"make docker-db-check ENV_FILE=.env.ci {compose_override}"

    expected_sequence = (
        f"run: {current_command}\n\n"
        "      - name: Verificar migración actual en head\n"
        f"        run: {check_command}"
    )

    assert expected_sequence in content


def test_migrator_has_hardened_artifact_contract() -> None:
    content = Path("../docker-compose.yml").read_text(encoding="utf-8")
    migrator = content.split("  migrate:\n", maxsplit=1)[1].split("volumes:\n")[0]

    for expected in (
        'profiles: ["migration"]',
        "read_only: true",
        'user: "guakamole"',
        'cap_drop: ["ALL"]',
        "no-new-privileges:true",
    ):
        assert expected in migrator
    assert "ports:" not in migrator
    assert "\n      DATABASE_URL:" not in migrator
    required_variables = (
        "MIGRATION_DATABASE_URL",
        "MIGRATION_ALLOWED_HOSTS",
        "MIGRATION_ALLOWED_DATABASES",
        "MIGRATION_EXPECTED_DB_USER",
    )
    for variable in required_variables:
        assert f"${{{variable}:?{variable} es obligatoria}}" in migrator


def test_postgres_requires_dedicated_role_passwords() -> None:
    content = Path("../docker-compose.yml").read_text(encoding="utf-8")
    postgres = content.split("  postgres:\n", maxsplit=1)[1].split("  backend:\n")[0]

    for variable in ("MIGRATION_DB_PASSWORD", "APP_DB_PASSWORD"):
        assert f"${{{variable}:?{variable} es obligatoria}}" in postgres


def test_compose_template_leaves_required_values_blank() -> None:
    content = Path("tests/compose/.env.example").read_text(encoding="utf-8")

    required_variables = (
        "MIGRATION_DB_PASSWORD",
        "APP_DB_PASSWORD",
        "MIGRATION_DATABASE_URL",
        "MIGRATION_ALLOWED_HOSTS",
        "MIGRATION_ALLOWED_DATABASES",
        "MIGRATION_EXPECTED_DB_USER",
    )
    for variable in required_variables:
        assert f"{variable}=" in content


def test_compose_config_rejects_missing_migration_role_value(tmp_path: Path) -> None:
    docker = shutil.which("docker")
    if docker is None:
        pytest.skip(
            "Docker no está disponible para validar la interpolación de Compose."
        )

    environment_file = tmp_path / "compose.env"
    environment_file.write_text(
        "\n".join(
            (
                "POSTGRES_USER=test_admin",
                "POSTGRES_PASSWORD=test-password",
                "POSTGRES_DB=test_database",
                "APP_DB_PASSWORD=test-application-password",
                "MIGRATION_DATABASE_URL=postgresql+psycopg://test@postgres/test_database",
                "MIGRATION_ALLOWED_HOSTS=postgres",
                "MIGRATION_ALLOWED_DATABASES=test_database",
                "MIGRATION_EXPECTED_DB_USER=test_migrator",
                "APP_ENV=test",
                "DATABASE_URL=postgresql+psycopg://test@postgres/test_database",
                "DOCKER_DATABASE_URL=postgresql+psycopg://test@postgres/test_database",
                "JWT_SECRET_KEY=test-secret-not-for-production-with-safe-length",
                "JWT_ALGORITHM=HS256",
                "CORS_ALLOWED_ORIGINS=http://localhost:3000",
                "NGINX_PORT=8080",
            )
        ),
        encoding="utf-8",
    )
    environment = {"PATH": os.environ["PATH"]}
    result = subprocess.run(  # noqa: S603 - Docker ejecuta sólo `compose config`.
        [
            docker,
            "compose",
            "--env-file",
            str(environment_file),
            "-f",
            "../docker-compose.yml",
            "config",
            "--quiet",
        ],
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "MIGRATION_DB_PASSWORD es obligatoria" in result.stderr


def test_compose_images_are_pinned_by_digest() -> None:
    content = Path("../docker-compose.yml").read_text(encoding="utf-8")
    backend_dockerfile = Path("Dockerfile").read_text(encoding="utf-8")

    for image in ("postgres:15-alpine", "nginx:alpine"):
        assert f"image: {image}@sha256:" in content
    assert "FROM python:3.12-slim@sha256:" in backend_dockerfile


def test_role_provisioning_is_explicit_and_not_a_startup_side_effect() -> None:
    makefile = Path("../Makefile").read_text(encoding="utf-8")
    compose = Path("../docker-compose.yml").read_text(encoding="utf-8")

    assert "db-provision-roles:" in makefile
    provision_target = makefile.split("db-provision-roles:", maxsplit=1)[1].split(
        "db-upgrade:", maxsplit=1
    )[0]
    assert 'CONFIRM)" = "PROVISION_DATABASE_ROLES' in provision_target
    assert "ROLE_PROVISION_ALLOW_PROTECTED" in provision_target
    assert "up -d --wait postgres" in provision_target
    assert "exec -T" in provision_target
    assert "postgres sh /opt/guakamole-postgres/provision-roles.sh" in provision_target
    assert "sh infrastructure/postgres/provision-roles.sh" not in provision_target
    assert "printf '%s' \"$$ADMIN_DATABASE_URL\"" not in provision_target
    assert "ADMIN_DATABASE_URL debe apuntar al PostgreSQL local del contenedor" in (
        provision_target
    )
    for variable in (
        "ADMIN_DATABASE_URL",
        "ROLE_PROVISION_EXPECTED_ADMIN_DATABASE_URL",
        "MIGRATION_DB_PASSWORD",
        "APP_DB_PASSWORD",
        "ROLE_PROVISION_ALLOWED_DATABASES",
        "ROLE_PROVISION_EXPECTED_DB_USER",
    ):
        assert f"-e {variable}" in provision_target

    assert (
        "./infrastructure/postgres/provision-roles.sh:"
        "/opt/guakamole-postgres/provision-roles.sh:ro" in compose
    )
    assert (
        "./infrastructure/postgres/roles.sql:"
        "/opt/guakamole-postgres/roles.sql:ro" in compose
    )
    assert "provision-roles" not in Path("app/main.py").read_text(encoding="utf-8")
    provisioner = Path("../infrastructure/postgres/provision-roles.sh").read_text(
        encoding="utf-8"
    )
    assert "ROLE_PROVISION_EXPECTED_ADMIN_DATABASE_URL" in provisioner
    assert "ROLE_PROVISION_ALLOWED_DATABASES" in provisioner


def test_docker_operation_contract_distinguishes_manual_and_deployment_paths() -> None:
    makefile = Path("../Makefile").read_text(encoding="utf-8")

    docker_up = makefile.split("docker-up:", maxsplit=1)[1].split("docker-db-migrate:")[
        0
    ]
    deploy = makefile.split("docker-deploy:", maxsplit=1)[1].split("docker-down:")[0]
    assert "migration" not in docker_up
    assert "docker-db-migrate" in deploy
    assert "COMPOSE_BASE" in deploy


def test_migration_targets_rebuild_only_the_migrator_image() -> None:
    makefile = Path("../Makefile").read_text(encoding="utf-8")
    migration_targets = makefile.split("docker-db-migrate:", maxsplit=1)[1].split(
        "docker-deploy:", maxsplit=1
    )[0]

    assert migration_targets.count("run --build --rm migrate") == 3
    assert "backend" not in migration_targets
    assert "\n\t$(COMPOSE) up " not in migration_targets


def test_make_help_exposes_safe_docker_migration_contract_only() -> None:
    makefile = Path("../Makefile").read_text(encoding="utf-8")
    help_block = makefile.split("install:", maxsplit=1)[0]

    expected_commands = {
        "make docker-db-migrate     Aplica upgrade head con el migrador aislado.",
        (
            "make docker-db-current     Consulta la revisión Alembic con el "
            "migrador aislado."
        ),
        (
            "make docker-db-check       Verifica que la revisión Alembic actual "
            "coincide con head mediante el migrador aislado."
        ),
        (
            "make docker-deploy         Aplica migraciones y levanta el stack "
            "base de despliegue."
        ),
    }

    for command in expected_commands:
        assert command in help_block

    assert "make db-history" not in help_block
    assert "make db-downgrade" not in help_block
    assert "db-history está obsoleto" in makefile
    assert "db-downgrade está obsoleto" in makefile
    assert makefile.count("exit 1") >= 2
