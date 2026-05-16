"""
calendario/urls.py — MindMetrics
Routing del módulo de calendario emocional.

Se conserva el nombre de URL `calendario` para no romper los `{% url %}`
de las plantillas que ya enlazaban a esta sección.
"""
from django.urls import path

from . import views

urlpatterns = [
    path("calendario/", views.calendario, name="calendario"),
]
