# SQL para ER Diagram IAM

## Objetivo

SQL ordenado para generar el diagrama entidad-relacion del dominio IAM en PostgreSQL usando `sqltoerdiagram.com`.

## Cambios realizados

Se documentan las tablas IAM actuales con sus claves primarias, claves foraneas, restricciones unicas e indices relevantes.

## Justificacion tecnica

El orden respeta las dependencias entre tablas para que las relaciones FK puedan resolverse correctamente al pegar el SQL en una herramienta de ERD.

## Decisiones tomadas

- Se mantiene el schema `sch_iam`.
- Se usan los nombres reales de tablas, columnas y constraints definidos en las migraciones/modelos actuales.
- Se incluyen indices FK para representar el modelo operacional con mayor claridad.

## Tests ejecutados

No aplica. Documento SQL para representacion visual del modelo.

## Riesgos o deuda tecnica

- Este SQL esta orientado a ERD, no a reemplazar migraciones Alembic.
- Si cambian las migraciones IAM, este documento debe actualizarse.

## Relacion con el backend

Representa la estructura actual del dominio IAM en `backend/app/domain/iam` y sus migraciones Alembic asociadas.

## SQL completo

```sql
CREATE SCHEMA IF NOT EXISTS sch_iam;

CREATE TABLE sch_iam.tbl_status (
    id_status BIGINT NOT NULL,
    status VARCHAR(50) NOT NULL,
    create_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    update_at TIMESTAMPTZ,

    CONSTRAINT pk_tbl_status PRIMARY KEY (id_status)
);

CREATE TABLE sch_iam.tbl_country (
    id_country BIGINT NOT NULL,
    country_name VARCHAR(100) NOT NULL,

    CONSTRAINT pk_tbl_country PRIMARY KEY (id_country)
);

CREATE TABLE sch_iam.tbl_state (
    id_state BIGINT NOT NULL,
    id_country BIGINT NOT NULL,
    state_name VARCHAR(100) NOT NULL,

    CONSTRAINT pk_tbl_state PRIMARY KEY (id_state),
    CONSTRAINT fk_tbl_state_id_country
        FOREIGN KEY (id_country)
        REFERENCES sch_iam.tbl_country (id_country)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

CREATE INDEX ix_tbl_state_id_country
    ON sch_iam.tbl_state (id_country);

CREATE TABLE sch_iam.tbl_city (
    id_city BIGINT NOT NULL,
    id_state BIGINT NOT NULL,
    city_name VARCHAR(120) NOT NULL,

    CONSTRAINT pk_tbl_city PRIMARY KEY (id_city),
    CONSTRAINT fk_tbl_city_id_state
        FOREIGN KEY (id_state)
        REFERENCES sch_iam.tbl_state (id_state)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

CREATE INDEX ix_tbl_city_id_state
    ON sch_iam.tbl_city (id_state);

CREATE TABLE sch_iam.tbl_platform_role (
    id_platform_role BIGINT NOT NULL,
    platform_role_type VARCHAR(50) NOT NULL,
    description TEXT,
    create_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    update_at TIMESTAMPTZ,

    CONSTRAINT pk_tbl_platform_role PRIMARY KEY (id_platform_role)
);

CREATE TABLE sch_iam.tbl_organization_role (
    id_org_role BIGINT NOT NULL,
    org_role_type VARCHAR(50) NOT NULL,
    create_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    update_at TIMESTAMPTZ,

    CONSTRAINT pk_tbl_organization_role PRIMARY KEY (id_org_role)
);

CREATE TABLE sch_iam.tbl_organization (
    id_organization BIGINT NOT NULL,
    id_country BIGINT NOT NULL,
    id_state BIGINT NOT NULL,
    id_city BIGINT NOT NULL,
    id_status BIGINT NOT NULL,
    name VARCHAR(150) NOT NULL,
    slug VARCHAR(120) NOT NULL,
    org_registered_name VARCHAR(200),
    org_tax VARCHAR(32),
    org_address VARCHAR(255) NOT NULL,
    org_zipcode VARCHAR(20) NOT NULL,
    create_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    update_at TIMESTAMPTZ,

    CONSTRAINT pk_tbl_organization PRIMARY KEY (id_organization),

    CONSTRAINT fk_tbl_organization_id_country
        FOREIGN KEY (id_country)
        REFERENCES sch_iam.tbl_country (id_country)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT fk_tbl_organization_id_state
        FOREIGN KEY (id_state)
        REFERENCES sch_iam.tbl_state (id_state)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT fk_tbl_organization_id_city
        FOREIGN KEY (id_city)
        REFERENCES sch_iam.tbl_city (id_city)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT fk_tbl_organization_id_status
        FOREIGN KEY (id_status)
        REFERENCES sch_iam.tbl_status (id_status)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT uq_tbl_organization_name UNIQUE (name),
    CONSTRAINT uq_tbl_organization_slug UNIQUE (slug),
    CONSTRAINT uq_tbl_organization_org_registered_name UNIQUE (org_registered_name),
    CONSTRAINT uq_tbl_organization_org_tax UNIQUE (org_tax)
);

CREATE INDEX ix_tbl_organization_id_country
    ON sch_iam.tbl_organization (id_country);

CREATE INDEX ix_tbl_organization_id_state
    ON sch_iam.tbl_organization (id_state);

CREATE INDEX ix_tbl_organization_id_city
    ON sch_iam.tbl_organization (id_city);

CREATE INDEX ix_tbl_organization_id_status
    ON sch_iam.tbl_organization (id_status);

CREATE TABLE sch_iam.tbl_users (
    id_user BIGINT NOT NULL,
    id_organization BIGINT NOT NULL,
    id_platform_role BIGINT NOT NULL,
    id_country BIGINT NOT NULL,
    id_state BIGINT NOT NULL,
    id_city BIGINT NOT NULL,
    id_org_role BIGINT NOT NULL,
    id_status BIGINT NOT NULL,
    email VARCHAR(254) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(150) NOT NULL,
    birthdate DATE NOT NULL,
    user_address VARCHAR(255) NOT NULL,
    user_zipcode VARCHAR(20) NOT NULL,
    last_login_at TIMESTAMPTZ,
    create_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    update_at TIMESTAMPTZ,

    CONSTRAINT pk_tbl_users PRIMARY KEY (id_user),

    CONSTRAINT fk_tbl_users_id_organization
        FOREIGN KEY (id_organization)
        REFERENCES sch_iam.tbl_organization (id_organization)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT fk_tbl_users_id_platform_role
        FOREIGN KEY (id_platform_role)
        REFERENCES sch_iam.tbl_platform_role (id_platform_role)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT fk_tbl_users_id_country
        FOREIGN KEY (id_country)
        REFERENCES sch_iam.tbl_country (id_country)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT fk_tbl_users_id_state
        FOREIGN KEY (id_state)
        REFERENCES sch_iam.tbl_state (id_state)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT fk_tbl_users_id_city
        FOREIGN KEY (id_city)
        REFERENCES sch_iam.tbl_city (id_city)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT fk_tbl_users_id_org_role
        FOREIGN KEY (id_org_role)
        REFERENCES sch_iam.tbl_organization_role (id_org_role)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT fk_tbl_users_id_status
        FOREIGN KEY (id_status)
        REFERENCES sch_iam.tbl_status (id_status)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT uq_tbl_users_email UNIQUE (email)
);

CREATE INDEX ix_tbl_users_id_organization
    ON sch_iam.tbl_users (id_organization);

CREATE INDEX ix_tbl_users_id_platform_role
    ON sch_iam.tbl_users (id_platform_role);

CREATE INDEX ix_tbl_users_id_country
    ON sch_iam.tbl_users (id_country);

CREATE INDEX ix_tbl_users_id_state
    ON sch_iam.tbl_users (id_state);

CREATE INDEX ix_tbl_users_id_city
    ON sch_iam.tbl_users (id_city);

CREATE INDEX ix_tbl_users_id_org_role
    ON sch_iam.tbl_users (id_org_role);

CREATE INDEX ix_tbl_users_id_status
    ON sch_iam.tbl_users (id_status);

CREATE TABLE sch_iam.tbl_department (
    id_department BIGINT NOT NULL,
    id_organization BIGINT NOT NULL,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    create_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    update_at TIMESTAMPTZ,

    CONSTRAINT pk_tbl_department PRIMARY KEY (id_department),

    CONSTRAINT fk_tbl_department_id_organization
        FOREIGN KEY (id_organization)
        REFERENCES sch_iam.tbl_organization (id_organization)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

CREATE INDEX ix_tbl_department_id_organization
    ON sch_iam.tbl_department (id_organization);

CREATE TABLE sch_iam.tbl_department_relations (
    id_department_relation BIGINT NOT NULL,
    id_department BIGINT NOT NULL,
    id_user BIGINT NOT NULL,
    create_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    update_at TIMESTAMPTZ,

    CONSTRAINT pk_tbl_department_relations
        PRIMARY KEY (id_department_relation),

    CONSTRAINT fk_tbl_department_relations_id_department
        FOREIGN KEY (id_department)
        REFERENCES sch_iam.tbl_department (id_department)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_tbl_department_relations_id_user
        FOREIGN KEY (id_user)
        REFERENCES sch_iam.tbl_users (id_user)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT uq_tbl_department_relations_id_department_id_user
        UNIQUE (id_department, id_user)
);

CREATE INDEX ix_tbl_department_relations_id_department
    ON sch_iam.tbl_department_relations (id_department);

CREATE INDEX ix_tbl_department_relations_id_user
    ON sch_iam.tbl_department_relations (id_user);
```
