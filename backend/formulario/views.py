"""
formulario/views.py — MindMetrics

Vista del onboarding obligatorio: evaluacion_inicial.

Flujo:
  signup -> enroll_2fa -> backup_codes -> evaluacion_inicial -> dashboard
  ^                                       ^
  Auto-crea usuario_dominio               Persiste EvaluacionInicial,
                                          invoca agente/classifier.py,
                                          crea RegistroEmocional inicial,
                                          marca evaluacion_completada=True
"""
from __future__ import annotations

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from core.models import Emocion, RegistroEmocional, Usuario as UsuarioDominio
from agente.classifier import evaluar_desde_evaluacion
from .forms import EvaluacionInicialForm

logger = logging.getLogger(__name__)

# Nombre de la emoción "semilla" que se crea junto al registro inicial.
# Debe existir en la tabla `emocion` (o se crea con get_or_create).
_EMOCION_EVALUACION = "Evaluación inicial"


@login_required(login_url="login_step1")
@csrf_protect
@require_http_methods(["GET", "POST"])
def evaluacion_inicial(request: HttpRequest) -> HttpResponse:
    """
    GET  — Muestra el formulario completo (4 secciones).
    POST — Persiste 1 fila en `evaluacion_inicial`, ejecuta el sistema
           experto (agente/) y crea el primer RegistroEmocional con el
           nivel de riesgo calculado. Finalmente marca evaluacion_completada=True.

    Si el usuario ya completó la evaluación, redirige al dashboard
    (anti-doble-submit y comportamiento idempotente).
    """
    if request.user.evaluacion_completada:
        return redirect("dashboard")

    # Garantizar usuario_dominio (defensivo: usuarios creados antes de la
    # migración del puente podrían no tenerlo).
    if request.user.usuario_dominio_id is None:
        dominio = UsuarioDominio.objects.create(
            email=request.user.email,
            password=request.user.password,
            nickname=request.user.username,
            activo=True,
            consentimiento_aceptado=False,
            two_fa_habilitado=request.user.is_2fa_enabled,
        )
        request.user.usuario_dominio = dominio
        request.user.save(update_fields=["usuario_dominio"])

    if request.method == "POST":
        form = EvaluacionInicialForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # 1. Persistir evaluacion_inicial
                evaluacion = form.save(commit=False)
                evaluacion.id_usuario = request.user.usuario_dominio
                evaluacion.save()

                # 2. Ejecutar sistema experto
                try:
                    resultado = evaluar_desde_evaluacion(evaluacion)
                    etiqueta_riesgo = resultado["etiqueta"]   # "Bajo", "Moderado", etc.
                    nivel_riesgo    = str(resultado["nivel_riesgo"])  # "1"–"5"
                except Exception:
                    logger.exception(
                        "Error al ejecutar el clasificador de riesgo "
                        "para usuario %s", request.user.pk
                    )
                    etiqueta_riesgo = None
                    nivel_riesgo    = None

                # 3. Crear el primer RegistroEmocional con el nivel calculado
                emocion, _ = Emocion.objects.get_or_create(
                    nombre_emocion=_EMOCION_EVALUACION
                )
                RegistroEmocional.objects.create(
                    id_usuario=request.user.usuario_dominio,
                    id_emocion=emocion,
                    nivel_riesgo=etiqueta_riesgo,
                )

                # 4. Marcar onboarding como completado
                request.user.evaluacion_completada = True
                request.user.save(update_fields=["evaluacion_completada"])

            messages.success(
                request,
                "¡Listo! Tu evaluación inicial fue registrada correctamente.",
            )
            return redirect("dashboard")
    else:
        form = EvaluacionInicialForm()

    return render(
        request,
        "evaluacion_inicial.html",
        {"form": form, "active_section": "perfil"},
    )
