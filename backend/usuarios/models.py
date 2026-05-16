"""usuarios/models.py - MindMetrics.

Modelo de autenticacion web. NO confundir con core.Usuario
(tabla de dominio del dataset ML, managed=False).

Decisiones (ver docs/ADR-001-2FA-TOTP.md):
  - email es USERNAME_FIELD (login por correo).
  - is_2fa_enabled se activa tras confirmar TOTPDevice.
  - email_verified_at lo establece la vista de verificacion.
  - El TOTP NO se almacena aqui; se delega a django-otp
    (tablas otp_totp_totpdevice y otp_static_staticdevice).
  - usuario_dominio: puente 1-a-1 hacia la tabla `usuario` (managed=False).
    Cada CustomUser creado via signup tiene su par en el dominio,
    para que evaluacion_inicial / registro_emocional puedan referenciarlo.
  - evaluacion_completada: gate UX. Mientras sea False, el middleware
    EvaluacionInicialRequiredMiddleware fuerza el formulario inicial.
"""
from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """Usuario de autenticacion web (hereda de AbstractUser)."""

    first_name = None
    last_name = None

    email = models.EmailField(unique=True)
    is_2fa_enabled = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp de verificacion de correo. NULL = pendiente.",
    )

    # Puente al dominio (Camino A).
    # db_constraint=False: la tabla `usuario` es managed=False y se crea
    # DESPUES de migrate en docker-compose; sin esta opcion la migracion
    # intentaria emitir el FOREIGN KEY SQL y fallaria. La integridad
    # referencial se mantiene a nivel ORM y se valida desde la app.
    usuario_dominio = models.OneToOneField(
        "core.Usuario",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_column="id_usuario_dominio",
        db_constraint=False,
        related_name="auth_user",
        help_text="FK 1-a-1 a la tabla de dominio usuario.",
    )

    # Gate del formulario inicial. Mientras sea False, el middleware
    # EvaluacionInicialRequiredMiddleware redirige a /evaluacion-inicial/.
    evaluacion_completada = models.BooleanField(
        default=False,
        help_text="True cuando el usuario completo su evaluacion_inicial.",
    )

    # ── Campos de perfil editable ──────────────────────────────────────────────
    edad = models.IntegerField(null=True, blank=True)
    estado_civil = models.CharField(max_length=50, blank=True, null=True)
    en_tratamiento = models.CharField(max_length=10, blank=True, null=True)
    detalle_tratamiento = models.TextField(blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "Usuario (auth)"
        verbose_name_plural = "Usuarios (auth)"
        db_table = "usuarios_customuser"

    def __str__(self) -> str:
        return f"[{self.pk}] {self.email}"
