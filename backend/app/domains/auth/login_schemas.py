"""Schemas HTTP y DTOs internos del login."""

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LoginRequest(BaseModel):
    """Credenciales de login validadas en servidor."""

    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)

    model_config = ConfigDict(extra="forbid")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized_email = value.strip().lower()
        if "@" not in normalized_email:
            raise ValueError("email inválido")
        return normalized_email


class LoginResponse(BaseModel):
    """Respuesta pública del login, sin token ni datos internos."""

    status: str = "authenticated"

    model_config = ConfigDict(extra="forbid")


@dataclass(frozen=True, slots=True)
class LoginTokenData:
    """Resultado interno autenticado para que el router emita la cookie."""

    access_token: str
    user_public_id: str
    organization_public_id: str
