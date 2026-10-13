"""Selector seguro de base de datos exclusivo para integración."""

from __future__ import annotations

from collections.abc import Mapping

from sqlalchemy.engine import make_url


def get_test_database_url(environment: Mapping[str, str]) -> str:
    """Exige una URL PostgreSQL cuyo nombre de base termine en ``_test``."""

    raw_url = environment.get("TEST_DATABASE_URL")
    if not raw_url:
        raise RuntimeError("TEST_DATABASE_URL es obligatoria para los tests DB.")
    url = make_url(raw_url)
    if url.get_backend_name() != "postgresql" or not url.database:
        raise RuntimeError("TEST_DATABASE_URL debe apuntar a PostgreSQL.")
    if not url.database.endswith("_test"):
        raise RuntimeError(
            "TEST_DATABASE_URL debe usar una base dedicada terminada en _test."
        )
    return raw_url
