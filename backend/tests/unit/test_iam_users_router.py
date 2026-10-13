"""El piloto IAM/users conserva sus pruebas internas, pero no se publica aún."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

pytestmark = pytest.mark.test_unit


def test_iam_users_pilot_is_not_mounted_in_public_api() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/iam/organizations/1/users")

    assert response.status_code == 404
