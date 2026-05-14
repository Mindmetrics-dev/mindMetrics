"""
usuarios/views.py — Vistas de autenticación, 2FA y dashboard.

Flujo:
    signup → enroll_2fa → backup_codes → dashboard
    login_step1 → (si 2FA activo) login_step2 → dashboard
                  (si no)        → dashboard

Cumple con ADR-001-2FA-TOTP §6 Fase 4.
"""
from __future__ import annotations

import base64
import secrets
from io import BytesIO

import qrcode
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django_otp.decorators import otp_required
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from django_otp.plugins.otp_totp.models import TOTPDevice

from .forms import Enroll2FAForm, LoginStep1Form, LoginStep2Form, SignupForm

User = get_user_model()

# Clave de sesión para el ID de usuario que pasó la etapa 1 del login.
PENDING_2FA_KEY = "pending_2fa_user_id"

# Cantidad de backup codes (PSP §F4).
BACKUP_CODES_COUNT = 8
BACKUP_CODE_BYTES = 5  # secrets.token_hex(5) → 10 hex chars


# ─────────────────────────────────────────────────────────────────────────────
# 0. Consentimiento informado
# ─────────────────────────────────────────────────────────────────────────────
CONSENT_SESSION_KEY = "consentimiento_aceptado"


@csrf_protect
@require_http_methods(["GET", "POST"])
def consentimiento(request: HttpRequest) -> HttpResponse:
    """Muestra el consentimiento informado. Solo al aceptar se habilita el registro."""
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        request.session[CONSENT_SESSION_KEY] = True
        return redirect("register")

    return render(request, "consentimiento.html")


# ─────────────────────────────────────────────────────────────────────────────
# 1. Registro
# ─────────────────────────────────────────────────────────────────────────────
@csrf_protect
@require_http_methods(["GET", "POST"])
def signup(request: HttpRequest) -> HttpResponse:
    """Alta de usuario. Tras éxito, login automático y redirección a enrolamiento 2FA."""
    if request.user.is_authenticated:
        return redirect("dashboard")

    if not request.session.get(CONSENT_SESSION_KEY):
        return redirect("consentimiento")

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Login sin 2FA aún — la fuerza del 2FA se ejerce vía @otp_required en dashboard.
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.info(request, "Cuenta creada. Configura ahora tu autenticación de dos factores.")
            return redirect("enroll_2fa")
    else:
        form = SignupForm()

    return render(request, "register.html", {"form": form})


# ─────────────────────────────────────────────────────────────────────────────
# 2. Enrolamiento TOTP
# ─────────────────────────────────────────────────────────────────────────────
@login_required
@csrf_protect
@require_http_methods(["GET", "POST"])
def enroll_2fa(request: HttpRequest) -> HttpResponse:
    """
    GET  — Genera (o reutiliza) TOTPDevice no confirmado y muestra QR + secreto.
    POST — Verifica el primer token; si es válido, marca el device como confirmado.

    Reglas anti-duplicado:
      1. Si ya existe un TOTPDevice confirmado, no se re-enrola: se redirige.
      2. Si quedo basura (varios unconfirmed de sesiones previas), se limpia
         dejando solo uno.
    """
    # (1) Si ya hay un device confirmado, no permitir un nuevo enroll.
    if TOTPDevice.objects.filter(user=request.user, confirmed=True).exists():
        messages.info(request, "Tu 2FA ya esta habilitado.")
        return redirect("dashboard")

    # (2) Limpiar duplicados unconfirmed: dejar solo el mas reciente.
    unconfirmed = TOTPDevice.objects.filter(
        user=request.user, confirmed=False
    ).order_by("-id")
    if unconfirmed.count() > 1:
        # conservar el primero (mas reciente), borrar el resto
        unconfirmed.exclude(pk=unconfirmed.first().pk).delete()

    device, _ = TOTPDevice.objects.get_or_create(
        user=request.user,
        name="default",
        confirmed=False,
    )

    if request.method == "POST":
        form = Enroll2FAForm(request.POST)
        if form.is_valid():
            token = form.cleaned_data["token"]
            if device.verify_token(token):
                device.confirmed = True
                device.save(update_fields=["confirmed"])
                request.user.is_2fa_enabled = True
                request.user.email_verified_at = timezone.now()
                request.user.save(update_fields=["is_2fa_enabled", "email_verified_at"])
                messages.success(request, "2FA habilitado correctamente.")
                return redirect("backup_codes")
            form.add_error("token", "El código no es válido o ya expiró.")
    else:
        form = Enroll2FAForm()

    qr_b64 = _build_qr_base64(device.config_url)
    return render(
        request,
        "enroll_2fa.html",
        {
            "form": form,
            "qr_image": qr_b64,
            "secret": device.key,
            "user": request.user,
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# 3. Backup codes
# ─────────────────────────────────────────────────────────────────────────────
@login_required
@csrf_protect
@require_http_methods(["GET", "POST"])
def backup_codes(request: HttpRequest) -> HttpResponse:
    """
    Genera 8 códigos de respaldo de un solo uso al confirmar 2FA.
    Se muestran UNA sola vez. POST confirma que el usuario los guardó.
    """
    static_device, _ = StaticDevice.objects.get_or_create(
        user=request.user,
        name="backup-codes",
    )

    if request.method == "POST":
        # Confirmación del usuario; se redirige al dashboard.
        return redirect("dashboard")

    # Regenerar: eliminar tokens anteriores y crear 8 nuevos.
    StaticToken.objects.filter(device=static_device).delete()
    codes: list[str] = []
    for _ in range(BACKUP_CODES_COUNT):
        token = secrets.token_hex(BACKUP_CODE_BYTES)  # 10 chars
        StaticToken.objects.create(device=static_device, token=token)
        codes.append(token)

    return render(request, "backup_codes.html", {"codes": codes})


# ─────────────────────────────────────────────────────────────────────────────
# 4. Login etapa 1
# ─────────────────────────────────────────────────────────────────────────────
@csrf_protect
@require_http_methods(["GET", "POST"])
def login_step1(request: HttpRequest) -> HttpResponse:
    """Email + password. Si 2FA está activo, redirige a etapa 2; si no, login directo."""
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = LoginStep1Form(request.POST, request=request)
        if form.is_valid():
            user = form.user
            if user.is_2fa_enabled and _user_has_confirmed_totp(user):
                # Guardar ID en sesión y forzar etapa 2.
                request.session[PENDING_2FA_KEY] = user.pk
                # No llamar login() aún — el usuario NO está autenticado hasta superar TOTP.
                return redirect("login_step2")
            # Sin 2FA: login directo.
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            return redirect("dashboard")
    else:
        form = LoginStep1Form(request=request)

    return render(request, "login_step1.html", {"form": form})


# ─────────────────────────────────────────────────────────────────────────────
# 5. Login etapa 2
# ─────────────────────────────────────────────────────────────────────────────
@csrf_protect
@require_http_methods(["GET", "POST"])
def login_step2(request: HttpRequest) -> HttpResponse:
    """Verifica token TOTP o backup code. Solo accesible tras superar etapa 1."""
    user_id = request.session.get(PENDING_2FA_KEY)
    if not user_id:
        return redirect("login_step1")

    try:
        user = User.objects.get(pk=user_id, is_active=True)
    except User.DoesNotExist:
        request.session.pop(PENDING_2FA_KEY, None)
        return redirect("login_step1")

    if request.method == "POST":
        form = LoginStep2Form(request.POST)
        if form.is_valid():
            token = form.cleaned_data["token"]
            if _verify_2fa_token(user, token):
                # Login real + limpieza de sesión + reset axes.
                login(request, user, backend="django.contrib.auth.backends.ModelBackend")
                request.session.pop(PENDING_2FA_KEY, None)
                return redirect("dashboard")
            # Token inválido — registrar intento fallido para axes (vía signal).
            form.add_error("token", "Código incorrecto.")
    else:
        form = LoginStep2Form()

    return render(request, "login_step2.html", {"form": form, "email": user.email})


# ─────────────────────────────────────────────────────────────────────────────
# 6. Logout
# ─────────────────────────────────────────────────────────────────────────────
@require_http_methods(["POST"])
@csrf_protect
def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect("login_step1")


# ─────────────────────────────────────────────────────────────────────────────
# 7. Dashboard protegido por 2FA
# ─────────────────────────────────────────────────────────────────────────────
@login_required(login_url="login_step1", redirect_field_name="next")
def dashboard(request: HttpRequest) -> HttpResponse:
    from calendario.view import _build_week_context, _get_dashboard_summary
    hoy = timezone.localdate()
    calendario_semana = _build_week_context(hoy)
    resumen = _get_dashboard_summary(hoy)
    contexto = {
        "active_section": "inicio",
        "usuario": request.user,
        "fecha_hoy_formateada": timezone.now().strftime("%A, %d de %B - semana %W"),
        "estado_hoy": resumen["estado_hoy"],
        "riesgo": resumen["riesgo"],
        "racha": resumen["racha"],
        "sin_datos": resumen["sin_datos"],
        "recomendacion": {"texto": "Tomate 10 minutos para respirar y desconectarte."},
        "calendario_semana": calendario_semana,
    }
    return render(request, "dashboard.html", contexto)


# ─────────────────────────────────────────────────────────────────────────────
# 8. Vistas de secciones (previews)
# ─────────────────────────────────────────────────────────────────────────────
@login_required(login_url="login_step1")
def registro_diario(request: HttpRequest) -> HttpResponse:
    return render(request, "registro_diario.html", {"active_section": "registro"})


@login_required(login_url="login_step1")
def calendario(request: HttpRequest) -> HttpResponse:
    from calendario.view import _build_month_context
    hoy = timezone.localdate()
    anio = int(request.GET.get("anio", hoy.year))
    mes = int(request.GET.get("mes", hoy.month))
    start_day = request.GET.get("start_day", "monday")
    contexto = {
        "active_section": "calendario",
        **_build_month_context(anio, mes, start_day, hoy),
    }
    return render(request, "calendario.html", contexto)


@login_required(login_url="login_step1")
def historial(request: HttpRequest) -> HttpResponse:
    return render(request, "historial.html", {"active_section": "historial", "metricas": None})


@login_required(login_url="login_step1")
def recursos(request: HttpRequest) -> HttpResponse:
    contexto = {
        "active_section": "recursos",
        "recursos": [
            {
                "titulo": "Termómetro de la Rabia",
                "descripcion": "Identifica la intensidad de tu enojo en una escala visual para aprender a regularlo.",
                "beneficio": "Autoconciencia emocional.",
                "url": "/static/recursos/ejercicio1_termometro_rabia.pdf",
                "externo": True,
                "icono": "🌡️",
            },
            {
                "titulo": "Disparadores de la Rabia",
                "descripcion": "Reconoce las situaciones o pensamientos que activan tu enojo.",
                "beneficio": "Prevención de crisis.",
                "url": "/static/recursos/ejercicio2_disparadores_rabia.pdf",
                "externo": True,
                "icono": "⚡",
            },
            {
                "titulo": "Cera de Conflictos",
                "descripcion": "Técnica guiada para desescalar conflictos interpersonales.",
                "beneficio": "Resolución pacífica.",
                "url": "/static/recursos/ejercicio3_cera_conflictos.pdf",
                "externo": True,
                "icono": "🕊️",
            },
            {
                "titulo": "Hoja de Fortalezas",
                "descripcion": "Descubre y registra tus fortalezas personales para momentos difíciles.",
                "beneficio": "Refuerzo de autoestima.",
                "url": "/static/recursos/ejercicio4_hoja_fortalezas.pdf",
                "externo": True,
                "icono": "💪",
            },
            {
                "titulo": "Partes de Mí",
                "descripcion": "Explora las diferentes facetas de tu personalidad y cómo se relacionan.",
                "beneficio": "Autoconocimiento integral.",
                "url": "/static/recursos/ejercicio5_partes_de_mi.pdf",
                "externo": True,
                "icono": "🧩",
            },
            {
                "titulo": "Autorretrato",
                "descripcion": "Ejercicio creativo para representar cómo te ves y cómo te sientes.",
                "beneficio": "Expresión emocional.",
                "url": "/static/recursos/ejercicio6_autorretrato.pdf",
                "externo": True,
                "icono": "🎨",
            },
        ],
        "lineas_atencion": [
            {
                "nombre": "Línea 106",
                "telefono": "106",
                "descripcion": "Atención en salud mental en Cali",
                "horario": "24/7, gratuita desde fijos y celulares",
            },
            {
                "nombre": "Psicóloga Daniela Soto",
                "telefono": "+57 301 4646247",
                "descripcion": "Psicoterapia presencial y remota",
                "horario": "",
            },
            {
                "nombre": "Casa Matria",
                "telefono": "350 803 2031 (Diurno) / 311 612 0000 (24/7)",
                "descripcion": "Atención a mujeres — Violencia de género",
                "horario": "",
            },
        ],
    }
    return render(request, "recursos.html", contexto)


@login_required(login_url="login_step1")
def perfil_inicial(request: HttpRequest) -> HttpResponse:
    return render(request, "perfil_inicial.html", {"active_section": "perfil"})


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _build_qr_base64(payload: str) -> str:
    """Genera PNG del QR codificado en base64 (data URI ready)."""
    img = qrcode.make(payload)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _user_has_confirmed_totp(user) -> bool:
    """¿El usuario tiene al menos un TOTPDevice confirmado activo?"""
    return TOTPDevice.objects.filter(user=user, confirmed=True).exists()


def _verify_2fa_token(user, token: str) -> bool:
    """
    Intenta verificar `token` contra cualquier dispositivo confirmado.
    Cubre TOTPDevice (6 dígitos) y StaticDevice (backup codes).
    StaticDevice.verify_token consume el token (lo elimina) si es correcto.
    """
    from django_otp.plugins.otp_totp.models import TOTPDevice
    from django_otp.plugins.otp_static.models import StaticDevice

    print("\n" + "="*50)
    print(f"[2FA DEBUG] Verificando token para usuario: {user.pk}")
    print(f"[2FA DEBUG] Token recibido: '{token}' (longitud: {len(token)})")

    totp_qs = TOTPDevice.objects.filter(user=user, confirmed=True)
    static_qs = StaticDevice.objects.filter(user=user, confirmed=True)
    print(f"[2FA DEBUG] Dispositivos TOTP confirmados: {totp_qs.count()}")
    print(f"[2FA DEBUG] Dispositivos Static (backup) confirmados: {static_qs.count()}")

    # Verificar TOTP
    for device in totp_qs:
        print(f"[2FA DEBUG] Probando TOTPDevice id={device.id} ...")
        ok = device.verify_token(token)
        print(f"[2FA DEBUG]   Resultado: {ok}")
        if ok:
            print("[2FA DEBUG] ✅ Token válido (TOTP). Autenticación exitosa.")
            return True

    # Verificar códigos de respaldo (static)
    for device in static_qs:
        print(f"[2FA DEBUG] Probando StaticDevice id={device.id} ...")
        ok = device.verify_token(token)
        print(f"[2FA DEBUG]   Resultado: {ok}")
        if ok:
            print("[2FA DEBUG] ✅ Token válido (código de respaldo). Autenticación exitosa.")
            return True

    print("[2FA DEBUG] ❌ Token inválido para todos los dispositivos.")
    print("="*50 + "\n")
    return False