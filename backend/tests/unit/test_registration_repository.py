from typing import cast
from unittest.mock import Mock

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domains.iam.registration.exceptions import RegistrationPersistenceConflictError
from app.domains.iam.registration.repository import SqlAlchemyRegistrationRepository

pytestmark = pytest.mark.test_unit


def build_integrity_error(operation: str) -> IntegrityError:
    return IntegrityError(
        f"INSERT INTO organizations ({operation})",
        {"email": "ana@example.test"},
        Exception("duplicate key value violates unique constraint"),
    )


def test_flush_rolls_back_and_translates_integrity_error() -> None:
    session_mock = Mock(spec=Session)
    sql_error = build_integrity_error("flush")
    session_mock.flush.side_effect = sql_error
    repository = SqlAlchemyRegistrationRepository(cast(Session, session_mock))

    with pytest.raises(RegistrationPersistenceConflictError) as raised_error:
        repository.flush()

    session_mock.rollback.assert_called_once_with()
    assert raised_error.value.args == ()
    assert str(raised_error.value) == ""
    assert "duplicate key" not in str(raised_error.value)
    assert "INSERT INTO" not in str(raised_error.value)


def test_commit_rolls_back_and_translates_integrity_error() -> None:
    session_mock = Mock(spec=Session)
    sql_error = build_integrity_error("commit")
    session_mock.commit.side_effect = sql_error
    repository = SqlAlchemyRegistrationRepository(cast(Session, session_mock))

    with pytest.raises(RegistrationPersistenceConflictError) as raised_error:
        repository.commit()

    session_mock.rollback.assert_called_once_with()
    assert raised_error.value.args == ()
    assert str(raised_error.value) == ""
    assert "duplicate key" not in str(raised_error.value)
    assert "INSERT INTO" not in str(raised_error.value)
