"""Infraestructura SQLAlchemy compartida por las dependencias HTTP."""

import os
from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL_ENV_VAR = "DATABASE_URL"


def get_required_database_url() -> str:
    database_url = os.environ.get(DATABASE_URL_ENV_VAR)
    if not database_url:
        msg = f"La variable de entorno {DATABASE_URL_ENV_VAR} debe estar definida."
        raise RuntimeError(msg)
    return database_url


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    return create_engine(get_required_database_url(), hide_parameters=True)


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_db_session() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
