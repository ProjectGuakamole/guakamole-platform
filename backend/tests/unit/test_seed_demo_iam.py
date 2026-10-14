"""Contratos de seguridad de fixture y destino del seed demo IAM."""

from __future__ import annotations

import copy
import json
from collections.abc import Callable
from pathlib import Path

import pytest

from app.core.iam_rebaseline import validate_safe_target
from app.domains.auth.shared.public_ids import PublicIdPrefix, parse_public_uuid
from scripts.seed_demo_iam import (
    FIXTURE_PATH,
    Fixture,
    _is_managed_public_id,
    _public_id,
    load_fixture,
    validate_fixture,
)

pytestmark = pytest.mark.test_unit


def test_fixture_contiene_solo_datos_de_negocio_demo() -> None:
    fixture = load_fixture()
    assert (
        len(fixture["organizations"]),
        len(fixture["users"]),
        len(fixture["departments"]),
        len(fixture["department_relations"]),
    ) == (6, 8, 8, 8)
    assert "password" not in FIXTURE_PATH.read_text(encoding="utf-8").lower()


@pytest.mark.parametrize("prefix", ["org", "usr"])
def test_public_id_demo_cabe_en_la_columna(prefix: str) -> None:
    public_id = _public_id(prefix, "demo-natural-key")

    assert public_id.startswith(f"{prefix}_")
    assert "demo" not in public_id
    assert len(public_id) <= 40
    assert parse_public_uuid(public_id, PublicIdPrefix(prefix))


@pytest.mark.parametrize("prefix", ["org", "usr"])
def test_public_id_demo_es_determinista_desde_la_clave_estable(prefix: str) -> None:
    assert _public_id(prefix, "stable@example.demo.test") == _public_id(
        prefix, "stable@example.demo.test"
    )
    assert _public_id(prefix, "stable@example.demo.test") != _public_id(
        prefix, "other@example.demo.test"
    )


@pytest.mark.parametrize(
    ("prefix", "public_id"),
    [
        ("org", _public_id("org", "demo-natural-key")),
        ("usr", _public_id("usr", "demo-natural-key")),
        ("org", _public_id("usr", "demo-natural-key")),
        ("org", _public_id("org", "other-demo-natural-key")),
        ("org", "org_abcdefghijklmnopqrstu"),
        ("org", "org_abcdefghijklmnopqrstuv!"),
        ("usr", "usr_" + "a" * 41),
    ],
)
def test_id_publico_demo_exige_formato_y_tipo_exactos(
    prefix: str, public_id: str
) -> None:
    assert _is_managed_public_id(prefix, "demo-natural-key", public_id) is (
        public_id == _public_id(prefix, "demo-natural-key")
    )


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda data: data["organizations"].append(data["organizations"][0]), "6/8"),
        (
            lambda data: data["users"].__setitem__(
                0, {**data["users"][0], "organization_slug": "missing"}
            ),
            "referencias",
        ),
        (
            lambda data: data["departments"].__setitem__(
                0, {**data["departments"][0], "name": "SOC"}
            ),
            "espacio demo",
        ),
        (
            lambda data: data["department_relations"].__setitem__(
                0,
                {
                    "department_name": "Demo SOC L1",
                    "user_email": "julia.cyber@iam.demo.test",
                },
            ),
            "misma organización",
        ),
    ],
)
def test_fixture_invalido_falla_antes_de_abrir_un_motor(
    mutate: Callable[[Fixture], object], message: str
) -> None:
    fixture = copy.deepcopy(load_fixture())
    mutate(fixture)
    with pytest.raises(ValueError, match=message):
        validate_fixture(fixture)


def test_fixture_malformado_devuelve_error_controlado(tmp_path: Path) -> None:
    path = tmp_path / "fixture.json"
    path.write_text(json.dumps({"organizations": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="colecciones"):
        load_fixture(path)


def test_destino_demo_no_usa_database_url() -> None:
    environment = {
        "APP_ENV": "development",
        "DATABASE_URL": "postgresql://remote/unsafe",
    }
    with pytest.raises(ValueError, match="DEMO_DEVELOPMENT_DATABASE_URL"):
        validate_safe_target(environment, "DEMO_DEVELOPMENT_DATABASE_URL")


def test_seed_demo_no_bootstrap_catalogos_implicitamente() -> None:
    source = Path("scripts/seed_demo_iam.py").read_text(encoding="utf-8")

    assert "bootstrap_iam_connection" not in source
    assert "assert_canonical_bootstrap_catalogs(connection)" in source


def test_make_exige_confirmaciones_distintas_y_no_trunca() -> None:
    makefile = Path("../Makefile").read_text(encoding="utf-8")
    assert 'CONFIRM)" = "SEED_DEMO_IAM' in makefile
    assert 'CONFIRM)" = "CLEAR_DEMO_IAM' in makefile
    assert 'CONFIRM)" = "REBASELINE_IAM' in makefile
    assert "ejecuta antes backend-bootstrap" in makefile
    assert "TRUNCATE" not in makefile
