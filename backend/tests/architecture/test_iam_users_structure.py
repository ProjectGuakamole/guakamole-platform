"""Tests de estructura mínima del subdominio IAM/users."""

from collections.abc import Iterator
from importlib import import_module
from types import ModuleType

IAM_USERS_MODULES: tuple[str, ...] = (
    "app.domain.iam.users.routers",
    "app.domain.iam.users.schemas",
    "app.domain.iam.users.services",
    "app.domain.iam.users.policies",
    "app.domain.iam.users.repositories",
    "app.domain.iam.users.dependencies",
)


def iter_iam_users_modules() -> Iterator[ModuleType]:
    """Importa los módulos esperados del scaffolding IAM/users."""
    for module_path in IAM_USERS_MODULES:
        yield import_module(module_path)


def test_iam_users_scaffolding_modules_are_importable() -> None:
    """La estructura mínima de IAM/users debe ser importable."""
    imported_modules = tuple(iter_iam_users_modules())

    assert tuple(module.__name__ for module in imported_modules) == IAM_USERS_MODULES


def test_iam_users_scaffolding_does_not_expose_functional_router() -> None:
    """Task 1 no debe añadir router/endpoints funcionales todavía."""
    routers_module = import_module("app.domain.iam.users.routers")

    assert not hasattr(routers_module, "router")
