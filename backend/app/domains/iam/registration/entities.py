"""DTOs internos del caso de uso de registro, independientes del ORM."""

from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class RegistrationOrganization:
    public_id: str
    country_id: int
    state_id: int
    city_id: int
    status_id: int
    name: str
    slug: str
    legal_name: str
    tax_id: str
    address: str
    postal_code: str
    id: int | None = None


@dataclass(frozen=True, slots=True)
class RegistrationUser:
    public_id: str
    organization_id: int
    platform_role_id: int
    country_id: int
    state_id: int
    city_id: int
    organization_role_id: int
    status_id: int
    email: str
    password_hash: str
    first_name: str
    last_name: str
    birth_date: date
    address: str
    postal_code: str
