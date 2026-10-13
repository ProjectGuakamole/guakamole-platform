"""Contratos estructurales del modelo ORM de revocación JWT."""

import pytest
from sqlalchemy import BigInteger, DateTime, String

import app.db.model_registry as model_registry
from app.db.base import Base

pytestmark = pytest.mark.test_unit


def test_revoked_access_token_is_registered_with_the_expected_metadata() -> None:
    _ = model_registry
    table = Base.metadata.tables["sch_iam.tbl_revoked_access_token"]

    assert table.schema == "sch_iam"
    assert table.name == "tbl_revoked_access_token"
    assert isinstance(table.c.id_revoked_access_token.type, BigInteger)
    assert isinstance(table.c.jti.type, String)
    assert isinstance(table.c.expires_at.type, DateTime)
    assert isinstance(table.c.revoked_at.type, DateTime)
    assert table.c.jti.unique is None
    assert any(
        index.unique and index.name == "ix_tbl_revoked_access_token_jti"
        for index in table.indexes
    )
