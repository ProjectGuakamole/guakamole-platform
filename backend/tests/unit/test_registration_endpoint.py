import pytest
from fastapi.testclient import TestClient

from app.domain.iam.organizations.registration_exceptions import (
    DuplicateRegistrationError,
    InvalidRegistrationReferenceError,
)
from app.domain.iam.organizations.registration_routers import get_registration_service
from app.domain.iam.organizations.registration_schemas import (
    RegistrationRequest,
    RegistrationResponse,
)
from app.main import create_app

pytestmark = pytest.mark.test_unit


class StubRegistrationService:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error

    def register(self, request: RegistrationRequest) -> RegistrationResponse:
        _ = request
        if self.error is not None:
            raise self.error
        return RegistrationResponse(
            organization_id="org_public",
            user_id="usr_public",
            organization_status="PENDING_ACTIVATION",
            user_status="ACTIVE",
        )


def build_payload() -> dict[str, object]:
    return {
        "organization": {
            "name": "Mi Empresa",
            "slug": "mi-empresa",
            "legal_name": "Mi Empresa S.L.",
            "tax_id": "B12345678",
            "country": "España",
            "state": "Catalunya",
            "city": "Barcelona",
            "address": "Calle Mayor 10",
            "postal_code": "08001",
        },
        "user": {
            "first_name": "Ana",
            "last_name": "García",
            "email": "ana@empresa.com",
            "birth_date": "1990-01-01",
            "password": "PasswordSeguro123!",
            "password_confirm": "PasswordSeguro123!",
            "country": "España",
            "state": "Catalunya",
            "city": "Barcelona",
            "address": "Calle Mayor 10",
            "postal_code": "08001",
        },
    }


def build_client(service: StubRegistrationService) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_registration_service] = lambda: service
    return TestClient(app)


def test_register_endpoint_returns_public_ids_without_sensitive_fields() -> None:
    client = build_client(StubRegistrationService())

    response = client.post("/api/v1/organizations/register", json=build_payload())

    assert response.status_code == 201
    body = response.json()
    assert body == {
        "organization_id": "org_public",
        "user_id": "usr_public",
        "organization_status": "PENDING_ACTIVATION",
        "user_status": "ACTIVE",
    }
    assert "password" not in body
    assert "password_hash" not in body
    assert "id_organization" not in body
    assert "id_user" not in body


def test_register_endpoint_rejects_extra_organization_id() -> None:
    client = build_client(StubRegistrationService())
    payload = build_payload()
    payload["organization_id"] = 1

    response = client.post("/api/v1/organizations/register", json=payload)

    assert response.status_code == 422


def test_register_endpoint_maps_duplicate_to_conflict() -> None:
    client = build_client(StubRegistrationService(DuplicateRegistrationError()))

    response = client.post("/api/v1/organizations/register", json=build_payload())

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "No se puede completar el registro con los datos proporcionados."
    )


def test_register_endpoint_maps_invalid_catalog_to_public_bad_request() -> None:
    client = build_client(StubRegistrationService(InvalidRegistrationReferenceError()))

    response = client.post("/api/v1/organizations/register", json=build_payload())

    assert response.status_code == 400
    assert response.json()["detail"] == "Datos de registro inválidos."
