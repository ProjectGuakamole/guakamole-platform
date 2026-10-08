"""Schemas HTTP para cierre de sesión."""

from pydantic import BaseModel, ConfigDict


class LogoutResponse(BaseModel):
    """Respuesta pública mínima del logout."""

    status: str = "logged_out"

    model_config = ConfigDict(extra="forbid")
