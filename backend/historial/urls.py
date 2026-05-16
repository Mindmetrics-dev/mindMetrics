"""
historial/urls.py — MindMetrics
Routing del módulo de historial conductual.

Se conserva el nombre de URL `historial` para no romper los `{% url %}`
de las plantillas que ya enlazaban a esta sección.
"""
from django.urls import path

from . import views

urlpatterns = [
    path("historial/", views.historial, name="historial"),
]
