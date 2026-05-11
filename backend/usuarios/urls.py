"""URLs de modo PREVIEW. Cada path renderiza un template con datos dummy."""
from django.urls import path
from . import views

urlpatterns = [
    # Indice (raiz)
    path('', views.template_index, name='preview_index'),

    # Pantallas principales
    path('inicio/',          views.dashboard,        name='inicio'),
    path('dashboard/',       views.dashboard,        name='dashboard'),
    path('registro_diario/', views.registro_diario,  name='registro_diario'),
    path('calendario/',      views.calendario,       name='calendario'),
    path('historial/',       views.historial,        name='historial'),
    path('recursos/',        views.recursos,         name='recursos'),
    path('perfil_inicial/',  views.perfil_inicial,   name='perfil_inicial'),

    # Auth
    path('login/',     views.login_view,    name='login'),
    path('register/',  views.register,      name='register'),
    path('logout/',    views.logout_stub,   name='logout'),

    # 2FA
    path('verify_2fa/', views.verify_2fa,  name='verify_2fa'),
    path('setup_2fa/',  views.setup_2fa,   name='setup_2fa'),
    path('resend_2fa/', views.resend_2fa,  name='resend_2fa'),
]
