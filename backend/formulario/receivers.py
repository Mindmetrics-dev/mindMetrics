"""
formulario/receivers.py — MindMetrics
========================================
Receptores (observers) para las señales del módulo formulario.

notify_riesgo_alto:
  Registra en el log del servidor cada caso de nivel alto o crítico.
  Esto funciona como notificación al sistema (audit trail) para que
  el equipo de salud mental pueda monitorear sin depender de la UI.
"""
import logging

from django.dispatch import receiver

from .signals import riesgo_alto_detectado

logger = logging.getLogger("mindmetrics.riesgo")


@receiver(riesgo_alto_detectado)
def notify_riesgo_alto(sender, usuario_id, nivel_riesgo, registro_id, **kwargs):
    """Observer del sistema: log de alerta cuando el riesgo es alto o crítico."""
    logger.warning(
        "ALERTA RIESGO %s — usuario_id=%s | registro_id=%s",
        nivel_riesgo.upper(),
        usuario_id,
        registro_id,
    )
