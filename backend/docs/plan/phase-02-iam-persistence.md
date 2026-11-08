# Phase 02 — Persistencia IAM
- goal: (baseline) los modelos ORM de sch_iam, una baseline de Alembic solo DDL, una CLI de migración protegida que solo se ejecuta contra hosts, bases de datos y usuario de migración permitidos, y scripts protegidos para el bootstrap de catálogos, el seed demo y el rebaseline.

## 2.1 Modelos ORM de IAM
- layer: infrastructure
- goal: las once tablas de sch_iam mapeadas como modelos SQLAlchemy dentro de sus módulos de dominio, de acuerdo con el contrato de la baseline.

## 2.2 Baseline de Alembic solo DDL
- layer: infrastructure
- goal: una única revisión raíz de Alembic que crea el esquema sch_iam solo con DDL y mantiene la metadata de Alembic fuera de sch_iam.

## 2.3 CLI de migración protegida
- layer: infrastructure
- goal: una CLI de migración que solo acepta comandos seguros contra un host, una base de datos y un usuario de migración permitidos, y que da al rol de la aplicación acceso a los datos de IAM más acceso de solo lectura a public.alembic_version para readiness.

## 2.4 Scripts de datos IAM protegidos
- layer: infrastructure
- goal: scripts de bootstrap de catálogos, seed demo y rebaseline que solo se ejecutan contra bases de datos dedicadas locales o de test, nunca recurren a DATABASE_URL y fallan con una salida saneada.

## 2.5 Sesión de base de datos en runtime
- layer: infrastructure
- goal: el engine y la factoría de sesiones cacheados, construidos a partir de los settings validados, que entregan una sesión por petición que se cierra siempre al terminar.
