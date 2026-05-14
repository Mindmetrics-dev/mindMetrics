from django.contrib import admin
from django.urls import path

urlpatterns = [
    # Ruta por defecto para el panel de administración
    path('admin/', admin.site.urls),
]