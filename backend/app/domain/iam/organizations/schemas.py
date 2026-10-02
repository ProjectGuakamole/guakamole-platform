from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrganizationBase(BaseModel):
    """Campos base de una organización IAM."""

    id_country: int
    id_state: int
    id_city: int
    id_status: int
    name: str = Field(..., max_length=150)
    slug: str = Field(..., max_length=120)
    org_registered_name: str | None = Field(default=None, max_length=200)
    org_tax: str | None = Field(default=None, max_length=32)
    org_address: str = Field(..., max_length=255)
    org_zipcode: str = Field(..., max_length=20)


class OrganizationCreate(OrganizationBase):
    """Datos necesarios para crear una organización."""


class OrganizationUpdate(BaseModel):
    """Datos opcionales para actualizar parcialmente una organización."""

    id_country: int | None = None
    id_state: int | None = None
    id_city: int | None = None
    id_status: int | None = None
    name: str | None = Field(default=None, max_length=150)
    slug: str | None = Field(default=None, max_length=120)
    org_registered_name: str | None = Field(default=None, max_length=200)
    org_tax: str | None = Field(default=None, max_length=32)
    org_address: str | None = Field(default=None, max_length=255)
    org_zipcode: str | None = Field(default=None, max_length=20)


class OrganizationRead(OrganizationBase):
    """Representación de lectura de una organización."""

    model_config = ConfigDict(from_attributes=True)

    id_organization: int
    created_at: datetime
    updated_at: datetime | None
