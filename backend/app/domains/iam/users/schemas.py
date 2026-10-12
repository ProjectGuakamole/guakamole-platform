from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

UserListSortField = Literal[
    "email",
    "first_name",
    "last_name",
    "create_at",
    "last_login_at",
    "id_user",
]
SortDirection = Literal["asc", "desc"]


class UserBase(BaseModel):
    """Campos base públicos/controlados de un usuario IAM."""

    id_organization: int
    id_platform_role: int
    id_country: int
    id_state: int
    id_city: int
    id_org_role: int
    id_status: int
    email: str = Field(..., max_length=254)
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=150)
    birthdate: date
    user_address: str = Field(..., max_length=255)
    user_zipcode: str = Field(..., max_length=20)


class UserCreate(UserBase):
    """Datos necesarios para crear un usuario IAM."""

    password_hash: str = Field(..., max_length=255)


class UserUpdate(BaseModel):
    """Datos opcionales para actualizar parcialmente un usuario IAM."""

    id_organization: int | None = None
    id_platform_role: int | None = None
    id_country: int | None = None
    id_state: int | None = None
    id_city: int | None = None
    id_org_role: int | None = None
    id_status: int | None = None
    email: str | None = Field(default=None, max_length=254)
    password_hash: str | None = Field(default=None, max_length=255)
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=150)
    birthdate: date | None = None
    user_address: str | None = Field(default=None, max_length=255)
    user_zipcode: str | None = Field(default=None, max_length=20)
    last_login_at: datetime | None = None


class UserRead(UserBase):
    """Representación de lectura de un usuario IAM sin hash de contraseña."""

    model_config = ConfigDict(from_attributes=True)

    id_user: int
    created_at: datetime
    updated_at: datetime | None
    last_login_at: datetime | None


class UserListQuery(BaseModel):
    """Parámetros seguros para listar usuarios de una organización."""

    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    search: str | None = Field(default=None, max_length=100)
    sort_by: UserListSortField = "email"
    sort_dir: SortDirection = "asc"

    @field_validator("search")
    @classmethod
    def normalize_search(cls, value: str | None) -> str | None:
        """Normaliza búsquedas vacías para evitar filtros ambiguos."""

        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class OrganizationUserRead(BaseModel):
    """Usuario visible en el listado de una organización sin datos sensibles."""

    model_config = ConfigDict(from_attributes=True)

    id_user: int
    id_organization: int
    email: str = Field(..., max_length=254)
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=150)
    id_status: int
    id_platform_role: int
    id_org_role: int
    created_at: datetime
    updated_at: datetime | None
    last_login_at: datetime | None


class OrganizationUserListResponse(BaseModel):
    """Respuesta paginada del listado de usuarios de organización."""

    items: list[OrganizationUserRead]
    limit: int
    offset: int
    total: int | None = None
