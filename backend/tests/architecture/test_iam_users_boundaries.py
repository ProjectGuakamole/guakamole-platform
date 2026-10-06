"""Tests de límites arquitectónicos del piloto IAM/users."""

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
IAM_USERS_PACKAGE = PROJECT_ROOT / "app" / "domain" / "iam" / "users"

ROUTERS_MODULE = IAM_USERS_PACKAGE / "routers.py"
MODELS_MODULE = IAM_USERS_PACKAGE / "models.py"
SERVICES_MODULE = IAM_USERS_PACKAGE / "services.py"
POLICIES_MODULE = IAM_USERS_PACKAGE / "policies.py"
REPOSITORIES_MODULE = IAM_USERS_PACKAGE / "repositories.py"
DEPENDENCIES_MODULE = IAM_USERS_PACKAGE / "dependencies.py"

SQLALCHEMY_IMPORTS = frozenset(("sqlalchemy",))
FASTAPI_IMPORTS = frozenset(("fastapi",))
ROUTER_FORBIDDEN_INFRA_IMPORTS = frozenset(
    (
        "docker",
        "github",
        "guacamole",
        "app.domain.iam.users.repositories",
        "app.integrations",
        "app.labs",
        "app.domain.labs",
        "app.domain.content",
        "app.content",
    )
)
MODEL_FORBIDDEN_UPPER_LAYER_IMPORTS = frozenset(
    (
        "app.domain.iam.users.dependencies",
        "app.domain.iam.users.policies",
        "app.domain.iam.users.repositories",
        "app.domain.iam.users.routers",
        "app.domain.iam.users.services",
    )
)


def imported_modules(module_path: Path) -> set[str]:
    """Devuelve los módulos importados mediante AST, sin leer comentarios/docstrings."""
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)

    return modules


def assert_no_imports_with_prefix(
    *,
    module_path: Path,
    forbidden_prefixes: frozenset[str],
) -> None:
    """Comprueba que el módulo no importa paquetes prohibidos por prefijo."""
    imports = imported_modules(module_path)
    forbidden = sorted(
        imported
        for imported in imports
        for prefix in forbidden_prefixes
        if imported == prefix or imported.startswith(f"{prefix}.")
    )

    assert forbidden == []


def test_router_does_not_import_sqlalchemy_or_repository_directly() -> None:
    """El router HTTP no debe saltarse dependencies/service hacia persistencia."""
    assert_no_imports_with_prefix(
        module_path=ROUTERS_MODULE,
        forbidden_prefixes=SQLALCHEMY_IMPORTS
        | frozenset(("app.domain.iam.users.repositories",)),
    )


def test_router_does_not_import_lab_content_or_external_integrations() -> None:
    """El router no debe mezclar infraestructura de labs, contenido o integraciones."""
    assert_no_imports_with_prefix(
        module_path=ROUTERS_MODULE,
        forbidden_prefixes=ROUTER_FORBIDDEN_INFRA_IMPORTS,
    )


def test_models_do_not_import_upper_layers() -> None:
    """Los modelos ORM no deben depender de capas superiores del subdominio."""
    assert_no_imports_with_prefix(
        module_path=MODELS_MODULE,
        forbidden_prefixes=MODEL_FORBIDDEN_UPPER_LAYER_IMPORTS,
    )


def test_services_and_policies_do_not_import_fastapi_or_sqlalchemy() -> None:
    """Service y policy deben permanecer libres de HTTP y ORM directo."""
    forbidden_prefixes = FASTAPI_IMPORTS | SQLALCHEMY_IMPORTS

    assert_no_imports_with_prefix(
        module_path=SERVICES_MODULE,
        forbidden_prefixes=forbidden_prefixes,
    )
    assert_no_imports_with_prefix(
        module_path=POLICIES_MODULE,
        forbidden_prefixes=forbidden_prefixes,
    )


def test_repositories_do_not_import_fastapi() -> None:
    """El adapter de persistencia puede usar SQLAlchemy, pero no FastAPI."""
    assert_no_imports_with_prefix(
        module_path=REPOSITORIES_MODULE,
        forbidden_prefixes=FASTAPI_IMPORTS,
    )


def test_dependencies_module_is_http_infra_boundary() -> None:
    """Dependencies actúa como frontera HTTP/infra.

    Por ello puede importar FastAPI y SQLAlchemy sin romper estos límites,
    pero esos imports no son obligatorios si futuras iteraciones desacoplan
    todavía más esta frontera.
    """

    assert DEPENDENCIES_MODULE.is_file()
    imported_modules(DEPENDENCIES_MODULE)
