# BACK-DEMO-001 — Seed demo IAM temporal

## Objetivo

Añadir datos ficticios temporales para validar conexiones con PostgreSQL, Swagger y relaciones PK/FK del piloto IAM sin modificar migraciones Alembic.

> **DESTRUCTIVO:** este script trunca las tablas IAM gestionadas bajo `sch_iam` antes de insertar el fixture demo.

## Uso

Prerequisito: ejecutar las migraciones sobre la base de datos objetivo.

```bash
cd backend
uv run alembic upgrade head
uv run python scripts/seed_demo_iam.py --yes
# o desde la raíz del repositorio:
make backend-seed
```

Para vaciar las tablas IAM gestionadas por el script sin reinsertar datos demo:

```bash
cd backend
uv run python scripts/seed_demo_iam.py --clear --yes
# o desde la raíz del repositorio:
make backend-seed-clear
```

El script lee `DATABASE_URL` del entorno y exige PostgreSQL real. No está preparado para SQLite ni otros dialectos. La opción `--yes` es obligatoria porque tanto el seed normal como `--clear` ejecutan un `TRUNCATE ... RESTART IDENTITY CASCADE` sobre las tablas gestionadas de `sch_iam`.

## Advertencias

- Los datos son ficticios y no productivos.
- No usar en staging, producción ni en ninguna base de datos con información a conservar.
- El seed normal es destructivo: trunca `tbl_status`, `tbl_platform_role`, `tbl_organization_role`, `tbl_country`, `tbl_state`, `tbl_city`, `tbl_organization`, `tbl_users`, `tbl_department` y `tbl_department_relations`, reinicia identidades y después inserta el fixture completo.
- `--clear --yes` también es destructivo: trunca esas mismas tablas y las deja vacías.
- Los emails terminan en `.demo.test`, los slugs empiezan por `demo-` y los nombres demo relevantes empiezan por `Demo `.
- El `password_hash` es un placeholder no válido: `argon2id-demo-placeholder-not-valid`.
- El script calcula claves temporales con `MAX(id)+1`. Es un riesgo aceptado porque este seed es temporal, no productivo y no concurrente; no debe ejecutarse en paralelo ni reutilizarse como patrón de persistencia de aplicación.
- Swagger sigue necesitando la auth/dev-auth provisional para obtener `200` en endpoints protegidos como IAM/users.
