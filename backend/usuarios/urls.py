"""
usuarios/urls.py — Routing de autenticación y 2FA.

Conforme a ADR-001-2FA-TOTP §6 Fase 5.
"""
from django.urls import path

from . import views

urlpatterns = [
    # ── Consentimiento + Registro ──────────────────────────────────────────────
    path("consentimiento/", views.consentimiento, name="consentimiento"),
    path("register/", views.signup, name="register"),

    # ── Login en dos etapas ───────────────────────────────────────────────────
    path("login/", views.login_step1, name="login_step1"),
    path("login/2fa/", views.login_step2, name="login_step2"),

    # ── Enrolamiento y backup ─────────────────────────────────────────────────
    path("2fa/enroll/", views.enroll_2fa, name="enroll_2fa"),
    path("2fa/backup/", views.backup_codes, name="backup_codes"),

    # ── Logout ────────────────────────────────────────────────────────────────
    path("logout/", views.logout_view, name="logout"),

    # ── Dashboard ──────────────────────────────────────────────────────────────
    path("dashboard/", views.dashboard, name="dashboard"),
    path("", views.dashboard, name="home"),

    # ── Secciones de la app ──────────────────────────────────────────────────
    # NOTA (reorganización modular): `calendario/`, `historial/` y `recursos/`
    # se trasladaron a sus apps homónimas (calendario.urls / historial.urls /
    # recursos.urls). Aquí quedan sólo las secciones aún no fragmentadas.
    path('perfil/', views.perfil, name='perfil'),
    path("inicio/", views.dashboard, name="inicio"),
    path("perfil_inicial/", views.perfil_inicial, name="perfil_inicial"),
]
