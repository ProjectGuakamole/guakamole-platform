from dataclasses import dataclass
from hashlib import sha256
from typing import Protocol

from app.domains.auth.shared.config import AuthSettings
from app.domains.auth.shared.password_hasher import PasswordHasher
from app.domains.auth.shared.public_ids import PublicIdPrefix, generate_public_id
from app.domains.iam.registration.entities import (
    RegistrationOrganization,
    RegistrationUser,
)
from app.domains.iam.registration.exceptions import (
    DuplicateRegistrationError,
    InvalidRegistrationReferenceError,
    RegistrationPersistenceConflictError,
)
from app.domains.iam.registration.repository import (
    GeographyReference,
    RegistrationRepository,
)
from app.domains.iam.registration.schemas import (
    RegistrationRequest,
    RegistrationResponse,
)


class AuditLogger(Protocol):
    def emit(self, *, action: str, metadata: dict[str, str]) -> None: ...


class NoOpAuditLogger:
    """Implementación exclusiva para pruebas unitarias explícitas."""

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
        organization = self._build_organization(request)
        self.repository.add_organization(organization)
        self._flush_organization()
        if organization.id is None:
            raise InvalidRegistrationReferenceError
        user = self._build_user(request, organization.id)
        self.repository.add_user(user)
        try:
            self.repository.commit()
        except RegistrationPersistenceConflictError as error:
            raise DuplicateRegistrationError from error
        self._audit(organization.public_id, user.public_id, request.user.email)
        return RegistrationResponse(
            organization_id=organization.public_id,
            user_id=user.public_id,
            organization_status=self.auth_settings.default_registered_organization_status,
            user_status=self.auth_settings.default_registered_user_status,
        )

    def _build_organization(
        self, request: RegistrationRequest
    ) -> RegistrationOrganization:
        geography = self._required_geography(
            request.organization.country,
            request.organization.state,
            request.organization.city,
        )
        return RegistrationOrganization(
            public_id=generate_public_id(PublicIdPrefix.ORGANIZATION),
            country_id=geography.country_id,
            state_id=geography.state_id,
            city_id=geography.city_id,
            status_id=self._required_status_id(
                self.auth_settings.default_registered_organization_status
            ),
            name=request.organization.name,
            slug=request.organization.slug,
            legal_name=request.organization.legal_name,
            tax_id=request.organization.tax_id,
            address=request.organization.address,
            postal_code=request.organization.postal_code,
        )

    def _build_user(
        self, request: RegistrationRequest, organization_id: int
    ) -> RegistrationUser:
        geography = self._required_geography(
            request.user.country, request.user.state, request.user.city
        )
        return RegistrationUser(
            public_id=generate_public_id(PublicIdPrefix.USER),
            organization_id=organization_id,
            platform_role_id=self._required_platform_role_id(
                self.auth_settings.default_platform_role
            ),
            country_id=geography.country_id,
            state_id=geography.state_id,
            city_id=geography.city_id,
            organization_role_id=self._required_organization_role_id(
                self.auth_settings.default_organization_role
            ),
            status_id=self._required_status_id(
                self.auth_settings.default_registered_user_status
            ),
            email=request.user.email,
            password_hash=self.password_hasher.hash(request.user.password),
            first_name=request.user.first_name,
            last_name=request.user.last_name,
            birth_date=request.user.birth_date,
            address=request.user.address,
            postal_code=request.user.postal_code,
        )

    def _flush_organization(self) -> None:
        try:
            self.repository.flush()
        except RegistrationPersistenceConflictError as error:
            raise DuplicateRegistrationError from error

    def _required_status_id(self, name: str) -> int:
        return self._required(self.repository.get_status_id(name))

    def _required_platform_role_id(self, name: str) -> int:
        return self._required(self.repository.get_platform_role_id(name))

    def _required_organization_role_id(self, name: str) -> int:
        return self._required(self.repository.get_organization_role_id(name))

    def _required_geography(
        self, country: str, state: str, city: str
    ) -> GeographyReference:
        geography = self.repository.get_geography(
            country=country, state=state, city=city
        )
        if geography is None:
            raise InvalidRegistrationReferenceError
        return geography

    @staticmethod
    def _required(value: int | None) -> int:
        if value is None:
            raise InvalidRegistrationReferenceError
        return value

    def _audit(self, organization_id: str, user_id: str, email: str) -> None:
        self._emit_audit(
            action="ORGANIZATION_REGISTERED",
            metadata={"organization_id": organization_id},
        )
        self._emit_audit(
            action="USER_REGISTERED",
            metadata={
                "user_id": user_id,
                "email_hash": sha256(email.encode()).hexdigest(),
            },
        )

    def _emit_audit(self, *, action: str, metadata: dict[str, str]) -> None:
        try:
            self.audit_logger.emit(action=action, metadata=metadata)
        except Exception:
            # La auditoría no persistente es auxiliar y no puede deshacer un registro.
            return
