from collections import Counter
from collections.abc import Sequence
from typing import Protocol, cast

import pytest
from fastapi import APIRouter
from fastapi.routing import APIRoute
from starlette.routing import BaseRoute

from app.main import app

pytestmark = pytest.mark.architecture


class RouterIncludeContext(Protocol):
    prefix: str


class IncludedRouterRoute(Protocol):
    original_router: APIRouter
    include_context: RouterIncludeContext


def openapi_methods_by_path() -> dict[str, set[str]]:
    openapi_schema = app.openapi()
    paths = cast(dict[str, dict[str, object]], openapi_schema["paths"])
    return {path: set(operations) for path, operations in paths.items()}


def iter_route_method_pairs(
    routes: Sequence[BaseRoute], prefix: str = ""
) -> list[tuple[str, str]]:
    route_method_pairs: list[tuple[str, str]] = []

    for route in routes:
        if isinstance(route, APIRoute):
            methods = route.methods or set()
            route_method_pairs.extend(
                (f"{prefix}{route.path}", method.upper()) for method in methods
            )
            continue

        if hasattr(route, "original_router") and hasattr(route, "include_context"):
            included_route = cast(IncludedRouterRoute, route)
            route_method_pairs.extend(
                iter_route_method_pairs(
                    included_route.original_router.routes,
                    f"{prefix}{included_route.include_context.prefix}",
                )
            )

    return route_method_pairs


def api_v1_route_method_occurrences() -> Counter[tuple[str, str]]:
    occurrences: Counter[tuple[str, str]] = Counter()

    for path, method in iter_route_method_pairs(app.routes):
        if not path.startswith("/api/v1/"):
            continue

        occurrences[(path, method)] += 1

    return occurrences


def test_api_v1_public_contract_routes_are_mounted_once() -> None:
    routes = openapi_methods_by_path()
    route_occurrences = api_v1_route_method_occurrences()
    expected_routes = {
        "/api/v1/health": "GET",
        "/api/v1/organizations/register": "POST",
        "/api/v1/iam/organizations/{organization_id}/users": "GET",
        "/api/v1/auth/login": "POST",
        "/api/v1/auth/logout": "POST",
        "/api/v1/auth/me": "GET",
        "/api/v1/auth/csrf": "GET",
        "/api/v1/auth/token": "POST",
    }

    for path, method in expected_routes.items():
        assert routes[path] == {method.lower()}
        assert route_occurrences[(path, method)] == 1


def test_api_v1_is_the_only_versioned_public_mount() -> None:
    route_occurrences = api_v1_route_method_occurrences()
    duplicated_routes = {
        route: count for route, count in route_occurrences.items() if count > 1
    }

    assert duplicated_routes == {}
