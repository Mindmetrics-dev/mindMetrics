"""URL config raiz de mi_plataforma."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),

    # --- Autenticacion, 2FA y dashboard ---
    path("", include("usuarios.urls")),
    path("", include("formulario.urls")),

    # --- Apps modulares (cada modulo expone su propio routing) ---
    path("", include("calendario.urls")),          # /calendario/
    path("", include("recursos.urls")),            # /recursos/ , /recursos/descargar/...
    path("", include("historial.urls")),           # /historial/
]

# Sirve estaticos en modo DEBUG (Django no los sirve en produccion)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=str(settings.STATICFILES_DIRS[0]))
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
