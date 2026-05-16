from django.apps import AppConfig


class HistorialConfig(AppConfig):
    """
    App de historial conductual (patrón MVT).

    No define tablas propias: consume el esquema canónico de `core`
    (RegistroEmocional, EvaluacionInicial, Emocion) con managed=False.
    Su responsabilidad es la lectura analítica: agregar los registros
    emocionales diarios del usuario y exponer métricas de tendencia.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "historial"
    verbose_name = "Historial conductual"
