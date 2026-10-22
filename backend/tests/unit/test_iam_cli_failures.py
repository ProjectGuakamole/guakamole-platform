"""Los CLIs IAM no exponen detalles internos ante fallos operacionales."""

from __future__ import annotations

import argparse
import sys
from types import ModuleType
from typing import NoReturn

import pytest
from sqlalchemy.exc import OperationalError

from scripts import bootstrap_iam, rebaseline_iam, seed_demo_iam

pytestmark = pytest.mark.test_unit

SENSITIVE_DATABASE_URL = (
    "postgresql+psycopg://operator:super-secret@localhost/guakamole_test"
)


def _operational_error() -> OperationalError:
    return OperationalError(
        "SELECT 1",
        {"password": "super-secret"},
        ConnectionRefusedError("database engine unavailable"),
    )


def _raise_operational_error(*_args: object, **_kwargs: object) -> NoReturn:
    raise _operational_error()


@pytest.mark.parametrize(
    ("module", "failure_target"),
    [
        (
            rebaseline_iam,
            "rebaseline_configured_database",
        ),
        (bootstrap_iam, "create_engine"),
        (seed_demo_iam, "create_engine"),
    ],
)
def test_iam_clis_emit_sanitized_failure_for_operational_errors(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    module: object,
    failure_target: str,
) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("TEST_DATABASE_URL", SENSITIVE_DATABASE_URL)
    monkeypatch.setenv("DEMO_SEED_PASSWORD", "super-secret")
    monkeypatch.setattr(
        rebaseline_iam,
        "parse_arguments",
        lambda: argparse.Namespace(confirm="REBASELINE_IAM"),
    )
    monkeypatch.setattr(sys, "argv", ["seed_demo_iam.py", "--yes"])
    monkeypatch.setattr(module, failure_target, _raise_operational_error)

    assert isinstance(module, ModuleType)
    exit_code = module.main()
    output = capsys.readouterr().out

    assert exit_code == 1
    assert '"event":"' in output
    assert ".failed" in output
    assert "Traceback" not in output
    assert SENSITIVE_DATABASE_URL not in output
    assert "super-secret" not in output
    assert "database engine unavailable" not in output
