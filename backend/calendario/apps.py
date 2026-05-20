from django.apps import AppConfig


class CalendarioConfig(AppConfig):
    """
    App del calendario emocional (patrón MVT).

    No define tablas propias: consume el esquema canónico de `core`
    (RegistroEmocional, Emocion) con managed=False. Su responsabilidad
    es la vista mensual/semanal del estado emocional y los builders de
    contexto que reutiliza el dashboard.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "calendario"
    verbose_name = "Calendario emocional"
