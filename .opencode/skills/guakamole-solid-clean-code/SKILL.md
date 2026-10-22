---
name: guakamole-solid-clean-code
description: Use when implementing or validating Guakamole backend code for atomic modular design, SOLID, Clean Code, abstractions, polymorphism, reusable classes and strict review criteria.
---

# Guakamole SOLID & Clean Code

Use this skill for `backend/` implementation and validation whenever code architecture, modularity, maintainability, testability or security-sensitive backend design is involved.

## Mandatory implementation principles

- Write atomic, modular, reusable code.
- Keep one responsibility per class, function and module.
- Follow SOLID pragmatically:
  - Single Responsibility: each component has one reason to change.
  - Open/Closed: extend behavior through abstractions/adapters where useful.
  - Liskov Substitution: fakes, no-op adapters and real adapters respect the same contracts.
  - Interface Segregation: small focused interfaces, no god protocols.
  - Dependency Inversion: services depend on abstractions, not framework or ORM details.
- Keep FastAPI routers as HTTP adapters only.
- Put business rules in services/use cases.
- Encapsulate SQLAlchemy inside repositories.
- Encapsulate security concerns in dedicated components: password hashing, token issuing, audit logging, authorization policies and configuration.
- Use models/classes for domain concepts and Pydantic schemas for HTTP contracts.
- Use `typing.Protocol` or `abc.ABC` for replaceable ports: repositories, token issuers, password hashers, audit loggers and external providers.
- Use polymorphism where it provides real decoupling: SQLAlchemy adapters, no-op adapters, fakes/stubs in tests, provider implementations.
- Use dependency injection to make services testable without FastAPI.
- Keep code compatible with `ruff` and `mypy --strict`.
- Avoid duplicated logic, circular imports, hidden side effects and magic constants.
- Never log or expose secrets, passwords, password hashes, tokens, flags or correct answers.

## Getter and setter rule for Python

Do not write Java-style getters/setters by default.

Use idiomatic Python:

- direct immutable fields for DTOs/value objects when safe;
- `@property` only when it protects invariants, derives values or hides internal representation;
- explicit methods when behavior is domain action, not field access.

## Validation criteria for reviewers

When validating code, reject or request changes if:

- routers contain business logic;
- services directly depend on FastAPI request/response objects;
- services build raw SQLAlchemy queries instead of using repositories;
- components mix unrelated responsibilities;
- abstractions are missing for replaceable dependencies;
- abstractions are decorative and not used to decouple tests or adapters;
- code cannot be unit-tested without running FastAPI or real external services;
- security-sensitive values are logged or returned;
- tests only check happy path and miss negative/security cases;
- role/status/tenant decisions are hardcoded without configuration/catalog resolution.

## Expected review output

- For implementers: produce modular code and explain component boundaries.
- For QA: explicitly state whether SOLID/Clean Code/modularity passed or which changes are required.
- For API architects: explicitly state whether endpoint/module design respects boundaries, security and tenant isolation.
