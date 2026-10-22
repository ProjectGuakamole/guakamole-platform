"""Reconstruye IAM sólo en bases aisladas de desarrollo local o test."""

from __future__ import annotations

import argparse
import os

from alembic.config import Config
from alembic.util.exc import CommandError
from sqlalchemy.exc import SQLAlchemyError

from app.core.iam_rebaseline import CONFIRMATION_TOKEN, rebaseline_configured_database


def parse_arguments() -> argparse.Namespace:
    """Obtiene la confirmación explícita requerida para la operación destructiva."""

    parser = argparse.ArgumentParser(
        description=(
            f"{__doc__} Con APP_ENV=test exige TEST_DATABASE_URL PostgreSQL con "
            "nombre terminado en _test. Con APP_ENV=development exige "
            "REBASELINE_DEVELOPMENT_DATABASE_URL PostgreSQL local "
            "(localhost, 127.0.0.1, ::1 o socket Unix) con nombre terminado en "
            "_dev o _development. DATABASE_URL nunca se usa."
        )
    )
    parser.add_argument(
        "--confirm", required=True, help=f"Debe ser {CONFIRMATION_TOKEN}."
    )
    return parser.parse_args()


def main() -> int:
    """Reconstruye IAM desde ``iam_baseline``; nunca se invoca al arrancar FastAPI."""

    try:
        arguments = parse_arguments()
        rebaseline_configured_database(
            os.environ, arguments.confirm, Config("alembic.ini")
        )
    except (CommandError, OSError, RuntimeError, SQLAlchemyError, ValueError):
        print('{"event":"rebaseline.failed"}')
        return 1
    print('{"event":"rebaseline.complete"}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
