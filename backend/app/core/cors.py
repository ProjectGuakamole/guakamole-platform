"""Configuración CORS segura para la API FastAPI."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.domains.auth.config import CorsSettings

ALLOWED_CORS_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
BASE_ALLOWED_CORS_HEADERS = ["Content-Type", "X-CSRF-Token"]


def build_allowed_cors_headers(settings: CorsSettings) -> list[str]:
    """Construye la lista explícita de headers permitidos por CORS."""

    headers = BASE_ALLOWED_CORS_HEADERS.copy()
    if settings.cors_allow_authorization_header:
        headers.append("Authorization")
    return headers


def configure_cors(app: FastAPI, settings: CorsSettings) -> None:
    """Registra CORSMiddleware sin wildcards y con origins explícitos."""

    if "*" in settings.cors_allowed_origins:
        msg = "CORS no permite '*' como origin permitido."
        raise ValueError(msg)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=ALLOWED_CORS_METHODS,
        allow_headers=build_allowed_cors_headers(settings),
    )
