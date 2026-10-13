from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.domains.auth.router import router as auth_router
from app.domains.iam.registration.router import (
    router as registration_router,
)

api_v1_router = APIRouter()
api_v1_router.include_router(health_router, prefix="/health", tags=["health"])
api_v1_router.include_router(auth_router)
api_v1_router.include_router(
    registration_router, prefix="/organizations", tags=["organizations"]
)
