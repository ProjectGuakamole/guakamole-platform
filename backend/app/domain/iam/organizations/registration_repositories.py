from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.iam.access.models import OrganizationRole, PlatformRole, Status
from app.domain.iam.geography.models import City, Country, State
from app.domain.iam.organizations.models import Organization
from app.domain.iam.users.models import User


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
    def add_organization(self, organization: Organization) -> None: ...
    def add_user(self, user: User) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def flush(self) -> None: ...


class SqlAlchemyRegistrationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

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

    def add_organization(self, organization: Organization) -> None:
        self._session.add(organization)

    def add_user(self, user: User) -> None:
        self._session.add(user)

    def flush(self) -> None:
        self._session.flush()

    def commit(self) -> None:
        try:
            self._session.commit()
        except IntegrityError:
            self._session.rollback()
            raise

    def rollback(self) -> None:
        self._session.rollback()
