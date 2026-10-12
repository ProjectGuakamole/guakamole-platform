"""Agregador de rutas del dominio de autenticación."""

from fastapi import APIRouter

from app.domains.auth.csrf.router import router as csrf_router
from app.domains.auth.login.router import router as login_router
from app.domains.auth.logout.router import router as logout_router
from app.domains.auth.me.router import router as me_router
from app.domains.auth.token.router import router as token_router

router = APIRouter(prefix="/auth", tags=["auth"])
router.include_router(csrf_router)
router.include_router(login_router)
router.include_router(logout_router)
router.include_router(me_router)
router.include_router(token_router)
