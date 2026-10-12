"""Schemas públicos para OAuth2 Password Bearer de desarrollo."""

from pydantic import BaseModel, ConfigDict, Field


class PasswordBearerTokenResponse(BaseModel):
    """Respuesta OAuth2 compatible con Swagger sin datos sensibles."""

    access_token: str = Field(min_length=1)
    token_type: str = "bearer"  # noqa: S105 - Valor estándar OAuth2, no es secreto.
    expires_in: int = Field(gt=0)

    model_config = ConfigDict(extra="forbid")
