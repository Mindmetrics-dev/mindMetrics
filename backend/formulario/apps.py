from django.apps import AppConfig


class FormularioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'formulario'

    def ready(self):
        import formulario.receivers  # noqa: F401 — conecta los observers
