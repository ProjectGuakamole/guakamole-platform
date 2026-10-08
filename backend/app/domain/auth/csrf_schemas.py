"""Schemas HTTP para CSRF."""

from pydantic import BaseModel, ConfigDict


class CsrfTokenResponse(BaseModel):
    """Respuesta pública con token CSRF firmado."""

    csrf_token: str

    model_config = ConfigDict(extra="forbid")
