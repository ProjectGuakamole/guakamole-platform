"""Schemas públicos para GET /auth/me."""

from pydantic import BaseModel, ConfigDict


class AuthMeResponse(BaseModel):
    """Identidad pública mínima de la sesión autenticada."""

    authenticated: bool
    user_id: str
    organization_id: str

    model_config = ConfigDict(extra="forbid")
