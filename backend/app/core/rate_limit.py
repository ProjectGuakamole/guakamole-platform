"""Rate limiting básico in-memory para endpoints públicos sensibles."""

from collections.abc import Callable
from dataclasses import dataclass
from threading import Lock
from time import monotonic
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from app.core.config import Settings, get_settings

RATE_LIMIT_EXCEEDED_DETAIL = "Demasiadas solicitudes. Inténtalo más tarde."


RateLimitSettings = Settings


@dataclass(frozen=True, slots=True)
class RateLimitRule:
    """Regla de ventana fija para una familia de endpoint."""

    scope: str
    max_requests: int
    window_seconds: int


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    """Resultado de evaluar una petición contra el rate limiter."""

    allowed: bool
    retry_after_seconds: int | None = None


@dataclass(slots=True)
class _Bucket:
    window_started_at: float
    requests: int


class InMemoryRateLimiter:
    """Rate limiter in-memory con ventana fija simple.

    Implementación apta para MVP/dev. No debe considerarse distribuida ni válida
    para múltiples procesos; se sustituirá por Redis más adelante.
    """

    def __init__(self, clock: Callable[[], float] = monotonic) -> None:
        self._clock = clock
        self._buckets: dict[str, _Bucket] = {}
        self._lock = Lock()

    def check(self, key: str, rule: RateLimitRule) -> RateLimitDecision:
        with self._lock:
            now = self._clock()
            bucket = self._buckets.get(key)
            if bucket is None or now - bucket.window_started_at >= rule.window_seconds:
                self._buckets[key] = _Bucket(window_started_at=now, requests=1)
                return RateLimitDecision(allowed=True)

            if bucket.requests >= rule.max_requests:
                retry_after = int(
                    rule.window_seconds - (now - bucket.window_started_at),
                )
                return RateLimitDecision(
                    allowed=False,
                    retry_after_seconds=max(retry_after, 1),
                )

            bucket.requests += 1
            return RateLimitDecision(allowed=True)

    def reset(self) -> None:
        """Limpia estado para tests o reinicios controlados."""

        with self._lock:
            self._buckets.clear()


_rate_limiter = InMemoryRateLimiter()


def get_rate_limit_settings() -> RateLimitSettings:
    return get_settings()


def get_rate_limiter() -> InMemoryRateLimiter:
    return _rate_limiter


def reset_rate_limiter_state() -> None:
    """Helper controlado para aislar tests del singleton in-memory."""

    _rate_limiter.reset()


def _build_key(request: Request, scope: str) -> str:
    client_host = request.client.host if request.client is not None else "unknown"
    return f"{scope}:{request.url.path}:{client_host}"


def _require_rate_limit(
    request: Request,
    rule: RateLimitRule,
    settings: RateLimitSettings,
    limiter: InMemoryRateLimiter,
) -> None:
    if not settings.rate_limit_enabled:
        return

    decision = limiter.check(_build_key(request, rule.scope), rule)
    if decision.allowed:
        return

    headers: dict[str, str] = {}
    if decision.retry_after_seconds is not None:
        headers["Retry-After"] = str(decision.retry_after_seconds)
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=RATE_LIMIT_EXCEEDED_DETAIL,
        headers=headers,
    )


def require_auth_login_rate_limit(
    request: Request,
    settings: Annotated[RateLimitSettings, Depends(get_rate_limit_settings)],
    limiter: Annotated[InMemoryRateLimiter, Depends(get_rate_limiter)],
) -> None:
    rule = RateLimitRule(
        scope="auth_login",
        max_requests=settings.auth_login_rate_limit_requests,
        window_seconds=settings.auth_login_rate_limit_window_seconds,
    )
    _require_rate_limit(request, rule, settings, limiter)


def require_auth_token_rate_limit(
    request: Request,
    settings: Annotated[RateLimitSettings, Depends(get_rate_limit_settings)],
    limiter: Annotated[InMemoryRateLimiter, Depends(get_rate_limiter)],
) -> None:
    rule = RateLimitRule(
        scope="auth_token",
        max_requests=settings.auth_token_rate_limit_requests,
        window_seconds=settings.auth_token_rate_limit_window_seconds,
    )
    _require_rate_limit(request, rule, settings, limiter)


def require_registration_rate_limit(
    request: Request,
    settings: Annotated[RateLimitSettings, Depends(get_rate_limit_settings)],
    limiter: Annotated[InMemoryRateLimiter, Depends(get_rate_limiter)],
) -> None:
    rule = RateLimitRule(
        scope="registration",
        max_requests=settings.registration_rate_limit_requests,
        window_seconds=settings.registration_rate_limit_window_seconds,
    )
    _require_rate_limit(request, rule, settings, limiter)
