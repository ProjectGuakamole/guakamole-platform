from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


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
