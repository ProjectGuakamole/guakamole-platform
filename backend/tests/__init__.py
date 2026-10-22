"""Paquete de pruebas del backend."""

import os

# Configuración sintética para imports de módulos que exponen la aplicación ASGI.
# Cada test puede sustituirla mediante monkeypatch; nunca se lee un .env real.
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://test:test@localhost/test_db"
)
os.environ.setdefault(
    "JWT_SECRET_KEY", "test-secret-not-for-production-with-safe-length"
)
