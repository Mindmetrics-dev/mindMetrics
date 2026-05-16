"""
formulario/services.py — MindMetrics
====================================
Capa de orquestación para el flujo del registro diario.

FLUJO (submit_registro_diario):
  1. Validar que el usuario no haya registrado ya en la fecha indicada.
  2. Resolver la emoción predominante (FK Emocion) por nombre.
  3. Crear el RegistroEmocional con los datos del día.
  4. Construir el estado consolidado (evaluación inicial + últimos 7).
  5. Llamar al motor de inferencia (agente/classifier).
  6. Normalizar la etiqueta del nivel de riesgo a snake_case.
  7. Guardar el nivel_riesgo en el mismo registro recién creado.

Todo dentro de transaction.atomic: si el motor falla, se hace rollback
y el registro no queda huérfano.
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Optional

from django.db import transaction
from django.utils import timezone

from agente.classifier import evaluar_desde_evaluacion
from agente.state_builder import build_consolidated_state
from core.models import Emocion, RegistroEmocional, Usuario

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Normalización del nivel de riesgo
# ─────────────────────────────────────────────────────────────────────────────
# El motor (agente/classifier.py) devuelve la etiqueta con formato visual:
# "Muy Bajo", "Bajo", "Moderado", "Alto", "Crítico".
#
# En BD guardamos la versión normalizada (snake_case, sin tildes ni espacios).
# La etiqueta legible se reconstruye en la UI con get_nivel_riesgo_display()
# si el modelo declara los choices correctos.

NIVEL_RIESGO_NORMALIZADO = {
    "Muy Bajo": "muy_bajo",
    "Bajo":     "bajo",
    "Moderado": "moderado",
    "Alto":     "alto",
    "Crítico":  "critico",
}


# ─────────────────────────────────────────────────────────────────────────────
# Excepciones de dominio
# ─────────────────────────────────────────────────────────────────────────────

class RegistroDiarioError(Exception):
    """Error genérico del flujo de registro diario."""


class YaRegistroHoy(RegistroDiarioError):
    """El usuario ya hizo un registro en la fecha indicada."""


class EvaluacionInicialFaltante(RegistroDiarioError):
    """El usuario no tiene evaluación inicial — flujo bloqueado."""


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _ya_registro_en_fecha(usuario: Usuario, fecha: date) -> bool:
    """True si el usuario ya tiene un RegistroEmocional en esa fecha."""
    return RegistroEmocional.objects.filter(
        id_usuario=usuario,
        fecha_registro__date=fecha,
    ).exists()


def _resolver_emocion(nombre: str) -> Emocion:
    """
    Busca la emoción por nombre. Si no existe, la crea.
    Las 6 emociones del template (miedo/tristeza/ira/alegría/sorpresa/asco)
    deberían estar pre-pobladas; este get_or_create es defensivo.
    """
    emocion, _ = Emocion.objects.get_or_create(nombre_emocion=nombre)
    return emocion


# ─────────────────────────────────────────────────────────────────────────────
# Función principal
# ─────────────────────────────────────────────────────────────────────────────

@transaction.atomic
def submit_registro_diario(
    usuario_dominio: Usuario,
    datos: dict,
    fecha: Optional[date] = None,
) -> RegistroEmocional:
    """
    Orquesta el flujo completo del registro diario.

    Args:
        usuario_dominio: instancia de core.models.Usuario
            (NO CustomUser — usar request.user.usuario_dominio).
        datos: dict con los campos del formulario diario.
            Claves esperadas:
              - horas_sueno, horas_trabajo_estudio, horas_pantallas,
                horas_actividad_fisica (float)
              - estres_laboral, estres_academico, estres_financiero (int 1-10)
              - interaccion_social, animo (int 1-10)
              - autocuidado (str, libre)
              - emocion_predominante (str: miedo/tristeza/ira/alegria/sorpresa/asco)
        fecha: fecha del registro. Si None, usa hoy en la timezone del proyecto.

    Returns:
        RegistroEmocional recién creado, con nivel_riesgo poblado.

    Raises:
        YaRegistroHoy: si el usuario ya registró ese día.
        EvaluacionInicialFaltante: si el usuario no tiene evaluación inicial.
    """
    if fecha is None:
        fecha = timezone.localdate()

    # 1. Validar unicidad por día
    if _ya_registro_en_fecha(usuario_dominio, fecha):
        raise YaRegistroHoy(
            f"El usuario {usuario_dominio.id_usuario} ya tiene un registro "
            f"para la fecha {fecha.isoformat()}."
        )

    # 2. Resolver FK a Emocion
    emocion = _resolver_emocion(datos["emocion_predominante"])

    # 3. Crear el RegistroEmocional con los datos del día.
    #    nivel_riesgo aún no se conoce; se completará en el paso 6.
    #    Nota: el campo apoyo_percibido_dia del modelo actual lo usamos para
    #    guardar interaccion_social (el SQL aún se llama apoyo_percibido_dia).
    registro = RegistroEmocional.objects.create(
        id_usuario          = usuario_dominio,
        id_emocion          = emocion,
        hr_sueno_dia        = datos.get("horas_sueno"),
        hr_trabajo_dia      = datos.get("horas_trabajo_estudio"),
        hr_pantalla_dia     = datos.get("horas_pantallas"),
        hr_act_fis_dia      = datos.get("horas_actividad_fisica"),
        estres_laboral_dia  = datos.get("estres_laboral"),
        estres_academico_dia= datos.get("estres_academico"),
        estres_financ_dia   = datos.get("estres_financiero"),
        apoyo_percibido_dia = (
            str(datos["interaccion_social"])
            if datos.get("interaccion_social") is not None else None
        ),
        autocuidado         = datos.get("autocuidado"),
        animo               = (
            str(datos["animo"])
            if datos.get("animo") is not None else None
        ),
        nivel_riesgo        = None,  # placeholder; se completa abajo
    )

    # 4. Construir el estado consolidado (incluye este registro recién creado,
    #    porque ya está persistido y el state_builder lo va a leer).
    try:
        state = build_consolidated_state(usuario_dominio)
    except Exception as exc:
        # Si no hay evaluación inicial, propagamos como error de dominio.
        # Cualquier otro error se loguea y se relanza para que la transacción
        # haga rollback.
        if exc.__class__.__name__ == "DoesNotExist":
            raise EvaluacionInicialFaltante(
                "No se pudo calcular el riesgo: falta evaluación inicial."
            ) from exc
        logger.exception(
            "Error construyendo el estado consolidado para usuario %s",
            usuario_dominio.id_usuario,
        )
        raise

    # 5. Llamar al motor
    try:
        resultado = evaluar_desde_evaluacion(state)
        etiqueta_motor = resultado["etiqueta"]  # "Muy Bajo" ... "Crítico"
    except Exception:
        logger.exception(
            "Error ejecutando el motor de riesgo para usuario %s",
            usuario_dominio.id_usuario,
        )
        raise  # rollback de transaction.atomic

    # 6. Normalizar y guardar
    nivel_normalizado = NIVEL_RIESGO_NORMALIZADO.get(etiqueta_motor)
    if nivel_normalizado is None:
        logger.warning(
            "Etiqueta de riesgo inesperada del motor: %r (usuario %s). "
            "Se guarda tal cual.",
            etiqueta_motor, usuario_dominio.id_usuario,
        )
        nivel_normalizado = etiqueta_motor  # defensivo: no perder el dato

    registro.nivel_riesgo = nivel_normalizado
    registro.save(update_fields=["nivel_riesgo"])

    logger.info(
        "Registro diario creado: usuario=%s id_registro=%s nivel=%s",
        usuario_dominio.id_usuario, registro.id_registro, nivel_normalizado,
    )

    return registro
