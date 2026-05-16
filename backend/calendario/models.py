"""
calendario/models.py — MindMetrics
============================================================
Capa de modelos del módulo `calendario`.

DECISIÓN ARQUITECTÓNICA (estrategia "core canónico"):
  El esquema 3NF vive en `core/models.py` con managed=False. Este módulo
  no redefine tablas: re-exporta los modelos del dominio que consulta,
  de modo que views/urls importen `calendario.models.RegistroEmocional`
  sin acoplarse a la ruta física de `core`.

Modelos del dominio usados por este módulo:
  - RegistroEmocional : registro conductual diario que se pinta en la
                        malla del calendario.
  - Emocion           : catálogo de emociones (etiqueta de cada día).
"""
from core.models import Emocion, RegistroEmocional

__all__ = ["RegistroEmocional", "Emocion"]
