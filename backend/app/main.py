from fastapi import FastAPI

from app.api.health import router as operational_health_router
from app.api.v1.router import api_v1_router
from app.core.cors import configure_cors
from app.domains.auth.config import CorsSettings


def create_app() -> FastAPI:
    app = FastAPI(
        title="Guakamole Backend",
        version="0.1.0",
    )
    configure_cors(app, CorsSettings())
    app.include_router(operational_health_router, prefix="/api")
    app.include_router(api_v1_router, prefix="/api/v1")
    return app


app = create_app()
