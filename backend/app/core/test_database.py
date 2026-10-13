"""Selector seguro de base de datos exclusivo para integración."""

from __future__ import annotations

from collections.abc import Mapping

from sqlalchemy.engine import URL, make_url

LOCAL_DATABASE_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def get_test_database_url(environment: Mapping[str, str]) -> str:
    """Exige una URL PostgreSQL local cuyo nombre de base termine en ``_test``."""

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
    if not uses_local_database_host(url):
        raise RuntimeError(
            "TEST_DATABASE_URL debe usar localhost, 127.0.0.1, ::1 o un socket "
            "Unix local."
        )
    return raw_url


def uses_local_database_host(url: URL) -> bool:
    """Comprueba que el destino sea un loopback o un socket Unix local."""

    if url.host in LOCAL_DATABASE_HOSTS:
        return True
    socket_host = url.query.get("host")
    return (
        url.host is None
        and isinstance(socket_host, str)
        and socket_host.startswith("/")
    )
