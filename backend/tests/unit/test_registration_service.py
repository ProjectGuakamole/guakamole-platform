from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.domain.auth.config import AuthSettings
from app.domain.iam.organizations.models import Organization
from app.domain.iam.organizations.registration_exceptions import (
    DuplicateRegistrationError,
)
from app.domain.iam.organizations.registration_repositories import GeographyReference
from app.domain.iam.organizations.registration_schemas import RegistrationRequest
from app.domain.iam.organizations.registration_services import RegistrationService
from app.domain.iam.users.models import User

pytestmark = pytest.mark.test_unit


class FakeHasher:
    def hash(self, plain_password: str) -> str:
        return f"hashed:{plain_password}"

    def verify(self, plain_password: str, password_hash: str) -> bool:
        return password_hash == f"hashed:{plain_password}"


class FakeRepository:
    def __init__(
        self,
        *,
        duplicates: bool = False,
        fail_flush: bool = False,
        fail_commit: bool = False,
    ) -> None:
        self.duplicates = duplicates
        self.fail_flush = fail_flush
        self.fail_commit = fail_commit
        self.organizations: list[Organization] = []
        self.users: list[User] = []
        self.rollback_called = False

    def has_duplicates(self, *, email: str, slug: str, tax_id: str) -> bool:
        _ = (email, slug, tax_id)
        return self.duplicates

    def get_status_id(self, status_name: str) -> int | None:
        _ = status_name
        return 1

    def get_platform_role_id(self, role_name: str) -> int | None:
        _ = role_name
        return 2

    def get_organization_role_id(self, role_name: str) -> int | None:
        _ = role_name
        return 3

    def get_geography(
        self, *, country: str, state: str, city: str
    ) -> GeographyReference | None:
        _ = (country, state, city)
        return GeographyReference(country_id=4, state_id=5, city_id=6)

    def add_organization(self, organization: Organization) -> None:
        self.organizations.append(organization)

    def add_user(self, user: User) -> None:
        self.users.append(user)

    def flush(self) -> None:
        if self.fail_flush:
            raise IntegrityError("insert organization", {}, Exception("duplicate"))
        organization = self.organizations[0]
        organization.id_organization = 99

    def commit(self) -> None:
        if self.fail_commit:
            raise IntegrityError("commit", {}, Exception("duplicate"))
        return

    def rollback(self) -> None:
        self.rollback_called = True


def build_request() -> RegistrationRequest:
    return RegistrationRequest.model_validate(
        {
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
                "birth_date": date(1990, 1, 1),
                "password": "PasswordSeguro123!",
                "password_confirm": "PasswordSeguro123!",
                "country": "España",
                "state": "Catalunya",
                "city": "Barcelona",
                "address": "Calle Mayor 10",
                "postal_code": "08001",
            },
        }
    )


def build_settings() -> AuthSettings:
    return AuthSettings.model_validate({"jwt_secret_key": "test-secret"})


def test_service_rejects_duplicates_with_generic_error() -> None:
    service = RegistrationService(
        FakeRepository(duplicates=True), FakeHasher(), build_settings()
    )

    with pytest.raises(DuplicateRegistrationError):
        service.register(build_request())


def test_service_maps_flush_integrity_error_to_duplicate_registration() -> None:
    repository = FakeRepository(fail_flush=True)
    service = RegistrationService(repository, FakeHasher(), build_settings())

    with pytest.raises(DuplicateRegistrationError):
        service.register(build_request())

    assert repository.rollback_called is True
    assert repository.users == []


def test_service_maps_commit_integrity_error_to_duplicate_registration() -> None:
    repository = FakeRepository(fail_commit=True)
    service = RegistrationService(repository, FakeHasher(), build_settings())

    with pytest.raises(DuplicateRegistrationError):
        service.register(build_request())

    assert repository.rollback_called is True


def test_service_uses_public_ids_and_hashes_password() -> None:
    repository = FakeRepository()
    service = RegistrationService(repository, FakeHasher(), build_settings())
    request = build_request()

    response = service.register(request)

    user = repository.users[0]
    assert response.organization_id.startswith("org_")
    assert response.user_id.startswith("usr_")
    assert response.organization_id != "99"
    assert user.password_hash.startswith("hashed:")
    assert user.password_hash != request.user.password
