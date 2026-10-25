# Architecture — what "good work" means

**Hexagonal** architecture. Dependencies point **toward the domain**.

## Layers

| Layer | Content | May import |
|-------|---------|------------|
| **domain** | Entities, value objects, business logic. Pure Python. | nothing external |
| **application** | Use cases; they define **ports** (`Protocol`/ABC). | domain |
| **infrastructure** | Adapters: ORM, HTTP, queues, scraping, external clients. | domain, application |
| **interfaces** | API (FastAPI/Django), CLI, workers. | application (and infra DI) |

`src/` layout:

```
src/
  <package>/
    domain/
    application/
    infrastructure/
    interfaces/
```

## Dependency rules (verified by Codex)

- `domain/` does **not** import FastAPI, Django, SQLAlchemy, infra Pydantic, or external clients.
- Ports are defined in `application/` as `Protocol`/ABC; `infrastructure/` implements them.
- **DI through the constructor**, not global singletons.
- The **ORM model is not the domain entity**: it is mapped in `infrastructure/`.
- Boundary validation (`interfaces/`): Pydantic v2 / serializers. External data = untrusted.

## ‹Project-specific decisions›

- ‹ORM: SQLAlchemy 2.x async | Django ORM›
- ‹Context boundaries / bounded contexts›
- ‹External integrations and their adapters›
