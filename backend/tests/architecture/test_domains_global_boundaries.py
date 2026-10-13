"""Reglas AST comunes para las capas de todos los dominios existentes."""

import ast
from collections.abc import Iterable
from pathlib import Path

import pytest

pytestmark = pytest.mark.architecture

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOMAINS_ROOT = PROJECT_ROOT / "app" / "domains"
ROUTER_NAMES = frozenset({"router", "routers"})
SERVICE_NAMES = frozenset({"service", "services"})
REPOSITORY_NAMES = frozenset({"repository", "repositories"})
POLICY_NAMES = frozenset({"policy", "policies"})
MODEL_NAMES = frozenset({"model", "models"})


def domain_modules() -> tuple[Path, ...]:
    """Obtiene módulos Python de los dominios sin depender de imports runtime."""

    return tuple(sorted(DOMAINS_ROOT.rglob("*.py")))


def imported_modules(module_path: Path) -> set[str]:
    """Extrae imports absolutos desde el AST del módulo indicado."""

    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module)
    return imports


def module_stem(module_path: Path) -> str:
    return module_path.stem


def relative_module_parts(module_path: Path) -> tuple[str, ...]:
    return module_path.relative_to(DOMAINS_ROOT).with_suffix("").parts


def has_prefix(module: str, prefixes: Iterable[str]) -> bool:
    return any(
        module == prefix or module.startswith(f"{prefix}.") for prefix in prefixes
    )


def assert_no_import_prefixes(module_path: Path, prefixes: Iterable[str]) -> None:
    forbidden = sorted(
        imported
        for imported in imported_modules(module_path)
        if has_prefix(imported, prefixes)
    )
    assert forbidden == [], f"{module_path.relative_to(PROJECT_ROOT)}: {forbidden}"


def test_domain_layers_respect_framework_and_persistence_boundaries() -> None:
    """Impide que las capas de dominio salten sus fronteras técnicas."""

    for module_path in domain_modules():
        stem = module_stem(module_path)
        if stem in ROUTER_NAMES:
            assert_no_import_prefixes(module_path, ("sqlalchemy",))
            assert_no_repository_imports(module_path)
        elif stem in SERVICE_NAMES | POLICY_NAMES:
            assert_no_import_prefixes(module_path, ("fastapi", "sqlalchemy"))
        elif stem in REPOSITORY_NAMES:
            assert_no_import_prefixes(module_path, ("fastapi",))
        elif stem in MODEL_NAMES:
            assert_no_import_prefixes(module_path, ("fastapi",))
            assert_no_layer_imports(module_path, ROUTER_NAMES | SERVICE_NAMES)


def assert_no_repository_imports(module_path: Path) -> None:
    forbidden = sorted(
        imported
        for imported in imported_modules(module_path)
        if any(part in REPOSITORY_NAMES for part in imported.split("."))
    )
    assert forbidden == [], f"{module_path.relative_to(PROJECT_ROOT)}: {forbidden}"


def assert_no_layer_imports(module_path: Path, layer_names: frozenset[str]) -> None:
    forbidden = sorted(
        imported
        for imported in imported_modules(module_path)
        if any(part in layer_names for part in imported.split("."))
    )
    assert forbidden == [], f"{module_path.relative_to(PROJECT_ROOT)}: {forbidden}"


def test_domain_init_modules_are_minimal() -> None:
    """Los paquetes no deben ocultar composición o lógica mediante reexports."""

    for module_path in domain_modules():
        if module_stem(module_path) != "__init__":
            continue
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        statements = [
            statement
            for statement in tree.body
            if not (
                isinstance(statement, ast.Expr)
                and isinstance(statement.value, ast.Constant)
                and isinstance(statement.value.value, str)
            )
        ]
        assert statements == [], f"{module_path.relative_to(PROJECT_ROOT)} no es mínimo"


def test_domains_do_not_use_legacy_singular_package() -> None:
    """Evita reintroducir el paquete obsoleto ``app.domain``."""

    for module_path in domain_modules():
        assert_no_import_prefixes(module_path, ("app.domain",))


def test_http_composition_does_not_cross_domain_boundaries() -> None:
    """Impide importar routers o dependencies HTTP de otro dominio funcional."""

    for module_path in domain_modules():
        source_parts = relative_module_parts(module_path)
        source_domain = source_parts[0]
        source_is_domain_router = (
            module_stem(module_path) in ROUTER_NAMES and len(source_parts) == 2
        )
        for imported in imported_modules(module_path):
            target_parts = imported.split(".")
            if target_parts[:2] != ["app", "domains"] or len(target_parts) < 4:
                continue
            target_domain = target_parts[2]
            target_is_shared = "shared" in target_parts[3:]
            target_is_http_composition = any(
                part in ROUTER_NAMES | {"dependencies"} for part in target_parts[3:]
            )
            if (
                target_is_http_composition
                and target_domain != source_domain
                and not target_is_shared
            ):
                pytest.fail(
                    f"{module_path.relative_to(PROJECT_ROOT)} importa composición HTTP "
                    f"de otro dominio: {imported}"
                )
            target_is_router = any(part in ROUTER_NAMES for part in target_parts[3:])
            if (
                target_is_router
                and target_domain == source_domain
                and not source_is_domain_router
            ):
                pytest.fail(
                    f"{module_path.relative_to(PROJECT_ROOT)} "
                    "importa un router sibling: "
                    f"{imported}"
                )
