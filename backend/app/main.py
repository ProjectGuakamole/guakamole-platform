from fastapi import FastAPI

from app.api.health import router as operational_health_router
from app.api.v1.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Guakamole Backend",
        version="0.1.0",
    )
    app.include_router(operational_health_router, prefix="/api")
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
