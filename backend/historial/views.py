"""
historial/views.py — MindMetrics
============================================================
Vista del historial: lista los registros emocionales del usuario
(fecha + emoción + nivel de riesgo calculado por el agente).
"""
from __future__ import annotations

import logging
from datetime import timedelta
from datetime import timezone as dt_tz

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Max
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils import timezone

from .models import RegistroEmocional

logger = logging.getLogger(__name__)

VENTANA_DIAS_DEFAULT = 30
VENTANA_DIAS_MAX = 365

# Mapa de etiqueta normalizada → etiqueta legible
NIVEL_LEGIBLE = {
    "muy_bajo":  "Muy Bajo",
    "bajo":      "Bajo",
    "moderado":  "Moderado",
    "alto":      "Alto",
    "critico":   "Crítico",
}

# Clase CSS por nivel de riesgo (para colorear la fila/badge)
NIVEL_CLASE = {
    "muy_bajo": "success",
    "bajo":     "success",
    "moderado": "warning",
    "alto":     "danger",
    "critico":  "danger",
}


def _preparar_registro(r) -> dict:
    emocion = getattr(r.id_emocion, "nombre_emocion", "") or "—"
    nivel_raw = r.nivel_riesgo or ""
    nivel_label = NIVEL_LEGIBLE.get(nivel_raw, nivel_raw or "Sin evaluar")
    nivel_clase = NIVEL_CLASE.get(nivel_raw, "neutral")
    return {
        "fecha": timezone.localtime(r.fecha_registro.replace(tzinfo=dt_tz.utc)).date() if r.fecha_registro else None,
        "emocion": emocion,
        "nivel_riesgo": nivel_label,
        "nivel_clase": nivel_clase,
        "hr_sueno": r.hr_sueno_dia,
        "estres_laboral": r.estres_laboral_dia,
        "estres_academico": r.estres_academico_dia,
        "estres_financiero": r.estres_financ_dia,
    }


@login_required(login_url="login_step1")
def historial(request: HttpRequest) -> HttpResponse:
    """
    Historial de registros emocionales del usuario autenticado.
    Acepta ?dias=N (1..365) para ajustar la ventana.
    """
    try:
        dias = int(request.GET.get("dias", VENTANA_DIAS_DEFAULT))
    except (TypeError, ValueError):
        dias = VENTANA_DIAS_DEFAULT
    dias = max(1, min(dias, VENTANA_DIAS_MAX))

    registros_lista = []
    resumen = None
    dominio = getattr(request.user, "usuario_dominio", None)

    if dominio is not None:
        desde = timezone.now() - timedelta(days=dias)
        qs = (
            RegistroEmocional.objects
            .select_related("id_emocion")
            .filter(id_usuario=dominio, fecha_registro__gte=desde)
            .order_by("-fecha_registro")
        )
        registros_lista = [_preparar_registro(r) for r in qs]

        if registros_lista:
            total = len(registros_lista)
            resumen = {
                "total": total,
                "primer_registro": registros_lista[-1]["fecha"],
                "ultimo_registro": registros_lista[0]["fecha"],
            }

    return render(request, "historial.html", {
        "active_section": "historial",
        "registros": registros_lista,
        "resumen": resumen,
        "ventana_dias": dias,
    })
