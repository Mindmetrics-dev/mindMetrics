"""
Views de MindMetrics — MODO PREVIEW (no funcional).
Cada view solo renderiza su template con datos dummy.

"""
import calendar as pycalendar
from datetime import date, timedelta

from django.shortcuts import render
from django.utils import timezone

from core.models import RegistroEmocional
from django.http import HttpResponse


MESES_CHOICES = [
    (1, 'Enero'),
    (2, 'Febrero'),
    (3, 'Marzo'),
    (4, 'Abril'),
    (5, 'Mayo'),
    (6, 'Junio'),
    (7, 'Julio'),
    (8, 'Agosto'),
    (9, 'Septiembre'),
    (10, 'Octubre'),
    (11, 'Noviembre'),
    (12, 'Diciembre'),
]

MONTH_NAMES = {value: label for value, label in MESES_CHOICES}
DAY_ABBREVIATIONS = ['Lun.', 'Mar.', 'Mié.', 'Jue.', 'Vie.', 'Sáb.', 'Dom.']
DAY_NAMES = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']


def _estado_clase(label, riesgo=''):
    texto = f'{riesgo} {label}'.strip().lower()
    if any(palabra in texto for palabra in ('critico', 'alto', 'ansios', 'triste', 'estres', 'agot')):
        return 'danger'
    if any(palabra in texto for palabra in ('moderado', 'cans', 'inestable', 'irritable')):
        return 'warning'
    if texto:
        return 'success'
    return 'neutral'


def _formatear_registro(registro):
    if not registro:
        return None

    label = getattr(registro.id_emocion, 'nombre_emocion', '') or registro.nivel_riesgo or 'Registro'
    riesgo = registro.nivel_riesgo or ''
    return {
        'label': label,
        'riesgo': riesgo,
        'estado_clase': _estado_clase(label, riesgo),
    }


def _obtener_registros_por_fecha(fecha_inicio, fecha_fin):
    try:
        registros = (
            RegistroEmocional.objects
            .select_related('id_emocion')
            .filter(fecha_registro__date__range=(fecha_inicio, fecha_fin))
            .order_by('fecha_registro')
        )

        registros_por_fecha = {}
        for registro in registros:
            registros_por_fecha[timezone.localdate(registro.fecha_registro)] = registro

        return registros_por_fecha
    except Exception:
        return {}


def _weekday_short_names(firstweekday):
    names = DAY_ABBREVIATIONS[:]
    if firstweekday == pycalendar.SUNDAY:
        return names[-1:] + names[:-1]
    return names


def _weekday_name(fecha):
    return DAY_NAMES[fecha.weekday()]


def _previous_month(year, month):
    if month == 1:
        return year - 1, 12
    return year, month - 1


def _next_month(year, month):
    if month == 12:
        return year + 1, 1
    return year, month + 1


def _build_week_context(hoy):
    fecha_inicio = hoy - timedelta(days=6)
    registros_por_fecha = _obtener_registros_por_fecha(fecha_inicio, hoy)

    dias = []
    for offset in range(7):
        fecha = fecha_inicio + timedelta(days=offset)
        registro = registros_por_fecha.get(fecha)
        estado = _formatear_registro(registro)
        dias.append({
            'fecha': fecha,
            'dia_corto': _weekday_short_names(pycalendar.MONDAY)[fecha.weekday()],
            'numero': fecha.day,
            'es_hoy': fecha == hoy,
            'estado_label': estado['label'] if estado else '',
            'estado_riesgo': estado['riesgo'] if estado else '',
            'estado_clase': estado['estado_clase'] if estado else 'empty',
        })

    return {
        'titulo': 'Estado emocional - Última semana',
        'subtitulo': 'Solo muestra resultados cuando existen encuestas registradas.',
        'dias': dias,
        'tiene_registros': any(registros_por_fecha.values()),
    }


def _build_month_context(anio, mes, start_day, hoy):
    firstweekday = pycalendar.SUNDAY if start_day == 'sunday' else pycalendar.MONDAY
    month_calendar = pycalendar.Calendar(firstweekday=firstweekday)
    first_day = date(anio, mes, 1)
    last_day = date(anio, mes, pycalendar.monthrange(anio, mes)[1])
    registros_por_fecha = _obtener_registros_por_fecha(first_day, last_day)

    dias_calendario = []
    for week in month_calendar.monthdatescalendar(anio, mes):
        for fecha in week:
            registro = registros_por_fecha.get(fecha)
            estado = _formatear_registro(registro)
            dias_calendario.append({
                'fecha': fecha,
                'numero': fecha.day,
                'es_otro_mes': fecha.month != mes,
                'es_hoy': fecha == hoy,
                'estado_label': estado['label'] if (estado and fecha.month == mes) else '',
                'estado_clase': estado['estado_clase'] if (estado and fecha.month == mes) else 'empty',
                'aria_label': f"{_weekday_name(fecha)} {fecha.day} de {MONTH_NAMES[fecha.month].lower()} de {fecha.year}",
            })

    anio_anterior, mes_anterior = _previous_month(anio, mes)
    anio_siguiente, mes_siguiente = _next_month(anio, mes)

    return {
        'hoy': {
            'dia_corto': DAY_ABBREVIATIONS[hoy.weekday()],
            'numero': hoy.day,
            'dia_del_anio': hoy.timetuple().tm_yday,
            'semana': hoy.isocalendar().week,
        },
        'mes_visible': {
            'nombre': MONTH_NAMES[mes],
            'anio': anio,
            'mes_num': mes,
            'mes_anterior_num': mes_anterior,
            'mes_siguiente_num': mes_siguiente,
            'anio_anterior': anio_anterior,
            'anio_siguiente': anio_siguiente,
        },
        'dias_calendario': dias_calendario,
        'nombres_dias': _weekday_short_names(firstweekday),
        'meses_choices': MESES_CHOICES,
        'start_day': start_day,
        'anios_disponibles': [anio - 1, anio, anio + 1],
        'leyenda': [
            {'clase': 'success', 'label': 'Estable'},
            {'clase': 'warning', 'label': 'Atención'},
            {'clase': 'danger', 'label': 'Riesgo alto'},
            {'clase': 'empty', 'label': 'Sin encuesta'},
        ],
    }


def _get_dashboard_summary(hoy):
    registros_por_fecha = _obtener_registros_por_fecha(hoy - timedelta(days=6), hoy)
    registro_hoy = registros_por_fecha.get(hoy)

    if not registro_hoy:
        return {
            'estado_hoy': None,
            'riesgo': None,
            'racha': None,
            'sin_datos': True,
        }

    return {
        'estado_hoy': {
            'label': getattr(registro_hoy.id_emocion, 'nombre_emocion', '') or 'Registro',
            'hint': 'Basado en tu encuesta de hoy',
        },
        'riesgo': {
            'label': registro_hoy.nivel_riesgo or 'Sin evaluación',
            'severity': registro_hoy.nivel_riesgo or 'warning',
            'hint': 'Calculado desde la encuesta de hoy',
        },
        'racha': {
            'dias': sum(1 for registro in registros_por_fecha.values() if registro),
            'hint': 'Registros en los últimos 7 días',
        },
        'sin_datos': False,
    }


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
    hoy = timezone.localdate()
    calendario_semana = _build_week_context(hoy)
    resumen = _get_dashboard_summary(hoy)
    contexto = {
        'active_section': 'inicio',
        'usuario': {'username': 'julian'},
        'fecha_hoy_formateada': 'Domingo, 03 de Mayo - semana 18',
        'estado_hoy': resumen['estado_hoy'],
        'riesgo': resumen['riesgo'],
        'racha': resumen['racha'],
        'sin_datos': resumen['sin_datos'],
        'recomendacion': {'texto': 'Tomate 10 minutos para respirar y desconectarte.'},
        'calendario_semana': calendario_semana,
    }
    return render(request, 'dashboard.html', contexto)


def registro_diario(request):
    return render(request, 'registro_diario.html', {'active_section': 'registro'})


def calendario(request):
    hoy = timezone.localdate()
    anio = int(request.GET.get('anio', hoy.year))
    mes = int(request.GET.get('mes', hoy.month))
    start_day = request.GET.get('start_day', 'monday')

    calendario_mes = _build_month_context(anio, mes, start_day, hoy)
    contexto = {
        'active_section': 'calendario',
        **calendario_mes,
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












