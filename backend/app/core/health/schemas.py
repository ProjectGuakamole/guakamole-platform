from enum import StrEnum

from pydantic import BaseModel


class HealthStatus(StrEnum):
    OK = "ok"


class ReadinessStatus(StrEnum):
    READY = "ready"
    NOT_READY = "not_ready"


class DependencyStatus(StrEnum):
    OK = "ok"
    FAILED = "failed"


class HealthResponse(BaseModel):
    status: HealthStatus


class ReadinessDependencies(BaseModel):
    database: DependencyStatus


class ReadinessResponse(BaseModel):
    status: ReadinessStatus
    dependencies: ReadinessDependencies
