from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: Literal["ok"]


@router.get("", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")
