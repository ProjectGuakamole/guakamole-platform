"""Contrato operativo seguro del target de pruebas de PostgreSQL."""

import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.test_unit

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _write_fake_uv(directory: Path) -> Path:
    """Crea un sustituto de ``uv`` que registra su contrato sin ejecutar comandos."""

    executable = directory / "uv"
    executable.write_text(
        "#!/bin/sh\n"
        'printf \'%s\\t%s\\t%s\\t%s\\n\' "$*" "${APP_ENV:-}" '
        '"${DATABASE_URL:-}" "${TEST_DATABASE_URL:-}" >> "$CALL_LOG"\n'
        'case "$*" in *"python -c"*) case "${TEST_DATABASE_URL:-}" in '
        '*"@remote/"*) exit 1 ;; esac ;; esac\n'
        'case "$*" in *"scripts.rebaseline_iam"*) '
        'if [ "${FAIL_REBASELINE:-}" = "1" ]; then exit 1; fi ;; esac\n',
        encoding="utf-8",
    )
    executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
    return executable


def test_backend_test_db_rebaselines_test_database_before_pytest(
    tmp_path: Path,
) -> None:
    """El target valida y reconstruye sólo la URL de pruebas antes de pytest."""

    environment_file = tmp_path / "test.env"
    call_log = tmp_path / "uv-calls.log"
    test_url = "postgresql+psycopg://test:test@localhost/guakamole_test"
    environment_file.write_text(
        "DATABASE_URL=postgresql+psycopg://prod:prod@remote/guakamole\n"
        f"TEST_DATABASE_URL={test_url}\n",
        encoding="utf-8",
    )
    _write_fake_uv(tmp_path)
    environment = {
        "PATH": f"{tmp_path}{os.pathsep}{os.environ['PATH']}",
        "CALL_LOG": str(call_log),
    }

    make_executable = shutil.which("make")
    assert make_executable is not None
    result = subprocess.run(  # noqa: S603 - test fixture controls make and inputs.
        [make_executable, "backend-test-db", f"ENV_FILE={environment_file}"],
        cwd=PROJECT_ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    calls = [
        line.split("\t") for line in call_log.read_text(encoding="utf-8").splitlines()
    ]
    assert [call[0] for call in calls] == [
        (
            "run python -c from app.core.test_database import "
            "get_test_database_url; import os; get_test_database_url(os.environ)"
        ),
        "run python -m scripts.rebaseline_iam --confirm REBASELINE_IAM",
        "run pytest -m db or integration",
    ]
    assert all(call[1] == "test" for call in calls)
    assert [call[2] for call in calls] == ["", "", test_url]
    assert all(call[3] == test_url for call in calls)


def test_backend_test_db_stops_when_rebaseline_fails(tmp_path: Path) -> None:
    """Un fallo de la reconstrucción impide que se ejecute la suite de pytest."""

    environment_file = tmp_path / "test.env"
    call_log = tmp_path / "uv-calls.log"
    environment_file.write_text(
        "TEST_DATABASE_URL=postgresql+psycopg://test:test@localhost/guakamole_test\n",
        encoding="utf-8",
    )
    _write_fake_uv(tmp_path)
    make_executable = shutil.which("make")
    assert make_executable is not None
    environment = {
        "PATH": f"{tmp_path}{os.pathsep}{os.environ['PATH']}",
        "CALL_LOG": str(call_log),
        "FAIL_REBASELINE": "1",
    }

    result = subprocess.run(  # noqa: S603 - test fixture controls make and inputs.
        [make_executable, "backend-test-db", f"ENV_FILE={environment_file}"],
        cwd=PROJECT_ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    commands = [
        line.split("\t", maxsplit=1)[0]
        for line in call_log.read_text(encoding="utf-8").splitlines()
    ]
    assert commands == [
        (
            "run python -c from app.core.test_database import "
            "get_test_database_url; import os; get_test_database_url(os.environ)"
        ),
        "run python -m scripts.rebaseline_iam --confirm REBASELINE_IAM",
    ]


def test_backend_test_db_rejects_remote_test_database_before_rebaseline(
    tmp_path: Path,
) -> None:
    """La prevalidación bloquea un destino remoto antes de cualquier destrucción."""

    environment_file = tmp_path / "test.env"
    call_log = tmp_path / "uv-calls.log"
    environment_file.write_text(
        "TEST_DATABASE_URL=postgresql+psycopg://test:test@remote/guakamole_test\n",
        encoding="utf-8",
    )
    _write_fake_uv(tmp_path)
    make_executable = shutil.which("make")
    assert make_executable is not None
    environment = {
        "PATH": f"{tmp_path}{os.pathsep}{os.environ['PATH']}",
        "CALL_LOG": str(call_log),
    }

    result = subprocess.run(  # noqa: S603 - test fixture controls make and inputs.
        [make_executable, "backend-test-db", f"ENV_FILE={environment_file}"],
        cwd=PROJECT_ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    commands = [
        line.split("\t", maxsplit=1)[0]
        for line in call_log.read_text(encoding="utf-8").splitlines()
    ]
    assert commands == [
        (
            "run python -c from app.core.test_database import "
            "get_test_database_url; import os; get_test_database_url(os.environ)"
        )
    ]


def test_backend_test_db_requires_explicit_test_database_url(tmp_path: Path) -> None:
    """El target destructivo no adquiere una URL de pruebas implícita."""

    environment_file = tmp_path / "test.env"
    environment_file.write_text("APP_ENV=test\n", encoding="utf-8")
    make_executable = shutil.which("make")
    assert make_executable is not None

    result = subprocess.run(  # noqa: S603 - controlled test command and environment.
        [make_executable, "backend-test-db", f"ENV_FILE={environment_file}"],
        cwd=PROJECT_ROOT,
        env={"PATH": os.environ["PATH"]},
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "TEST_DATABASE_URL es obligatoria." in result.stderr


@pytest.mark.parametrize(
    "test_file",
    [
        "tests/integration/test_iam_baseline_postgresql.py",
        "tests/integration/test_iam_seed_initial_catalogs.py",
    ],
)
def test_direct_pytest_skips_database_and_integration_tests_without_test_url(
    test_file: str,
) -> None:
    """Pytest directo no debe requerir una DB si no se configuró explícitamente."""

    environment = os.environ.copy()
    environment.pop("TEST_DATABASE_URL", None)
    result = subprocess.run(  # noqa: S603 - controlled test command and environment.
        [sys.executable, "-m", "pytest", "-q", test_file],
        cwd=PROJECT_ROOT / "backend",
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "skipped" in result.stdout


def test_database_roles_skips_without_compose_role_environment() -> None:
    """La suite de host no debe asumir las credenciales privadas de Compose."""

    environment = os.environ.copy()
    environment["TEST_DATABASE_URL"] = (
        "postgresql+psycopg://test:test@localhost/guakamole_test"
    )
    for variable in (
        "MIGRATION_DATABASE_URL",
        "MIGRATION_ALLOWED_HOSTS",
        "MIGRATION_ALLOWED_DATABASES",
        "MIGRATION_EXPECTED_DB_USER",
        "APP_DB_PASSWORD",
        "POSTGRES_DB",
    ):
        environment.pop(variable, None)

    result = subprocess.run(  # noqa: S603 - controlled test command and environment.
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-rs",
            "tests/integration/test_database_roles.py",
        ],
        cwd=PROJECT_ROOT / "backend",
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "Requiere el entorno de roles de Compose" in result.stdout
