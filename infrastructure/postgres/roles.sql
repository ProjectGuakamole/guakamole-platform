-- Idempotente. Se ejecuta únicamente por init de volumen vacío o provisión manual.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'guakamole_migrator') THEN
    CREATE ROLE guakamole_migrator LOGIN NOINHERIT;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'guakamole_app') THEN
    CREATE ROLE guakamole_app LOGIN NOINHERIT;
  END IF;
END
$$;

ALTER ROLE guakamole_migrator PASSWORD :'migrator_password';
ALTER ROLE guakamole_app PASSWORD :'app_password';
GRANT CONNECT, TEMPORARY, CREATE ON DATABASE :"db_name" TO guakamole_migrator;
GRANT CONNECT ON DATABASE :"db_name" TO guakamole_app;
ALTER ROLE guakamole_migrator IN DATABASE :"db_name" SET search_path = sch_iam, public;
ALTER ROLE guakamole_app IN DATABASE :"db_name" SET search_path = sch_iam, public;

REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE, CREATE ON SCHEMA public TO guakamole_migrator;
GRANT USAGE ON SCHEMA public TO guakamole_app;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'sch_iam') THEN
    ALTER SCHEMA sch_iam OWNER TO guakamole_migrator;
    GRANT USAGE ON SCHEMA sch_iam TO guakamole_app;
    GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA sch_iam
      TO guakamole_app;
    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA sch_iam TO guakamole_app;
  END IF;
  IF to_regclass('public.alembic_version') IS NOT NULL THEN
    ALTER TABLE public.alembic_version OWNER TO guakamole_migrator;
    GRANT SELECT ON TABLE public.alembic_version TO guakamole_app;
  END IF;
END
$$;

ALTER DEFAULT PRIVILEGES FOR ROLE guakamole_migrator IN SCHEMA public
  REVOKE ALL ON TABLES FROM PUBLIC;
