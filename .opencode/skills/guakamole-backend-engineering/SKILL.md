---
name: guakamole-backend-engineering
description: Use when working on Guakamole backend engineering in backend/: FastAPI, Python 3.12, uv, SOLID, PEP8, modular code, Pydantic, ORM, ruff, mypy strict and pytest.
---

# Guakamole Backend Engineering

Usa esta skill para cualquier tarea de ingenieria backend en Project Guakamole.

Reglas de ambito:

- Trabaja solo en `backend/`.
- La documentacion backend vive en `docs/backend/`.
- No modifiques `frontend/` salvo instruccion explicita del usuario.

Stack acordado:

- Python 3.12.
- FastAPI.
- uv.
- Pydantic.
- SQLAlchemy como ORM.
- Alembic para migraciones.
- ruff para lint y formato.
- mypy en modo strict.
- pytest para tests.

Reglas de codigo:

- Aplica SOLID.
- Respeta PEP8.
- Escribe codigo modular y reutilizable.
- Evita duplicacion; reutiliza con imports.
- Mantiene funciones y clases cortas, con una sola responsabilidad.
- Usa polimorfismo o clases abstractas cuando mejore claramente la estructura.
- Usa type hints completos.
- Evita `Any` y `# type: ignore` salvo justificacion concreta.
- Todo codigo funcional nuevo debe tener tests.
- No introduzcas secretos ni valores sensibles.

## Estandares obligatorios de calidad y diseno

### Codigo atomico y responsabilidad unica

- Las funciones y los metodos deben ser atomicos, cortos y tener una unica responsabilidad.
- Evita parametros booleanos y disenos que mezclen comportamientos inconexos.
- Separa la logica pura de los efectos secundarios cuando resulte viable.
- Evita la duplicacion, los valores magicos y las dependencias circulares.
- Reutiliza los componentes existentes antes de crear abstracciones nuevas.

### Naming

- Usa nombres semanticos, claros y consistentes.
- Usa `is_` para predicados booleanos y `has_` para comprobar existencia.
- Usa `get_` para obtencion, `find_` para busquedas que pueden no encontrar resultado y `list_` para colecciones.
- Usa `create_` o `build_` para construccion, y `validate_`, `require_` o `delete_` segun la intencion.
- Usa `set_` solo cuando no sea mas correcto utilizar `@property`.

### Patrones y extensibilidad

- Usa `@property` para accesos o derivaciones simples frente a getters y setters triviales.
- Usa `@classmethod`, `@abstractmethod`, `Protocol`, polimorfismo y decorators unicamente cuando mejoren de forma real la legibilidad, el desacoplamiento, la extensibilidad, la reutilizacion o la testabilidad.
- No introduzcas patrones ni capas por moda o sobreingenieria.
- Preserva la inyeccion de dependencias y la testabilidad.

### Tipado y seguridad

- Usa type hints completos.
- Evita `Any`, `cast` y `# type: ignore` salvo justificacion concreta y minima.
- No registres, expongas ni hardcodees secretos, tokens, hashes o datos sensibles.
- Mantiene los errores controlados y no filtres detalles internos.

### Imports

- Importa explicitamente desde el modulo real, nunca desde `__init__.py`.
- No dejes lineas en blanco innecesarias dentro del mismo grupo de imports.
- Separa los imports por grupos: stdlib, third-party y aplicacion.
- No permitas imports circulares.

### Docstrings de modulos

- Los docstrings se escriben siempre en ingles.
- No anadas docstrings de modulo en archivos `.py` normales solo por convencion. Elimina los redundantes que no aporten un contrato o contexto no evidente.
- Cada `__init__.py` mantiene solo un docstring de paquete minimo, en ingles y sin imports, exports ni logica.
- El docstring de una clase estandar va inmediatamente bajo `class`, nunca bajo `__init__`.
- El docstring de `__init__` va inmediatamente bajo `def __init__` cuando sus argumentos o su construccion requieran contexto.
- El docstring de una funcion o metodo va inmediatamente bajo `def`.
- Son obligatorios para clases publicas, funciones publicas, metodos publicos, constructores con argumentos no evidentes y funciones privadas complejas o no obvias.
- No son obligatorios para helpers privados triviales, propiedades autoexplicativas ni metodos muy pequenos cuyo nombre y tipos explican por completo la accion.
- Mantenlos cortos y utiles: una explicacion breve de una o dos lineas y, cuando aplique, `Args:` y `Returns:` de forma concisa. No escribas docstrings extensos ni redundantes.

### Hexagonal progresiva

- Mantiene los routers finos, sin logica de negocio ni acceso directo a SQLAlchemy.
- Desacopla los servicios de FastAPI y HTTP.
- Mantiene los repositorios y adapters aislados de HTTP y como responsables de persistencia e integraciones.
- No crees abstracciones sin necesidad actual o una extension clara.

Comandos objetivo cuando el backend este configurado:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict .
uv run pytest
```
