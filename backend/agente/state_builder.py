"""
agente/state_builder.py — MindMetrics
=====================================
Construye el "estado consolidado" de un usuario para alimentar al motor
de inferencia (agente/classifier.py).

El estado consolidado mezcla:
  - Variables de la evaluación inicial (no cambian con el diario).
  - Promedios móviles de los últimos N registros diarios.
  - Variables derivadas (cambio_emocional = varianza del ánimo).

IMPORTANTE — DECISIONES DE DISEÑO
---------------------------------
1. El state_builder NO modifica la EvaluacionInicial. Devuelve un objeto
   temporal (ConsolidatedState) que vive solo durante el cálculo.
   Razón: preservar el valor original que respondió el usuario y permitir
   reconstruir el estado de cualquier día pasado.

2. Acepta un parámetro fecha_referencia opcional. Si se omite, usa "ahora".
   Esto permite reconstruir el estado tal como era en una fecha histórica,
   útil para auditoría y debugging.

3. La ventana es de 7 registros (no 7 días calendario): tomamos los últimos
   7 registros disponibles, sin importar si tienen huecos en las fechas.

4. cambio_emocional usa fallback: si hay <2 registros con ánimo, usamos el
   valor que el usuario respondió en la evaluación inicial.

USO
---
    from agente.state_builder import build_consolidated_state
    from agente.classifier import evaluar_desde_evaluacion

    state = build_consolidated_state(usuario_dominio)
    resultado = evaluar_desde_evaluacion(state)
    nivel = resultado["etiqueta"]  # "Muy Bajo" ... "Crítico"
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

from core.models import EvaluacionInicial, RegistroEmocional, Usuario


# ─────────────────────────────────────────────────────────────────────────────
# Configuración
# ─────────────────────────────────────────────────────────────────────────────

VENTANA_REGISTROS = 7
MIN_REGISTROS_PARA_VARIANZA = 2

_VARIANZA_UMBRAL_BAJO = 1.0
_VARIANZA_UMBRAL_ALTO = 4.0


# ─────────────────────────────────────────────────────────────────────────────
# DTO consolidado
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ConsolidatedState:
    """
    Estado consolidado que se pasa al motor.

    Expone los 19 atributos que agente/mapper.py lee vía getattr.
    No es un modelo Django; es un objeto temporal que vive solo
    durante el cálculo y se descarta después.
    """
    # ── De la evaluación inicial (no cambian con el diario) ───────────────
    edad: Optional[int] = None
    genero: Optional[str] = None
    estado_relacion: Optional[str] = None
    situacion_trabajo: Optional[str] = None
    diagnostico_previo: Optional[bool] = None
    historial_panico: Optional[bool] = None
    historial_familiar: Optional[bool] = None
    tratamiento_previo: Optional[str] = None
    apoyo_percibido: Optional[str] = None
    uso_sustancias: Optional[bool] = None
    dificultad_concentra: Optional[str] = None
    satisfaccion_laboral: Optional[int] = None

    # ── Del diario, promedio móvil de últimos 7 registros ─────────────────
    hr_sueno: Optional[float] = None
    hr_trabajo: Optional[float] = None
    hr_pantalla: Optional[float] = None
    hr_act_fis: Optional[float] = None
    estres_laboral: Optional[int] = None
    estres_academico: Optional[int] = None

    # ── Derivada: varianza del ánimo (con fallback a la inicial) ──────────
    cambio_emocional: Optional[int] = None


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _promediar(valores: list) -> Optional[float]:
    limpios = [v for v in valores if v is not None]
    if not limpios:
        return None
    return sum(limpios) / len(limpios)


def _promediar_int(valores: list) -> Optional[int]:
    avg = _promediar(valores)
    return round(avg) if avg is not None else None


def _calcular_cambio_emocional(animos: list[int], fallback: Optional[int]) -> Optional[int]:
    limpios = [a for a in animos if a is not None]
    if len(limpios) < MIN_REGISTROS_PARA_VARIANZA:
        return fallback

    var = statistics.pvariance(limpios)

    if var < _VARIANZA_UMBRAL_BAJO:
        return 1
    if var > _VARIANZA_UMBRAL_ALTO:
        return min(10, 7 + int(var - _VARIANZA_UMBRAL_ALTO))

    factor = (var - _VARIANZA_UMBRAL_BAJO) / (_VARIANZA_UMBRAL_ALTO - _VARIANZA_UMBRAL_BAJO)
    return round(2 + factor * 4)


# ─────────────────────────────────────────────────────────────────────────────
# Función principal
# ─────────────────────────────────────────────────────────────────────────────

def build_consolidated_state(
    usuario: Usuario,
    fecha_referencia: Optional[datetime] = None,
) -> ConsolidatedState:
    """
    Construye el estado consolidado de un usuario.

    Raises:
        EvaluacionInicial.DoesNotExist: si el usuario no tiene evaluación inicial.
    """
    evaluacion = EvaluacionInicial.objects.filter(
        id_usuario=usuario
    ).order_by("-id_eval").first()

    if evaluacion is None:
        raise EvaluacionInicial.DoesNotExist(
            f"El usuario {usuario.id_usuario} no tiene evaluación inicial."
        )

    qs = RegistroEmocional.objects.filter(id_usuario=usuario)
    if fecha_referencia is not None:
        qs = qs.filter(fecha_registro__lte=fecha_referencia)
    registros = list(qs.order_by("-fecha_registro")[:VENTANA_REGISTROS])

    state_kwargs = dict(
        edad=evaluacion.edad,
        genero=evaluacion.genero,
        estado_relacion=evaluacion.estado_relacion,
        situacion_trabajo=evaluacion.situacion_trabajo,
        diagnostico_previo=evaluacion.diagnostico_previo,
        historial_panico=evaluacion.historial_panico,
        historial_familiar=evaluacion.historial_familiar,
        tratamiento_previo=evaluacion.tratamiento_previo,
        apoyo_percibido=evaluacion.apoyo_percibido,
        uso_sustancias=evaluacion.uso_sustancias,
        dificultad_concentra=evaluacion.dificultad_concentra,
        satisfaccion_laboral=evaluacion.satisfaccion_laboral,
    )

    if registros:
        state_kwargs["hr_sueno"]    = _promediar([r.hr_sueno_dia    for r in registros])
        state_kwargs["hr_trabajo"]  = _promediar([r.hr_trabajo_dia  for r in registros])
        state_kwargs["hr_pantalla"] = _promediar([r.hr_pantalla_dia for r in registros])
        state_kwargs["hr_act_fis"]  = _promediar([r.hr_act_fis_dia  for r in registros])
        state_kwargs["estres_laboral"]   = _promediar_int([r.estres_laboral_dia   for r in registros])
        state_kwargs["estres_academico"] = _promediar_int([r.estres_academico_dia for r in registros])
    else:
        state_kwargs["hr_sueno"]    = evaluacion.hr_sueno
        state_kwargs["hr_trabajo"]  = evaluacion.hr_trabajo
        state_kwargs["hr_pantalla"] = evaluacion.hr_pantalla
        state_kwargs["hr_act_fis"]  = evaluacion.hr_act_fis
        state_kwargs["estres_laboral"]   = evaluacion.estres_laboral
        state_kwargs["estres_academico"] = evaluacion.estres_academico

    animos = []
    for r in registros:
        if r.animo is None:
            continue
        try:
            animos.append(int(r.animo))
        except (ValueError, TypeError):
            continue

    state_kwargs["cambio_emocional"] = _calcular_cambio_emocional(
        animos,
        fallback=evaluacion.cambio_emocional,
    )

    return ConsolidatedState(**state_kwargs)


def consolidated_state_to_dict(state: ConsolidatedState) -> dict:
    return asdict(state)
