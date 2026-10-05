from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DepartmentBase(BaseModel):
    """Campos base de un departamento IAM."""

    id_organization: int
    name: str = Field(..., max_length=150)
    description: str | None = None


class DepartmentCreate(DepartmentBase):
    """Datos necesarios para crear un departamento IAM."""


class DepartmentUpdate(BaseModel):
    """Datos opcionales para actualizar parcialmente un departamento IAM."""

    id_organization: int | None = None
    name: str | None = Field(default=None, max_length=150)
    description: str | None = None


class DepartmentRead(DepartmentBase):
    """Representación de lectura de un departamento IAM."""

    model_config = ConfigDict(from_attributes=True)

    id_department: int
    created_at: datetime
    updated_at: datetime | None


class DepartmentRelationBase(BaseModel):
    """Campos base de una relación departamento-usuario IAM."""

    id_department: int
    id_user: int


class DepartmentRelationCreate(DepartmentRelationBase):
    """Datos necesarios para crear una relación departamento-usuario IAM."""


class DepartmentRelationUpdate(BaseModel):
    """Datos opcionales para actualizar parcialmente una relación IAM."""

    id_department: int | None = None
    id_user: int | None = None


class DepartmentRelationRead(DepartmentRelationBase):
    """Representación de lectura de una relación departamento-usuario IAM."""

    model_config = ConfigDict(from_attributes=True)

    id_department_relation: int
    created_at: datetime
    updated_at: datetime | None
