"""
formulario/services.py — MindMetrics
====================================================
Capa de orquestación para el flujo del registro diario.

FLUJO (submit_registro_diario):
  1. Validar que el usuario no haya registrado ya en la fecha indicada.
  2. Resolver la emoción predominante (FK Emocion) por nombre.
  3. Crear el RegistroEmocional con los datos del día.
  4. Construir el estado consolidado (evaluación inicial + últimos 7).
  5. Llamar al motor de inferencia (agente/classifier).
  6. Normalizar la etiqueta del nivel de riesgo a snake_case.
  7. Guardar el nivel_riesgo en el mismo registro recién creado.
  8. [Observer] Disparar señal riesgo_alto_detectado si el nivel es alto o crítico.

Todo dentro de transaction.atomic.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, time as dt_time
from typing import Optional

from django.db import transaction
from django.utils import timezone

from agente.classifier import evaluar_desde_evaluacion
from agente.state_builder import build_consolidated_state
from core.models import Emocion, RegistroEmocional, Usuario

logger = logging.getLogger(__name__)

NIVEL_RIESGO_NORMALIZADO = {
    "Muy Bajo": "muy_bajo",
    "Bajo":     "bajo",
    "Moderado": "moderado",
    "Alto":     "alto",
    "Crítico":  "critico",
}


# ─── Excepciones de dominio ───────────────────────────────────────────────────

class RegistroDiarioError(Exception):
    pass


class YaRegistroHoy(RegistroDiarioError):
    pass


class EvaluacionInicialFaltante(RegistroDiarioError):
    pass


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _ya_registro_en_fecha(usuario: Usuario, fecha: date) -> bool:
    """True si el usuario ya tiene un RegistroEmocional en esa fecha local.

    Usa datetimes aware (Bogota) para el __range: Django los convierte a UTC
    correctamente al generar el SQL, evitando el RuntimeWarning y el desfase
    de 5 horas que producían los datetimes naive pasados directamente.
    """
    inicio = timezone.make_aware(datetime.combine(fecha, dt_time.min))
    fin    = timezone.make_aware(datetime.combine(fecha, dt_time.max))
    return RegistroEmocional.objects.filter(
        id_usuario=usuario,
        fecha_registro__range=(inicio, fin),
    ).exists()


def _resolver_emocion(nombre: str) -> Emocion:
    emocion, _ = Emocion.objects.get_or_create(nombre_emocion=nombre)
    return emocion


# ─── Función principal ────────────────────────────────────────────────────────

@transaction.atomic
def submit_registro_diario(
    usuario_dominio: Usuario,
    datos: dict,
    fecha: Optional[date] = None,
) -> RegistroEmocional:
    if fecha is None:
        fecha = timezone.localdate()

    if _ya_registro_en_fecha(usuario_dominio, fecha):
        raise YaRegistroHoy(
            f"El usuario {usuario_dominio.id_usuario} ya tiene un registro "
            f"para la fecha {fecha.isoformat()}."
        )

    emocion = _resolver_emocion(datos["emocion_predominante"])

    registro = RegistroEmocional.objects.create(
        id_usuario           = usuario_dominio,
        id_emocion           = emocion,
        hr_sueno_dia         = datos.get("horas_sueno"),
        hr_trabajo_dia       = datos.get("horas_trabajo_estudio"),
        hr_pantalla_dia      = datos.get("horas_pantallas"),
        hr_act_fis_dia       = datos.get("horas_actividad_fisica"),
        estres_laboral_dia   = datos.get("estres_laboral"),
        estres_academico_dia = datos.get("estres_academico"),
        estres_financ_dia    = datos.get("estres_financiero"),
        apoyo_percibido_dia  = datos.get("interaccion_social"),
        autocuidado          = datos.get("autocuidado"),
        animo                = (
            str(datos["animo"]) if datos.get("animo") is not None else None
        ),
        nivel_riesgo         = None,
    )

    try:
        state = build_consolidated_state(usuario_dominio)
    except Exception as exc:
        if exc.__class__.__name__ == "DoesNotExist":
            raise EvaluacionInicialFaltante(
                "No se pudo calcular el riesgo: falta evaluacion inicial."
            ) from exc
        logger.exception(
            "Error construyendo el estado consolidado para usuario %s",
            usuario_dominio.id_usuario,
        )
        raise

    try:
        resultado = evaluar_desde_evaluacion(state)
        etiqueta_motor = resultado["etiqueta"]
    except Exception:
        logger.exception(
            "Error ejecutando el motor de riesgo para usuario %s",
            usuario_dominio.id_usuario,
        )
        raise

    nivel_normalizado = NIVEL_RIESGO_NORMALIZADO.get(etiqueta_motor)
    if nivel_normalizado is None:
        logger.warning(
            "Etiqueta de riesgo inesperada del motor: %r (usuario %s). Se guarda tal cual.",
            etiqueta_motor,
            usuario_dominio.id_usuario,
        )
        nivel_normalizado = etiqueta_motor

    registro.nivel_riesgo = nivel_normalizado
    registro.save(update_fields=["nivel_riesgo"])

    logger.info(
        "Registro diario creado: usuario=%s id_registro=%s nivel=%s",
        usuario_dominio.id_usuario,
        registro.id_registro,
        nivel_normalizado,
    )

    # [Observer] Notificar cuando el riesgo es alto o critico
    if nivel_normalizado in ("alto", "critico"):
        from .signals import riesgo_alto_detectado
        riesgo_alto_detectado.send(
            sender=RegistroEmocional,
            usuario_id=usuario_dominio.id_usuario,
            nivel_riesgo=nivel_normalizado,
            registro_id=registro.id_registro,
        )

    return registro
