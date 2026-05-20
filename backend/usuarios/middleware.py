"""
usuarios/middleware.py — MindMetrics

EvaluacionInicialRequiredMiddleware
-----------------------------------
Si el usuario esta autenticado y `evaluacion_completada == False`, se
le redirige a la vista `evaluacion_inicial` antes de servir cualquier
ruta de la app.

Whitelist (no se intercepta):
  - URL de la propia evaluacion (anti-loop).
  - Login (etapas 1 y 2), logout, signup.
  - Flujo 2FA: enroll, backup codes.
  - Admin de Django.
  - Estaticos / media.

Decision de diseno (ADR W-04):
  - Se usa middleware y no decorador @evaluacion_required en cada vista
    porque el patron debe ser global: si manana se anaden mas vistas, el
    gate debe seguir activo sin tocar cada view.
  - El middleware se ejecuta DESPUES de AuthenticationMiddleware (para
    tener request.user).
"""
from __future__ import annotations

from django.conf import settings
from django.shortcuts import redirect
from django.urls import resolve, reverse, Resolver404


class EvaluacionInicialRequiredMiddleware:
    """Fuerza el formulario inicial en el primer ingreso del usuario."""

    # URL names que NO deben ser interceptadas (pueden seguir accesibles).
    EXEMPT_URL_NAMES = frozenset({
        "evaluacion_inicial",
        "login_step1",
        "login_step2",
        "register",
        "logout",
        "enroll_2fa",
        "backup_codes",
    })

    # Prefijos de path exentos (admin, static, media).
    EXEMPT_PATH_PREFIXES = (
        "/admin/",
        getattr(settings, "STATIC_URL", "/static/"),
        getattr(settings, "MEDIA_URL", "/media/"),
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._should_redirect(request):
            return redirect(reverse("evaluacion_inicial"))
        return self.get_response(request)

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _should_redirect(self, request) -> bool:
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            return False
        if getattr(user, "evaluacion_completada", False):
            return False

        # Exencion por prefijo (admin, static, media)
        path = request.path or ""
        for prefix in self.EXEMPT_PATH_PREFIXES:
            if prefix and path.startswith(prefix):
                return False

        # Exencion por url_name
        try:
            match = resolve(path)
        except Resolver404:
            return False
        if match.url_name in self.EXEMPT_URL_NAMES:
            return False

        return True
