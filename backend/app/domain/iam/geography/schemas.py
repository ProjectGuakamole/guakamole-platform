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


class StateBase(BaseModel):
    """Campos base del catálogo de estados o provincias."""

    id_country: int
    state_name: str = Field(..., max_length=100)


class StateCreate(StateBase):
    """Datos necesarios para crear un estado o provincia."""


class StateUpdate(BaseModel):
    """Datos opcionales para actualizar parcialmente un estado o provincia."""

    id_country: int | None = None
    state_name: str | None = Field(default=None, max_length=100)


class StateRead(StateBase):
    """Representación de lectura de un estado o provincia."""

    model_config = ConfigDict(from_attributes=True)

    id_state: int


class CityBase(BaseModel):
    """Campos base del catálogo de ciudades."""

    id_state: int
    city_name: str = Field(..., max_length=120)


class CityCreate(CityBase):
    """Datos necesarios para crear una ciudad."""


class CityUpdate(BaseModel):
    """Datos opcionales para actualizar parcialmente una ciudad."""

    id_state: int | None = None
    city_name: str | None = Field(default=None, max_length=120)


class CityRead(CityBase):
    """Representación de lectura de una ciudad."""

    model_config = ConfigDict(from_attributes=True)

    id_city: int
