"""
formulario/views.py — MindMetrics
====================================
Vistas de onboarding (evaluacion_inicial) y registro diario.

Flujo onboarding:
  signup -> enroll_2fa -> backup_codes -> evaluacion_inicial -> dashboard

Flujo diario:
  dashboard -> registro_diario -> historial (o recursos si riesgo alto/critico)
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

from django.utils import timezone

from core.models import Emocion, RegistroEmocional, Usuario as UsuarioDominio
from agente.classifier import evaluar_desde_evaluacion
from . import services
from .forms import EMOCION_CHOICES, EvaluacionInicialForm, RegistroDiarioForm

logger = logging.getLogger(__name__)

_EMOCION_EVALUACION = "Evaluación inicial"

_NIVEL_LEGIBLE = {
    "muy_bajo": "Muy Bajo",
    "bajo":     "Bajo",
    "moderado": "Moderado",
    "alto":     "Alto",
    "critico":  "Crítico",
}

_PSICOLOGA_CONTACTO = (
    "Psicóloga Daniela Soto · +57 301 4646247 · Psicoterapia presencial y remota"
)


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


# ─────────────────────────────────────────────────────────────────────────────
# Registro diario
# ─────────────────────────────────────────────────────────────────────────────

@login_required(login_url="login_step1")
@csrf_protect
@require_http_methods(["GET", "POST"])
def registro_diario(request: HttpRequest) -> HttpResponse:
    """
    GET  — Muestra el formulario; bloquea si ya registró hoy.
    POST — Valida, delega al service, y redirige.
           Si el nivel es alto/crítico → recursos con alerta de contacto.
    """
    dominio = getattr(request.user, "usuario_dominio", None)
    if dominio and services._ya_registro_en_fecha(dominio, timezone.localdate()):
        messages.success(
            request,
            "Ya completaste tu registro diario. Aquí puedes ver tu estado actual. "
            "O en historial verificar los datos registrados.",
        )
        return redirect("dashboard")

    if request.method == "POST":
        form = RegistroDiarioForm(request.POST)
        if form.is_valid():
            try:
                registro = services.submit_registro_diario(
                    usuario_dominio=request.user.usuario_dominio,
                    datos=form.cleaned_data,
                )
            except services.YaRegistroHoy:
                messages.warning(request, "Ya registraste tu registro diario. Vuelve mañana para registrar otro.")
                return redirect("dashboard")
            except services.EvaluacionInicialFaltante:
                messages.error(request, "Necesitas completar tu evaluación inicial antes de registrar el diario.")
                return redirect("evaluacion_inicial")
            except Exception:
                logger.exception("Error en el flujo de registro diario para usuario %s", request.user.pk)
                messages.error(request, "Ocurrió un error al guardar tu registro. Inténtalo de nuevo.")
                return redirect("registro_diario")

            nivel = registro.nivel_riesgo or ""
            etiqueta = _NIVEL_LEGIBLE.get(
                nivel, nivel.replace("_", " ").title() if nivel else "Sin evaluar"
            )

            if nivel in ("alto", "critico"):
                messages.error(
                    request,
                    f"⚠️ Tu nivel de riesgo es {etiqueta}. "
                    f"Te recomendamos comunicarte con la {_PSICOLOGA_CONTACTO}.",
                )
                return redirect("recursos")

            messages.success(request, f"Registro guardado. Nivel de riesgo: {etiqueta}.")
            return redirect("historial")
    else:
        form = RegistroDiarioForm()

    return render(
        request,
        "registro_diario.html",
        {
            "form": form,
            "emociones_choices": EMOCION_CHOICES,
            "active_section": "registro",
        },
    )


@login_required(login_url="login_step1")
@require_http_methods(["GET"])
def resultado_diario(request: HttpRequest) -> HttpResponse:
    resultado = request.session.pop("resultado_diario", None)
    if not resultado:
        return redirect("dashboard")
    return render(
        request,
        "resultado_registro.html",
        {"resultado": resultado, "active_section": "registro"},
    )
