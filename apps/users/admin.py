from django.contrib import admin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'nickname', 'is_staff', 'consentimiento_aceptado')
    search_fields = ('email', 'nickname')
    readonly_fields = ('date_joined',)

    # Organiza los campos por secciones en el formulario
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información Personal', {'fields': ('nickname',)}),
        ('Seguridad y Ética', {'fields': ('consentimiento_aceptado', 'dos_factores_habilitado')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas Importantes', {'fields': ('date_joined',)}),
    )