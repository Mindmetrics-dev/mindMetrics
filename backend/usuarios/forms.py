"""
usuarios/forms.py — Formularios de autenticación y 2FA.

Diseño:
  - SignupForm: alta de usuario con validación robusta (Argon2 + validators de Django).
  - LoginStep1Form: email + password (primera etapa).
  - LoginStep2Form: token TOTP o backup code (segunda etapa).
  - Enroll2FAForm: confirmación inicial del TOTPDevice.
"""
from __future__ import annotations

from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction

from core.models import Usuario as UsuarioDominio

User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
# 1. Registro
# ─────────────────────────────────────────────────────────────────────────────
class SignupForm(forms.ModelForm):
    """
    Formulario de alta de usuario.

    Validaciones:
      - email único (forzado por modelo).
      - password1 == password2.
      - password cumple AUTH_PASSWORD_VALIDATORS (longitud, no común, etc.).
    """

    username = forms.CharField(
        max_length=150,
        required=True,
    )
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        strip=False,
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        strip=False,
    )

    class Meta:
        model = User
        fields = ("email", "username")
        widgets = {
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
        }

    def clean_email(self) -> str:
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Ya existe un usuario con este correo.")
        return email

    def clean_password2(self) -> str:
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise ValidationError("Las contraseñas no coinciden.")
        if p2:
            validate_password(p2, user=User(email=self.cleaned_data.get("email", "")))
        return p2

    @transaction.atomic
    def save(self, commit: bool = True):  # type: ignore[override]
        """
        Crea el CustomUser y, en la misma transaccion, su par en la tabla
        de dominio `usuario`. El password Argon2 se replica para mantener
        coherencia (los registros ETL del CSV tambien usan hash Django).
        """
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        # Crear contraparte en la tabla `usuario` (dominio, managed=False)
        dominio = UsuarioDominio.objects.create(
            email=user.email,
            password=user.password,          # hash Argon2 ya aplicado
            nickname=user.username,
            activo=True,
            consentimiento_aceptado=False,   # se firma luego
            two_fa_habilitado=False,
        )
        user.usuario_dominio = dominio

        if commit:
            user.save()
        return user


# ─────────────────────────────────────────────────────────────────────────────
# 2. Login etapa 1
# ─────────────────────────────────────────────────────────────────────────────
class LoginStep1Form(forms.Form):
    """email + password. Retorna user autenticado en clean()."""

    email = forms.EmailField(
        label="Correo",
        widget=forms.EmailInput(attrs={"class": "form-group__input","placeholder": "Email","autocomplete": "email", "autofocus": True}),
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-group__input","placeholder": "Contraseña","autocomplete": "current-password"}),
        strip=False,
    )

    def __init__(self, *args, request=None, **kwargs) -> None:
        self.request = request
        self.user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email")
        password = cleaned.get("password")
        if email and password:
            # `authenticate` invoca AxesStandaloneBackend + ModelBackend.
            user = authenticate(self.request, username=email, password=password)
            if user is None:
                raise ValidationError("Credenciales inválidas.")
            if not user.is_active:
                raise ValidationError("Cuenta inactiva.")
            self.user = user
        return cleaned


# ─────────────────────────────────────────────────────────────────────────────
# 3. Login etapa 2 / Enrolamiento TOTP — comparten estructura
# ─────────────────────────────────────────────────────────────────────────────
class _TokenFormBase(forms.Form):
    """Base para formularios que aceptan tokens TOTP (6 dígitos) o backup (10 hex)."""

    token = forms.CharField(
        label="Código",
        min_length=6,
        max_length=16,
        widget=forms.TextInput(attrs={
            "autocomplete": "one-time-code",
            "inputmode": "numeric",
            "autofocus": True,
        }),
    )

    def clean_token(self) -> str:
        return self.cleaned_data["token"].strip().replace(" ", "").replace("-", "")


class LoginStep2Form(_TokenFormBase):
    """Segunda etapa del login. Acepta TOTP de 6 dígitos o backup code."""


class Enroll2FAForm(_TokenFormBase):
    """Confirmación inicial del TOTPDevice tras escanear el QR."""
