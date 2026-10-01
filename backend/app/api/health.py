from fastapi import APIRouter, Response, status

from app.core.health.checks import get_readiness_status
from app.core.health.schemas import (
    HealthResponse,
    HealthStatus,
    ReadinessResponse,
    ReadinessStatus,
)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status=HealthStatus.OK)


@router.get("/ready", response_model=ReadinessResponse)
def readiness_check(response: Response) -> ReadinessResponse:
    readiness = get_readiness_status()
    if readiness.status is ReadinessStatus.NOT_READY:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return readiness
