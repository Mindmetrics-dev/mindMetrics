"""formulario/urls.py — MindMetrics. Routing del onboarding."""
from django.urls import path

from . import views

urlpatterns = [
    path("evaluacion-inicial/", views.evaluacion_inicial,
         name="evaluacion_inicial"),
]
