"""URL config raiz de mi_plataforma."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views
from usuarios.forms import CustomPasswordResetForm

urlpatterns = [
    path("admin/", admin.site.urls),

    # --- Autenticacion, 2FA y dashboard ---
    path("", include("usuarios.urls")),
    path("", include("formulario.urls")),

    # --- Flujo Nativo de Restablecimiento de Contraseña vía SMTP ---
    # 1. Formulario para solicitar el restablecimiento ingresando el correo
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="password_reset.html",
            email_template_name="password_reset_email.html",
            subject_template_name="password_reset_subject.txt",
            form_class=CustomPasswordResetForm 
        ),
        name="password_reset"
    ),
    # 2. Confirmación de que el correo con el enlace ha sido enviado
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="password_reset_done.html"
        ),
        name="password_reset_done"
    ),
    # 3. Formulario seguro donde el usuario ingresa su nueva contraseña (valida el token dinámico)
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="password_reset_confirm.html"
        ),
        name="password_reset_confirm"
    ),
    # 4. Pantalla final informando el éxito del proceso y enlace al Login
    path(
        "password-reset-complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="password_reset_complete.html"
        ),
        name="password_reset_complete"
    ),

    # --- Apps modulares (cada modulo expone su propio routing) ---
    path("", include("calendario.urls")),          
    path("", include("recursos.urls")),             
    path("", include("historial.urls")),            
]

# Sirve estaticos en modo DEBUG (Django no los sirve en produccion)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=str(settings.STATICFILES_DIRS[0]))
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)