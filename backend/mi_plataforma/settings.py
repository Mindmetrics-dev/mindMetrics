from datetime import timedelta
from pathlib import Path
from decouple import config
import os

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent

# ─── Secret / Debug ───────────────────────────────────────────────────────────
SECRET_KEY = config(
    "DJANGO_SECRET_KEY",
    default="django-insecure-preview-key-cambiar-en-produccion",
)
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = config(
    "DJANGO_ALLOWED_HOSTS",
    default="*",
    cast=lambda v: [h.strip() for h in v.split(",")],
)

# ─── Installed Apps ───────────────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Auth / 2FA
    "django_otp",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_static",
    "axes",

    # Apps del proyecto
    # ── Núcleo / dominio ──────────────────────────────────────────────────────
    "core",          # esquema 3NF canónico (managed=False) — fuente única del DDL
    # ── Apps de dominio / autenticación ───────────────────────────────────────
    "usuarios",      # autenticación, 2FA y dashboard
    "formulario",    # onboarding y evaluación inicial
    # ── Apps modulares (capa MVT, sin tablas propias — consumen `core`) ───────
    "calendario",    # calendario emocional mensual/semanal
    "recursos",      # catálogo de recursos de apoyo + servido de PDFs
    "historial",     # historial conductual y métricas de tendencia
]

# ─── Middleware ───────────────────────────────────────────────────────────────
# IMPORTANTE (ADR W-03):
#   - OTPMiddleware DEBE ir después de AuthenticationMiddleware.
#   - AxesMiddleware DEBE ir al final.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Gate de onboarding: fuerza /evaluacion-inicial/ en el primer ingreso.
    "usuarios.middleware.EvaluacionInicialRequiredMiddleware",
    "axes.middleware.AxesMiddleware",
]

ROOT_URLCONF = "mi_plataforma.urls"

# ─── Templates ────────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [PROJECT_DIR / "frontend" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "mi_plataforma.wsgi.application"

# ─── Database ─────────────────────────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="BD_MindMetrics"),
        "USER": config("DB_USER", default="postgres"),
        "PASSWORD": config("DB_PASSWORD", default="clave123"),
        "HOST": config("DB_HOST", default="db"),
        "PORT": config("DB_PORT", default="5432"),
    }
}

# ─── Authentication backends ──────────────────────────────────────────────────
# django-axes debe ir PRIMERO para interceptar intentos fallidos.
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_USER_MODEL = "usuarios.CustomUser"

# ─── Password hashers (Argon2 primero — recomendación OWASP 2024) ─────────────
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ─── django-otp ───────────────────────────────────────────────────────────────
OTP_TOTP_ISSUER = config("OTP_TOTP_ISSUER", default="MindMetrics")

# ─── django-axes ──────────────────────────────────────────────────────────────
AXES_FAILURE_LIMIT = config("AXES_FAILURE_LIMIT", default=5, cast=int)
AXES_COOLOFF_TIME = timedelta(
    minutes=config("AXES_COOLOFF_MINUTES", default=15, cast=int)
)
AXES_LOCKOUT_PARAMETERS = ["ip_address", "username"]
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_TEMPLATE = "locked_out.html"

# ─── Localización ─────────────────────────────────────────────────────────────
LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

# ─── Login / Logout ───────────────────────────────────────────────────────────
LOGIN_URL = "/login_step1/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"

# ─── Static / Media ───────────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    PROJECT_DIR / "frontend" / "static",
    ("recursos", PROJECT_DIR / "backend" / "recursos"),
]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─── Sesión: expiración por inactividad (30 minutos) ─────────────────────────
SESSION_COOKIE_AGE = 1800          # 30 min en segundos
SESSION_SAVE_EVERY_REQUEST = True  # reinicia el contador con cada request
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # persiste aunque se cierre el tab

# settings.py
# En lugar del backend SMTP, le decimos que pinte los correos en la terminal
#EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_USER', default=None) 
EMAIL_HOST_PASSWORD = config('EMAIL_PASS', default=None)

# Dirección emisora oficial visible para el usuario caleño
DEFAULT_FROM_EMAIL = f'Soporte MindMetrics <{EMAIL_HOST_USER}>'
# ─── Seguridad (activar en producción cuando DEBUG=False) ─────────────────────
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    X_FRAME_OPTIONS = "DENY"

# HTTPS
CSRF_TRUSTED_ORIGINS = [
    'https://mindmetrics.cloud',
    'https://www.mindmetrics.cloud',
]

# X-Forwarded-Proto que envía Nginx para saber si la sesión es segura (HTTPS)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
