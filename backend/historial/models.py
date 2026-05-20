"""
historial/models.py — MindMetrics
============================================================
Capa de modelos del módulo `historial`.

DECISIÓN ARQUITECTÓNICA (estrategia "core canónico"):
  El esquema 3NF vive en `core/models.py` con managed=False. Este módulo
  no redefine tablas: re-exporta los modelos del dominio que consulta,
  de modo que views/urls importen `historial.models.RegistroEmocional`
  sin acoplarse a la ruta física de `core`.

Modelos del dominio usados por este módulo:
  - RegistroEmocional : registro conductual diario (fuente de las métricas).
  - EvaluacionInicial : línea base sociodemográfica/clínica del usuario.
  - Emocion           : catálogo de emociones (para etiquetar registros).
"""
from core.models import Emocion, EvaluacionInicial, RegistroEmocional

__all__ = ["RegistroEmocional", "EvaluacionInicial", "Emocion"]
