"""
formulario/signals.py — MindMetrics
=====================================
Señales del módulo formulario (patrón Observer).

riesgo_alto_detectado:
  Se dispara cuando el agente calcula nivel_riesgo "alto" o "critico"
  para un registro diario recién creado.

  kwargs enviados:
    sender       — clase RegistroEmocional
    usuario_id   — PK del usuario de dominio (int)
    nivel_riesgo — "alto" | "critico"
    registro_id  — PK del RegistroEmocional recién creado (int)
"""
from django.dispatch import Signal

riesgo_alto_detectado = Signal()
