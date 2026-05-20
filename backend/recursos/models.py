"""
recursos/models.py — MindMetrics
============================================================
Capa de modelos del módulo `recursos`.

DECISIÓN ARQUITECTÓNICA (estrategia "core canónico"):
  El esquema 3NF vive en `core/models.py` con managed=False (las tablas
  las crea el DDL SQL, no las migraciones de Django). Este módulo NO
  redefine tablas: re-exporta únicamente los modelos del dominio que le
  competen para que el resto del módulo (views, urls) los importe como
  `recursos.models.RecursoApoyo` sin acoplarse a la ruta física de core.

  Ventaja: integridad referencial intacta, cero migraciones nuevas,
  y un único punto de verdad para el DDL.

Modelos del dominio usados por este módulo:
  - TipoRecurso         : catálogo de tipos de recurso.
  - RecursoApoyo        : recurso de apoyo (artículo, ejercicio, PDF...).
  - PresentacionRecurso : traza M2M usuario ↔ recurso ↔ fecha.
"""
from core.models import PresentacionRecurso, RecursoApoyo, TipoRecurso

__all__ = ["TipoRecurso", "RecursoApoyo", "PresentacionRecurso"]
