from pydantic import BaseModel, ConfigDict, Field


class CountryBase(BaseModel):
    """Campos base del catálogo de países."""

    country_name: str = Field(..., max_length=100)


class CountryCreate(CountryBase):
    """Datos necesarios para crear un país."""


class CountryUpdate(BaseModel):
    """Datos opcionales para actualizar parcialmente un país."""

    country_name: str | None = Field(default=None, max_length=100)


class CountryRead(CountryBase):
    """Representación de lectura de un país."""

    model_config = ConfigDict(from_attributes=True)

    id_country: int
