"""CLI fino para cargar los catálogos IAM canónicos."""

from __future__ import annotations

import os

from alembic.util.exc import CommandError
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

from app.core.iam_bootstrap import bootstrap_iam
from app.core.iam_rebaseline import validate_safe_target


def main() -> int:
    try:
        print('{"event":"bootstrap.start"}')
        variable = (
            "TEST_DATABASE_URL"
            if os.environ.get("APP_ENV") == "test"
            else "BOOTSTRAP_DEVELOPMENT_DATABASE_URL"
        )
        url = validate_safe_target(os.environ, variable)
        engine = create_engine(url, hide_parameters=True)
        try:
            result = bootstrap_iam(engine)
        finally:
            engine.dispose()
        print(f'{{"event":"bootstrap.complete","created":{result.created}}}')
        return 0
    except (CommandError, OSError, RuntimeError, SQLAlchemyError, ValueError):
        print('{"event":"bootstrap.failed"}')
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
