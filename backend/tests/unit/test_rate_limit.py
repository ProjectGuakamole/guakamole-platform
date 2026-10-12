"""Tests unitarios del rate limiter in-memory."""

from concurrent.futures import ThreadPoolExecutor

import pytest

from app.core.rate_limit import InMemoryRateLimiter, RateLimitRule

pytestmark = pytest.mark.test_unit


class ManualClock:
    def __init__(self) -> None:
        self.current = 0.0

    def __call__(self) -> float:
        return self.current

    def advance(self, seconds: float) -> None:
        self.current += seconds


def test_limiter_allows_requests_within_limit() -> None:
    limiter = InMemoryRateLimiter(clock=ManualClock())
    rule = RateLimitRule(scope="auth_login", max_requests=2, window_seconds=60)

    assert limiter.check("ip-route", rule).allowed is True
    assert limiter.check("ip-route", rule).allowed is True


def test_limiter_blocks_when_limit_is_exceeded() -> None:
    limiter = InMemoryRateLimiter(clock=ManualClock())
    rule = RateLimitRule(scope="auth_login", max_requests=1, window_seconds=60)

    assert limiter.check("ip-route", rule).allowed is True
    decision = limiter.check("ip-route", rule)

    assert decision.allowed is False
    assert decision.retry_after_seconds == 60


def test_limiter_allows_again_after_window_expires_without_sleep() -> None:
    clock = ManualClock()
    limiter = InMemoryRateLimiter(clock=clock)
    rule = RateLimitRule(scope="auth_login", max_requests=1, window_seconds=60)

    assert limiter.check("ip-route", rule).allowed is True
    assert limiter.check("ip-route", rule).allowed is False

    clock.advance(60)

    assert limiter.check("ip-route", rule).allowed is True


def test_limiter_separates_keys_by_ip_and_route() -> None:
    limiter = InMemoryRateLimiter(clock=ManualClock())
    rule = RateLimitRule(scope="auth_login", max_requests=1, window_seconds=60)

    assert limiter.check("auth_login:/login:10.0.0.1", rule).allowed is True
    assert limiter.check("auth_login:/login:10.0.0.1", rule).allowed is False
    assert limiter.check("auth_login:/login:10.0.0.2", rule).allowed is True
    assert limiter.check("auth_login:/token:10.0.0.1", rule).allowed is True


def test_limiter_allows_exact_limit_under_concurrent_access() -> None:
    max_requests = 5
    attempted_requests = 20
    limiter = InMemoryRateLimiter(clock=ManualClock())
    rule = RateLimitRule(
        scope="auth_login",
        max_requests=max_requests,
        window_seconds=60,
    )

    def check_same_key(_: int) -> bool:
        return limiter.check("auth_login:/login:testclient", rule).allowed

    with ThreadPoolExecutor(max_workers=attempted_requests) as executor:
        results = list(executor.map(check_same_key, range(attempted_requests)))

    assert results.count(True) == max_requests
    assert results.count(False) == attempted_requests - max_requests
