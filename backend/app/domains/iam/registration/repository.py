from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domains.iam.access.models import OrganizationRole, PlatformRole, Status
from app.domains.iam.geography.models import City, Country, State
from app.domains.iam.organizations.models import Organization
from app.domains.iam.registration.entities import (
    RegistrationOrganization,
    RegistrationUser,
)
from app.domains.iam.registration.exceptions import RegistrationPersistenceConflictError
from app.domains.iam.users.models import User


@dataclass(frozen=True, slots=True)
class GeographyReference:
    country_id: int
    state_id: int
    city_id: int


class RegistrationRepository(Protocol):
    def has_duplicates(self, *, email: str, slug: str, tax_id: str) -> bool: ...
    def get_status_id(self, status_name: str) -> int | None: ...
    def get_platform_role_id(self, role_name: str) -> int | None: ...
    def get_organization_role_id(self, role_name: str) -> int | None: ...
    def get_geography(
        self, *, country: str, state: str, city: str
    ) -> GeographyReference | None: ...
    def add_organization(self, organization: RegistrationOrganization) -> None: ...
    def add_user(self, user: RegistrationUser) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def flush(self) -> None: ...


class SqlAlchemyRegistrationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._pending_organization: (
            tuple[RegistrationOrganization, Organization] | None
        ) = None

    def has_duplicates(self, *, email: str, slug: str, tax_id: str) -> bool:
        query = select(Organization.id_organization).where(
            (Organization.slug == slug) | (Organization.org_tax == tax_id),
        )
        user_query = select(User.id_user).where(User.email == email)
        return (
            self._session.scalar(query) is not None
            or self._session.scalar(user_query) is not None
        )

    def get_status_id(self, status_name: str) -> int | None:
        return self._session.scalar(
            select(Status.id_status).where(Status.status == status_name)
        )

    def get_platform_role_id(self, role_name: str) -> int | None:
        return self._session.scalar(
            select(PlatformRole.id_platform_role).where(
                PlatformRole.platform_role_type == role_name
            ),
        )

    def get_organization_role_id(self, role_name: str) -> int | None:
        return self._session.scalar(
            select(OrganizationRole.id_org_role).where(
                OrganizationRole.org_role_type == role_name
            ),
        )

    def get_geography(
        self, *, country: str, state: str, city: str
    ) -> GeographyReference | None:
        statement = (
            select(Country.id_country, State.id_state, City.id_city)
            .join(State, State.id_country == Country.id_country)
            .join(City, City.id_state == State.id_state)
            .where(
                func.lower(Country.country_name) == country.lower(),
                func.lower(State.state_name) == state.lower(),
                func.lower(City.city_name) == city.lower(),
            )
        )
        row = self._session.execute(statement).one_or_none()
        if row is None:
            return None
        return GeographyReference(country_id=row[0], state_id=row[1], city_id=row[2])

    def add_organization(self, organization: RegistrationOrganization) -> None:
        entity = Organization(
            public_id=organization.public_id,
            id_country=organization.country_id,
            id_state=organization.state_id,
            id_city=organization.city_id,
            id_status=organization.status_id,
            name=organization.name,
            slug=organization.slug,
            org_registered_name=organization.legal_name,
            org_tax=organization.tax_id,
            org_address=organization.address,
            org_zipcode=organization.postal_code,
        )
        self._session.add(entity)
        self._pending_organization = (organization, entity)

    def add_user(self, user: RegistrationUser) -> None:
        self._session.add(
            User(
                public_id=user.public_id,
                id_organization=user.organization_id,
                id_platform_role=user.platform_role_id,
                id_country=user.country_id,
                id_state=user.state_id,
                id_city=user.city_id,
                id_org_role=user.organization_role_id,
                id_status=user.status_id,
                email=user.email,
                password_hash=user.password_hash,
                first_name=user.first_name,
                last_name=user.last_name,
                birthdate=user.birth_date,
                user_address=user.address,
                user_zipcode=user.postal_code,
            )
        )

    def flush(self) -> None:
        try:
            self._session.flush()
            if self._pending_organization is not None:
                dto, entity = self._pending_organization
                dto.id = entity.id_organization
        except IntegrityError as error:
            self._session.rollback()
            raise RegistrationPersistenceConflictError from error

    def commit(self) -> None:
        try:
            self._session.commit()
        except IntegrityError as error:
            self._session.rollback()
            raise RegistrationPersistenceConflictError from error

    def rollback(self) -> None:
        self._session.rollback()
