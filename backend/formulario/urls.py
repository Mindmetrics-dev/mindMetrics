"""formulario/urls.py — MindMetrics. Routing del onboarding y registro diario."""
from django.urls import path

from . import views
from .actualizacion import views as act_views

urlpatterns = [
    path("evaluacion-inicial/", views.evaluacion_inicial,
         name="evaluacion_inicial"),
    path("registro-diario/", act_views.registro_diario,
         name="registro_diario"),
    path("registro-diario/resultado/", act_views.resultado_diario,
         name="resultado_diario"),
]
