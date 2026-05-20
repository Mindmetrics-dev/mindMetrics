from django.apps import AppConfig


class RecursosConfig(AppConfig):
    """
    App de recursos de apoyo psicoeducativo (MVT).

    No define tablas propias: opera sobre el esquema canónico de `core`
    (RecursoApoyo, TipoRecurso, PresentacionRecurso) con managed=False.
    Su responsabilidad es la capa de presentación: listar recursos,
    servir los PDF físicos de backend/recursos/ y registrar la
    trazabilidad de qué recurso se mostró a qué usuario.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "recursos"
    verbose_name = "Recursos de apoyo"
