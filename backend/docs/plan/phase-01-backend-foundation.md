# Phase 01 — Base del backend
- goal: (baseline) un toolchain reproducible (uv, ruff, mypy --strict, markers de pytest) y el esqueleto modular de la aplicación: create_app(), el router v1 normalizado, el layout app/domains/<domain>/<module> y la base de datos compartida, los mixins y el registro de modelos.

## 1.1 Toolchain de Python
- layer: infrastructure
- goal: un proyecto uv reproducible con ruff, mypy --strict y markers estrictos de pytest, en el que los tests de base de datos nunca se ejecutan contra una base de datos implícita.

## 1.2 Esqueleto de la aplicación
- layer: interfaces
- goal: la factoría create_app() que monta el router operativo /api y un único router normalizado /api/v1, sobre el layout app/domains/<domain>/<module>.

## 1.3 Capa de base de datos compartida
- layer: infrastructure
- goal: la base declarativa compartida, el mixin de timestamps y un registro central de modelos que carga todos los modelos ORM en una única metadata.
