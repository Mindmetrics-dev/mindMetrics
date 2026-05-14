"""URL config raíz de mi_plataforma."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("usuarios.urls")),
    path("", include("formulario.urls")),
]

# Sirve estáticos en modo DEBUG (Django no los sirve en producción)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=str(settings.STATICFILES_DIRS[0]))
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
