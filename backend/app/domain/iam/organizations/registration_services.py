from dataclasses import dataclass
from hashlib import sha256
from typing import Protocol

from sqlalchemy.exc import IntegrityError

from app.domain.auth.config import AuthSettings
from app.domain.auth.password_hasher import PasswordHasher
from app.domain.auth.public_ids import PublicIdPrefix, generate_public_id
from app.domain.iam.organizations.models import Organization
from app.domain.iam.organizations.registration_exceptions import (
    DuplicateRegistrationError,
    InvalidRegistrationReferenceError,
)
from app.domain.iam.organizations.registration_repositories import (
    GeographyReference,
    RegistrationRepository,
)
from app.domain.iam.organizations.registration_schemas import (
    RegistrationRequest,
    RegistrationResponse,
)
from app.domain.iam.users.models import User


class AuditLogger(Protocol):
    def emit(self, *, action: str, metadata: dict[str, str]) -> None: ...


class NoOpAuditLogger:
    def emit(self, *, action: str, metadata: dict[str, str]) -> None:
        _ = (action, metadata)


@dataclass(frozen=True, slots=True)
class RegistrationService:
    repository: RegistrationRepository
    password_hasher: PasswordHasher
    auth_settings: AuthSettings
    audit_logger: AuditLogger = NoOpAuditLogger()

    def register(self, request: RegistrationRequest) -> RegistrationResponse:
        if self.repository.has_duplicates(
            email=request.user.email,
            slug=request.organization.slug,
            tax_id=request.organization.tax_id,
        ):
            raise DuplicateRegistrationError

        organization_status_id = self._required_status_id(
            self.auth_settings.default_registered_organization_status,
        )
        user_status_id = self._required_status_id(
            self.auth_settings.default_registered_user_status,
        )
        platform_role_id = self._required_platform_role_id(
            self.auth_settings.default_platform_role
        )
        organization_role_id = self._required_organization_role_id(
            self.auth_settings.default_organization_role,
        )
        org_geo = self._required_geography(
            country=request.organization.country,
            state=request.organization.state,
            city=request.organization.city,
        )
        user_geo = self._required_geography(
            country=request.user.country,
            state=request.user.state,
            city=request.user.city,
        )

        organization = Organization(
            public_id=generate_public_id(PublicIdPrefix.ORGANIZATION),
            id_country=org_geo.country_id,
            id_state=org_geo.state_id,
            id_city=org_geo.city_id,
            id_status=organization_status_id,
            name=request.organization.name,
            slug=request.organization.slug,
            org_registered_name=request.organization.legal_name,
            org_tax=request.organization.tax_id,
            org_address=request.organization.address,
            org_zipcode=request.organization.postal_code,
        )
        self.repository.add_organization(organization)
        self._flush_organization()
        user = User(
            public_id=generate_public_id(PublicIdPrefix.USER),
            id_organization=organization.id_organization,
            id_platform_role=platform_role_id,
            id_country=user_geo.country_id,
            id_state=user_geo.state_id,
            id_city=user_geo.city_id,
            id_org_role=organization_role_id,
            id_status=user_status_id,
            email=request.user.email,
            password_hash=self.password_hasher.hash(request.user.password),
            first_name=request.user.first_name,
            last_name=request.user.last_name,
            birthdate=request.user.birth_date,
            user_address=request.user.address,
            user_zipcode=request.user.postal_code,
        )
        self.repository.add_user(user)
        try:
            self.repository.commit()
        except IntegrityError as error:
            self.repository.rollback()
            raise DuplicateRegistrationError from error

        self._audit(
            organization_public_id=organization.public_id,
            user_public_id=user.public_id,
            email=request.user.email,
        )
        return RegistrationResponse(
            organization_id=organization.public_id,
            user_id=user.public_id,
            organization_status=self.auth_settings.default_registered_organization_status,
            user_status=self.auth_settings.default_registered_user_status,
        )

    def _flush_organization(self) -> None:
        try:
            self.repository.flush()
        except IntegrityError as error:
            self.repository.rollback()
            raise DuplicateRegistrationError from error

    def _required_status_id(self, status_name: str) -> int:
        status_id = self.repository.get_status_id(status_name)
        if status_id is None:
            raise InvalidRegistrationReferenceError
        return status_id

    def _required_platform_role_id(self, role_name: str) -> int:
        role_id = self.repository.get_platform_role_id(role_name)
        if role_id is None:
            raise InvalidRegistrationReferenceError
        return role_id

    def _required_organization_role_id(self, role_name: str) -> int:
        role_id = self.repository.get_organization_role_id(role_name)
        if role_id is None:
            raise InvalidRegistrationReferenceError
        return role_id

    def _required_geography(
        self, *, country: str, state: str, city: str
    ) -> GeographyReference:
        geography = self.repository.get_geography(
            country=country, state=state, city=city
        )
        if geography is None:
            raise InvalidRegistrationReferenceError
        return geography

    def _audit(
        self, *, organization_public_id: str, user_public_id: str, email: str
    ) -> None:
        email_hash = sha256(email.encode("utf-8")).hexdigest()
        self.audit_logger.emit(
            action="ORGANIZATION_REGISTERED",
            metadata={"organization_id": organization_public_id},
        )
        self.audit_logger.emit(
            action="USER_REGISTERED",
            metadata={"user_id": user_public_id, "email_hash": email_hash},
        )
