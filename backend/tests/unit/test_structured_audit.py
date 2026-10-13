"""Pruebas de la auditoría estructurada no persistente de runtime."""

import logging
from collections.abc import Iterator, Mapping
from typing import cast

import pytest

from app.domains.auth.login.audit import StructuredLoginAuditAdapter
from app.domains.auth.login.service import LoginFailedAuditEvent, LoginSuccessAuditEvent
from app.domains.iam.registration.dependencies import get_registration_service
from app.domains.iam.users.dependencies import get_list_organization_users_service
from app.shared.audit import (
    REDACTED_VALUE,
    TRUNCATED_VALUE,
    StructuredAuditLogger,
)

pytestmark = pytest.mark.test_unit


class CapturingHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


class FailingMetadata(Mapping[str, object]):
    def __getitem__(self, key: str) -> object:
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        raise RuntimeError("fallo de saneamiento")

    def __len__(self) -> int:
        return 0


def test_login_audit_emits_safe_success_and_failure_events() -> None:
    logger = logging.getLogger("test.audit.login")
    handler = CapturingHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    adapter = StructuredLoginAuditAdapter(StructuredAuditLogger(logger))

    adapter.record_login_success(
        LoginSuccessAuditEvent("LOGIN_SUCCESS", "hash", "usr_1")
    )
    adapter.record_login_failed(LoginFailedAuditEvent("LOGIN_FAILED", "hash"))

    logger.removeHandler(handler)
    metadata = [
        cast(dict[str, str], record.__dict__["audit_metadata"])
        for record in handler.records
    ]
    actions = [cast(str, record.__dict__["audit_action"]) for record in handler.records]
    assert actions == ["LOGIN_SUCCESS", "LOGIN_FAILED"]
    assert metadata == [
        {"email_hash": "hash", "user_id": "usr_1"},
        {"email_hash": "hash"},
    ]
    assert "password" not in repr(metadata).lower()
    assert "token" not in repr(metadata).lower()


def test_structured_audit_never_blocks_when_logger_fails() -> None:
    logger = logging.getLogger("test.audit.failing")

    class FailingHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            _ = record
            raise RuntimeError("logger failure")

    handler = FailingHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    StructuredAuditLogger(logger).emit(
        action="USER_REGISTERED", metadata={"user_id": "usr_1"}
    )

    logger.removeHandler(handler)


def test_structured_audit_discards_sensitive_metadata_recursively() -> None:
    logger = logging.getLogger("test.audit.sensitive")
    handler = CapturingHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    StructuredAuditLogger(logger).emit(
        action="USER_REGISTERED",
        metadata={
            "password": "PasswordSeguro123!",
            "password_hash": "argon2-hash",
            "accessToken": "access-token-value",
            "refresh_token": "refresh-token-value",
            "jwt": "header.payload.signature",
            "csrf-token": "csrf-token-value",
            "client_secret": "client-secret-value",
            "Authorization": "Bearer secret-bearer-value",
            "nested": {
                "token": "nested-token",
                "passwordHash": "nested-hash",
                "allowed": "visible",
            },
            "events": [
                {"secret": "nested-secret", "event_id": "evt_1"},
                "Bearer nested-bearer-value",
                "header.payload.signature",
            ],
        },
    )

    logger.removeHandler(handler)
    metadata = cast(dict[str, object], handler.records[0].__dict__["audit_metadata"])
    assert metadata == {
        "nested": {"allowed": "visible"},
        "events": [{"event_id": "evt_1"}, REDACTED_VALUE, REDACTED_VALUE],
    }


def test_structured_audit_discards_private_key_and_passphrase_metadata() -> None:
    logger = logging.getLogger("test.audit.private_key")
    handler = CapturingHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    sensitive_values = {
        "private_key": "private-key-value",
        "private-key": "private-key-dashed-value",
        "privateKey": "private-key-camel-value",
        "PRIVATE_KEY": "private-key-uppercase-value",
        "passphrase": "passphrase-value",
        "Pass-Phrase": "passphrase-dashed-value",
    }

    StructuredAuditLogger(logger).emit(
        action="LAB_REQUESTED",
        metadata={**sensitive_values, "lab_id": "lab_1"},
    )

    logger.removeHandler(handler)
    metadata = cast(dict[str, object], handler.records[0].__dict__["audit_metadata"])
    assert metadata == {"lab_id": "lab_1"}
    emitted_metadata = repr(metadata)
    for value in sensitive_values.values():
        assert value not in emitted_metadata


def test_structured_audit_discards_nested_private_key_and_passphrase_metadata() -> None:
    logger = logging.getLogger("test.audit.nested_private_key")
    handler = CapturingHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    sensitive_values = {
        "private_key": "nested-private-key-value",
        "private-key": "nested-private-key-dashed-value",
        "privateKey": "nested-private-key-camel-value",
        "passphrase": "nested-passphrase-value",
        "PASS_PHRASE": "nested-passphrase-uppercase-value",
    }

    StructuredAuditLogger(logger).emit(
        action="LAB_REQUESTED",
        metadata={
            "lab": {
                **sensitive_values,
                "provider": "docker",
            },
        },
    )

    logger.removeHandler(handler)
    metadata = cast(dict[str, object], handler.records[0].__dict__["audit_metadata"])
    assert metadata == {"lab": {"provider": "docker"}}
    emitted_metadata = repr(metadata)
    for value in sensitive_values.values():
        assert value not in emitted_metadata


def test_structured_audit_preserves_allowed_serializable_metadata() -> None:
    logger = logging.getLogger("test.audit.allowed")
    handler = CapturingHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    StructuredAuditLogger(logger).emit(
        action="CASE_SUBMITTED",
        metadata={
            "organization_id": "org_1",
            "user_id": "usr_1",
            "actor_hash": "safe-hash",
            "correlation_id": "corr_1",
            "attempt": 2,
            "active": True,
            "tenant": {"id": "org_1"},
        },
    )

    logger.removeHandler(handler)
    metadata = cast(dict[str, object], handler.records[0].__dict__["audit_metadata"])
    assert metadata == {
        "organization_id": "org_1",
        "user_id": "usr_1",
        "actor_hash": "safe-hash",
        "correlation_id": "corr_1",
        "attempt": 2,
        "active": True,
        "tenant": {"id": "org_1"},
    }


def test_structured_audit_handles_non_serializable_and_long_values() -> None:
    logger = logging.getLogger("test.audit.serializable")
    handler = CapturingHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    StructuredAuditLogger(logger).emit(
        action="CASE_SUBMITTED",
        metadata={"safe": "value", "too_long": "a" * 1_025, "object": object()},
    )

    logger.removeHandler(handler)
    metadata = cast(dict[str, object], handler.records[0].__dict__["audit_metadata"])
    assert metadata == {"safe": "value", "too_long": TRUNCATED_VALUE}


def test_structured_audit_never_blocks_when_metadata_sanitization_fails() -> None:
    StructuredAuditLogger(logging.getLogger("test.audit.sanitization")).emit(
        action="CASE_SUBMITTED", metadata=FailingMetadata()
    )


def test_runtime_factories_do_not_use_noop_auditing() -> None:
    assert "NoOp" not in get_registration_service.__code__.co_names
    assert "Noop" not in get_list_organization_users_service.__code__.co_names
