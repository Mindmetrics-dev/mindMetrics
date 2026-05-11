"""URL config raiz de mi_plataforma."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('usuarios.urls')),
]

# Sirve estaticos en modo DEBUG (Django no los sirve en produccion)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=str(settings.STATICFILES_DIRS[0]))
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
