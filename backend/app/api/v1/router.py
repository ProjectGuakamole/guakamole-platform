from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.domain.auth.login_routers import router as login_router
from app.domain.auth.me_routers import router as auth_me_router
from app.domain.iam.organizations.registration_routers import (
    router as registration_router,
)
from app.domain.iam.users.routers import router as iam_users_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(login_router, prefix="/auth", tags=["auth"])
api_router.include_router(auth_me_router, prefix="/auth", tags=["auth"])
api_router.include_router(iam_users_router, prefix="/iam", tags=["iam-users"])
api_router.include_router(
    registration_router, prefix="/organizations", tags=["organizations"]
)
