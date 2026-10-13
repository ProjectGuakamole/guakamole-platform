---
name: guakamole-documentation-style
description: Use when creating or updating Guakamole technical documentation to apply homogeneous Markdown/Obsidian formatting in Spanish that is didactic and secure.
---

# Guakamole Documentation Style

Usa esta skill al crear o actualizar documentación técnica de Guakamole, tanto para el backend actual como para sus evoluciones futuras.

## Idioma y tono

- Escribe en castellano de España.
- Usa un lenguaje técnico, claro, coloquial, humanizado y didáctico.
- Explica los conceptos sin dar por sentado conocimiento innecesario, pero sin perder precisión técnica.
- Prioriza frases concretas y útiles frente a texto de relleno.

## Formato

- Escribe Markdown compatible con Obsidian.
- Los documentos deben ser autocontenidos: no incluyas enlaces internos a archivos del repositorio.
- Mantén consistentes los títulos, niveles de encabezado, tablas, listas y bloques de código dentro de cada documento.
- Usa ejemplos de código, rutas, entradas, salidas y decisiones cuando ayuden a entender el cambio o su uso.
- Evita enlaces rotos, textos vacíos, docstrings o documentación redundante y listados de archivos sin explicar su relevancia.

## Contenido técnico

Cuando aplique, documenta de forma explícita:

- Qué se ha hecho.
- Por qué se ha hecho.
- Cómo se ha implantado.
- Beneficios obtenidos.
- Limitaciones y compromisos asumidos.
- Riesgos conocidos.
- Ejemplos de uso o comportamiento.

Separa claramente los hechos implantados, las decisiones tomadas, la deuda técnica y el trabajo futuro. Nunca presentes una tarea pendiente, una hipótesis o una recomendación como si estuviera implantada.

## Seguridad

- Nunca expongas secretos, tokens reales, hashes, flags, respuestas correctas ni datos sensibles.
- Emplea valores ficticios y no operativos en ejemplos, como `API_TOKEN=<configurado_en_entorno>`.
- Describe los controles de seguridad y los riesgos sin revelar información que permita eludirlos.

## Auditorías

Al documentar una auditoría, incluye, cuando aplique:

| Elemento | Contenido esperado |
| --- | --- |
| Hallazgo | Qué se ha observado. |
| Severidad | Nivel de impacto o prioridad. |
| Riesgo | Consecuencia técnica o de seguridad. |
| Decisión | Criterio adoptado ante el hallazgo. |
| Acción | Medida implantada o prevista. |
| Estado | Situación actual: resuelto, aceptado, pendiente o en seguimiento. |

Indica de forma inequívoca qué acciones están completadas y cuáles permanecen pendientes.
