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
make db-upgrade
make backend-check
```

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

Para dejar la base de datos en la versión esperada por la aplicación:

```bash
make db-upgrade
```

Para comprobar la versión actual:

```bash
make db-current
```

Para consultar el histórico de migraciones:

```bash
make db-history
```

Para retroceder una revisión:

```bash
make db-downgrade REVISION=-1
```

Usa `db-downgrade` con cuidado, especialmente si estás compartiendo entorno o datos de prueba con otras personas.

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
- `make docker-down`
- `make docker-logs`
- `make psql`
- `make db-upgrade`
- `make db-current`
- `make db-history`
- `make db-downgrade`

## Troubleshooting básico

### El backend no responde

Consulta los logs:

```bash
make docker-logs
```

### La comprobación de readiness falla

Comprueba que los servicios están levantados y ejecuta las migraciones operativas:

```bash
make docker-up
make db-upgrade
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
