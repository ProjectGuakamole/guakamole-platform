from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StatusBase(BaseModel):
    """Campos base del catálogo de estados IAM."""

    status: str = Field(..., max_length=50)


class StatusCreate(StatusBase):
    """Datos necesarios para crear un estado IAM."""


class StatusUpdate(BaseModel):
    """Datos opcionales para actualizar parcialmente un estado IAM."""

    status: str | None = Field(default=None, max_length=50)


class StatusRead(StatusBase):
    """Representación de lectura de un estado IAM."""

    model_config = ConfigDict(from_attributes=True)

    id_status: int
    created_at: datetime
    updated_at: datetime | None


class PlatformRoleBase(BaseModel):
    """Campos base de un rol global de plataforma."""

    platform_role_type: str = Field(..., max_length=50)
    description: str | None = None


class PlatformRoleCreate(PlatformRoleBase):
    """Datos necesarios para crear un rol global de plataforma."""


class PlatformRoleUpdate(BaseModel):
    """Datos opcionales para actualizar parcialmente un rol de plataforma."""

    platform_role_type: str | None = Field(default=None, max_length=50)
    description: str | None = None


class PlatformRoleRead(PlatformRoleBase):
    """Representación de lectura de un rol global de plataforma."""

    model_config = ConfigDict(from_attributes=True)

    id_platform_role: int
    created_at: datetime
    updated_at: datetime | None


class OrganizationRoleBase(BaseModel):
    """Campos base de un rol organizativo."""

    org_role_type: str = Field(..., max_length=50)


class OrganizationRoleCreate(OrganizationRoleBase):
    """Datos necesarios para crear un rol organizativo."""


class OrganizationRoleUpdate(BaseModel):
    """Datos opcionales para actualizar parcialmente un rol organizativo."""

    org_role_type: str | None = Field(default=None, max_length=50)


class OrganizationRoleRead(OrganizationRoleBase):
    """Representación de lectura de un rol organizativo."""

    model_config = ConfigDict(from_attributes=True)

    id_org_role: int
    created_at: datetime
    updated_at: datetime | None
