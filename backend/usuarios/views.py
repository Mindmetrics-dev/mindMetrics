"""
Views de MindMetrics — MODO PREVIEW (no funcional).
Cada view solo renderiza su template con datos dummy.
La logica real (auth, 2FA, ML) se implementara en fases posteriores.
"""
from django.shortcuts import render
from django.http import HttpResponse


# ---------- Indice de previsualizacion ----------
def template_index(request):
    """Pagina home con links a todos los templates para verlos rapido."""
    paginas = [
        ('inicio',          'Dashboard / Inicio'),
        ('registro_diario', 'Registro diario'),
        ('calendario',      'Calendario'),
        ('historial',       'Historial'),
        ('recursos',        'Recursos'),
        ('perfil_inicial',  'Perfil inicial (anamnesis)'),
        ('login',           'Login'),
        ('register',        'Registro de cuenta'),
        ('verify_2fa',      'Verificacion 2FA'),
        ('setup_2fa',       'Setup 2FA'),
    ]

    items = ''.join(
        f'<li><a href="/{name}/" style="color:#5b6cff;text-decoration:none;font-weight:600;">{label}</a> '
        f'<code style="color:#666;font-size:.85em;">/{name}/</code></li>'
        for name, label in paginas
    )

    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>MindMetrics - Indice de previsualizacion</title>
        <style>
            body {{ font-family: 'Inter', system-ui, sans-serif; max-width: 720px;
                    margin: 48px auto; padding: 0 24px; color: #1a1a2e; }}
            h1 {{ color: #5b6cff; margin-bottom: 8px; }}
            p.lead {{ color: #555; margin-top: 0; }}
            ul {{ list-style: none; padding: 0; }}
            li {{ padding: 12px 16px; margin: 6px 0; background: #f5f6fa;
                  border-radius: 8px; border-left: 4px solid #5b6cff; }}
            li a:hover {{ text-decoration: underline; }}
            .nota {{ background: #fff8dc; padding: 12px 16px; border-radius: 8px;
                     border-left: 4px solid #f0c419; margin-top: 24px; font-size: .9em; }}
        </style>
    </head>
    <body>
        <h1>MindMetrics — Preview</h1>
        <p class="lead">Indice de plantillas. Modo no funcional: solo render visual.</p>
        <ul>{items}</ul>
        <div class="nota">
            <strong>Nota:</strong> formularios y enlaces internos no procesan datos.
            Cuando envies un POST simplemente recargara la misma vista.
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)


# ---------- Vistas principales (solo rendering) ----------
def dashboard(request):
    contexto = {
        'active_section': 'inicio',
        'usuario': {'username': 'julian'},
        'fecha_hoy_formateada': 'Domingo, 03 de Mayo - semana 18',
        'estado_hoy': {'label': 'Estable', 'hint': 'Mejora vs ayer'},
        'riesgo':    {'label': 'Moderado', 'severity': 'warning', 'hint': 'Estable esta semana'},
        'racha':     {'dias': 7, 'hint': 'Racha actual'},
        'recomendacion': {'texto': 'Tomate 10 minutos para respirar y desconectarte.'},
        # 'puntos_semana': '[3,4,2,5,4,3,4]',  # descomentar cuando exista chart.js + datos
    }
    return render(request, 'dashboard.html', contexto)


def registro_diario(request):
    return render(request, 'registro_diario.html', {'active_section': 'registro'})


def calendario(request):
    contexto = {
        'active_section': 'calendario',
        'hoy': {'dia_corto': 'Dom.', 'numero': 3, 'dia_del_anio': 123, 'semana': 18},
        'mes_visible': {'nombre': 'Mayo', 'anio': 2026},
        'anios_disponibles': [2024, 2025, 2026],
    }
    return render(request, 'calendario.html', contexto)


def historial(request):
    contexto = {
        'active_section': 'historial',
        'metricas': None,  # vacio para mostrar estado "sin datos"
    }
    return render(request, 'historial.html', contexto)


def recursos(request):
    contexto = {
        'active_section': 'recursos',
        'recursos': [
            {'titulo': 'Tecnica 4-7-8', 'descripcion': 'Respiracion guiada para reducir ansiedad.',
             'beneficio': 'Calma sistema nervioso.', 'url': '#', 'externo': False},
            {'titulo': 'Mindfulness 10 min', 'descripcion': 'Sesion corta de atencion plena.',
             'beneficio': 'Mejora foco y descanso.', 'url': '#', 'externo': False},
            {'titulo': 'Linea Amiga (Cali)', 'descripcion': 'Apoyo psicologico telefonico gratuito.',
             'beneficio': 'Apoyo profesional inmediato.', 'url': 'https://www.cali.gov.co', 'externo': True},
        ],
    }
    return render(request, 'recursos.html', contexto)


def perfil_inicial(request):
    return render(request, 'perfil_inicial.html', {})


def login_view(request):
    return render(request, 'login.html', {'form': {}})


def register(request):
    return render(request, 'register.html', {'form': {}})


def verify_2fa(request):
    return render(request, 'verify_2fa.html', {'form': {}, 'email_destino': 'demo@mindmetrics.co'})


def setup_2fa(request):
    """Vista preview sin generar QR real."""
    return render(request, 'setup_2fa.html', {'qr_image': '', 'user': {'email': 'demo@mindmetrics.co'}})


def resend_2fa(request):
    """Stub que solo redirige al verify para no romper el form."""
    from django.shortcuts import redirect
    return redirect('verify_2fa')


def logout_stub(request):
    from django.shortcuts import redirect
    return redirect('inicio')
