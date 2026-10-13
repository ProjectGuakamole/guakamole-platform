# backend/audit/BACK-DB-MIGRATIONS-AUDIT-001

## Objetivo

Registrar la evidencia Docker del punto 2 para la configuración del backend y su contexto de construcción, dentro del alcance de migraciones.

## Responsabilidad del documento

Este histórico trata Compose y el contexto de imagen. No describe el grafo Alembic ni la interfaz operativa de Makefile.

## Estado actual

**EN CURSO — punto 2 aprobado y completado.** La fase conserva puntos posteriores; este histórico no declara un cierre global.

## Cambios realizados

- El servicio backend de Compose recibe una lista explícita de variables permitidas; no carga el entorno completo, la contraseña de PostgreSQL ni la base de datos de pruebas.
- La configuración seleccionada es determinista para el servicio.
- Se añadió `.dockerignore` al contexto de construcción de `backend/`: excluye archivos de entorno, Git, cachés, entornos virtuales y pruebas, y conserva aplicación, Alembic, `alembic.ini` y scripts necesarios.
- La tarea Docker específica para migraciones permanece pendiente del punto 5.

## Justificacion tecnica

La lista permitida limita la propagación accidental de configuración al contenedor. Reducir el contexto de construcción evita incluir material local no necesario sin retirar los recursos que necesita la imagen.

## Decisiones tomadas

- Mantener la configuración de Compose sin secretos documentados.
- No iniciar migraciones automáticamente con el backend; el trabajo Docker explícito se evaluará en el punto 5.
- Conservar en la imagen únicamente los recursos requeridos para ejecutar el backend y Alembic.

## Tests ejecutados

Se validó el renderizado de las configuraciones de Compose para confirmar la selección determinista y la ausencia de secretos en la configuración resultante. Los resultados globales de calidad se registran en el histórico Makefile para evitar duplicación.

## Riesgos o deuda tecnica

- No existe todavía una tarea Docker dedicada de migraciones.
- La validación del ciclo completo de baseline y Docker sigue pendiente.

## Relacion con el backend

El backend recibe solo la configuración necesaria al ejecutarse en Compose y su imagen evita incorporar ficheros locales ajenos a la aplicación.
