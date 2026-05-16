"""formulario/urls.py — MindMetrics. Routing del onboarding y registro diario."""
from django.urls import path

from . import views

urlpatterns = [
    path("evaluacion-inicial/", views.evaluacion_inicial,
         name="evaluacion_inicial"),
    path("registro-diario/", views.registro_diario,
         name="registro_diario"),
]
