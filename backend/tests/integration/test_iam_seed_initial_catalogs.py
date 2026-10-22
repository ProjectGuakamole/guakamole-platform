from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

MIGRATION_PATH = Path("alembic/versions/iam_baseline.py")


def test_iam_baseline_is_single_root_revision_with_only_ddl() -> None:
    content = MIGRATION_PATH.read_text(encoding="utf-8")

    assert 'revision = "iam_baseline"' in content
    assert "down_revision: str | None = None" in content
    assert content.count("op.create_table(") == 11
    for forbidden in ("INSERT ", "UPDATE ", "DELETE ", "TRUNCATE ", "pgcrypto"):
        assert forbidden not in content


def test_iam_baseline_keeps_alembic_metadata_outside_iam_schema() -> None:
    content = MIGRATION_PATH.read_text(encoding="utf-8")

    assert "alembic_version" not in content
    assert "GRANT" not in content
    assert "REVOKE" not in content
