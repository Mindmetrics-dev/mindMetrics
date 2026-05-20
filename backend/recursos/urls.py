"""
recursos/urls.py — MindMetrics
Routing del módulo de recursos de apoyo.

Se conserva el nombre de URL `recursos` para no romper los `{% url %}`
de las plantillas que ya enlazaban a esta sección.
"""
from django.urls import path

from . import views

urlpatterns = [
    path("recursos/", views.lista_recursos, name="recursos"),
    path("recursos/descargar/<int:id_recurso>/",
         views.descargar_recurso, name="descargar_recurso"),
    path("recursos/descargar/archivo/<str:nombre>/",
         views.descargar_recurso_estatico, name="descargar_recurso_estatico"),
]
