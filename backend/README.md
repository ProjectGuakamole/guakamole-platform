# Backend — Guakamole Platform

## Propósito

Esta guía explica cómo instalar, levantar y validar el backend de Guakamole Platform en local.

Está pensada especialmente para compañeros de frontend que necesiten tener la API disponible durante el desarrollo, comprobar que responde correctamente y ejecutar validaciones básicas antes de integrar cambios.

No entra en detalles internos de base de datos ni en la estructura interna del backend.

## Requisitos previos

Antes de empezar, asegúrate de tener instalado:

- Docker / Docker Compose.
- `uv`.
- `make`.
- Git.

## Flujo rápido recomendado

Desde la raíz del repositorio, ejecuta:

```bash
make install
make docker-up
make docker-db-migrate
make backend-check
```

`docker-up` es el flujo manual de desarrollo y no ejecuta migraciones
automáticamente. Ejecuta el migrador explícitamente antes de comprobar la
readiness.

En desarrollo local, `docker-up` incorpora obligatoriamente
`docker-compose.local.yml`. Este override publica los puertos de PostgreSQL,
backend y frontend para el host. No es el compose de staging.

Si todo va bien, el backend queda disponible en:

```text
http://localhost:8000
```

## Instalación

Para instalar las dependencias necesarias del entorno local:

```bash
make install
```

Este comando prepara el entorno de desarrollo para poder ejecutar y validar el backend.

## Variables de entorno

Por defecto, el proyecto toma como referencia la configuración definida en `.env.example`.

No deben commitearse secretos reales, credenciales privadas ni tokens personales.

Opcionalmente, para configuración local, puedes crear un archivo `.env` a partir de `.env.example` y adaptarlo a tu entorno. No es obligatorio para todos los flujos y no debe subirse al repositorio.

## Levantar y parar servicios

Para levantar los servicios necesarios en Docker:

```bash
make docker-up
```

Para parar los servicios:

```bash
make docker-down
```

Para consultar logs de los servicios:

```bash
make docker-logs
```

## Base de datos y migraciones desde el punto de vista operativo

El migrador aislado de Docker Compose y su wrapper restringido son el flujo
canónico para despliegues Docker y de staging. Para flujos locales o de backend
controlados se mantienen los targets de host `db-upgrade` y `db-current`,
sujetos a sus allowlists de rol y URL. No ejecutes Alembic directamente ni
incluyas credenciales en comandos, documentación o ficheros versionados.

Para aplicar las migraciones pendientes de forma explícita:

```bash
make docker-db-migrate
```

Para consultar si la revisión aplicada está en la versión esperada:

```bash
make docker-db-current
```

Para comprobar que la revisión Alembic actual coincide con el `head` empaquetado,
sin modificar la base de datos:

```bash
make docker-db-check
```

Esta comprobación no ejecuta deliberadamente `alembic check`: no genera una
revisión ni compara deriva entre los modelos ORM y el esquema.

`db-history` no está disponible mediante el migrador seguro. El histórico no
forma parte de la interfaz operativa expuesta. No existe un flujo de downgrade.

Para un despliegue canónico, que migra antes de iniciar el stack base:

```bash
make docker-deploy
```

`docker-deploy` no sustituye la revisión de la configuración de entorno: usa un
fichero `ENV_FILE` adecuado y mantenlo fuera del repositorio.

`docker-deploy` usa exclusivamente `docker-compose.yml`, pensado para staging:
la red `backend_internal` continúa con `internal: true` y no publica los
puertos de PostgreSQL, backend ni frontend.

## Ejecutar backend en modo desarrollo

Para arrancar FastAPI en modo desarrollo con recarga automática:

```bash
make backend-run
```

## Comprobar backend levantado

Para comprobar que el backend responde correctamente:

```bash
make backend-check
```

También puedes revisar estas URLs desde el navegador o con una herramienta HTTP:

```text
http://localhost:8000/api/health
http://localhost:8000/api/ready
```

## Ejecutar validaciones de código backend

Para ejecutar las validaciones principales del backend:

```bash
make backend-test
```

Este comando ejecuta lint, comprobación de formato, `mypy` y `pytest`.

## Acceder a PostgreSQL si hace falta

Si necesitas abrir una sesión de `psql` en el contenedor de PostgreSQL:

```bash
make psql
```

Este comando levanta PostgreSQL si hace falta y abre `psql` dentro del contenedor.

### pgAdmin local

Para conectar un cliente del host, como pgAdmin, usa el entorno levantado con
`make docker-up`: el override local hace accesible PostgreSQL desde el host.
Configura la conexión con estos valores, tomados del entorno local:

| Campo de pgAdmin | Valor |
| --- | --- |
| Host | `localhost` |
| Puerto | `POSTGRES_PORT` |
| Base de datos | `POSTGRES_DB` |
| Usuario | `POSTGRES_USER` |
| Contraseña | `POSTGRES_PASSWORD` |

No copies credenciales en este documento ni las añadas a argumentos de
comandos. El compose base mantiene PostgreSQL aislado y no permite esta
conexión directa desde el host.

## Ayuda de comandos

Para ver la ayuda disponible del `Makefile`:

```bash
make help
```

Comandos principales visibles:

- `make install`
- `make backend-test`
- `make backend-check`
- `make backend-run`
- `make docker-up`
- `make docker-db-migrate`
- `make docker-db-current`
- `make docker-db-check`
- `make docker-deploy`
- `make docker-down`
- `make docker-logs`
- `make psql`

## Troubleshooting básico

### El backend no responde

Consulta los logs:

```bash
make docker-logs
```

### La comprobación de readiness falla

Comprueba que los servicios están levantados y ejecuta explícitamente las
migraciones operativas. `docker-up` no las ejecuta automáticamente:

```bash
make docker-up
make docker-db-migrate
make backend-check
```

### El puerto está ocupado

Revisa si tienes procesos locales o contenedores usando el mismo puerto. Para reiniciar los servicios del proyecto:

```bash
make docker-down
make docker-up
```

### Quiero reiniciar el entorno

Para parar y volver a levantar los servicios:

```bash
make docker-down
make docker-up
```
