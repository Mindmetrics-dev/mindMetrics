"""
calendario/views.py — MindMetrics
============================================================
Vistas y helpers del módulo `calendario` (patrón MVT).

  - `calendario`            — vista funcional del calendario mensual.
  - `_build_week_context`   — resumen de la última semana (lo consume
                              también `usuarios.views.dashboard`).
  - `_build_month_context`  — malla mensual con estado emocional por día.
  - `_get_dashboard_summary`— tarjetas-resumen del dashboard.

Fuente de datos: `RegistroEmocional` (esquema canónico de `core`,
managed=False). Todos los queries están filtrados por el usuario
autenticado para aislar datos entre cuentas.
"""
from __future__ import annotations

import calendar as pycalendar
from datetime import date, datetime, time as dt_time, timedelta
from datetime import timezone as dt_tz

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from .models import RegistroEmocional


def _to_local_date(dt):
    """Convierte datetime naive-UTC a fecha local (America/Bogota).

    fecha_registro se guarda como UTC naive (auto_now_add con USE_TZ=True).
    Llamar .date() directamente devuelve la fecha UTC; después de las 19:00
    Bogota (= 00:00 UTC) el registro aparece en el día siguiente.
    """
    if dt is None:
        return None
    return timezone.localtime(dt.replace(tzinfo=dt_tz.utc)).date()

# ─────────────────────────────────────────────────────────────────────────────
# Constantes de localización
# ─────────────────────────────────────────────────────────────────────────────
MESES_CHOICES = [
    (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
    (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
    (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre'),
]
MONTH_NAMES = {value: label for value, label in MESES_CHOICES}
DAY_ABBREVIATIONS = ['Lun.', 'Mar.', 'Mié.', 'Jue.', 'Vie.', 'Sáb.', 'Dom.']
DAY_NAMES = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de presentación
# ─────────────────────────────────────────────────────────────────────────────
def _estado_clase(label, riesgo=''):
    texto = f'{riesgo} {label}'.strip().lower()
    if any(p in texto for p in ('critico', 'alto', 'ansios', 'triste', 'estres', 'agot')):
        return 'danger'
    if any(p in texto for p in ('moderado', 'cans', 'inestable', 'irritable')):
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


def _utc_naive_range(fecha_inicio, fecha_fin):
    """Convierte un rango de fechas locales al rango naive-UTC para filtrar fecha_registro."""
    inicio = timezone.make_aware(datetime.combine(fecha_inicio, dt_time.min))
    fin    = timezone.make_aware(datetime.combine(fecha_fin,    dt_time.max))
    return (
        inicio.astimezone(timezone.utc).replace(tzinfo=None),
        fin.astimezone(timezone.utc).replace(tzinfo=None),
    )


def _obtener_registros_por_fecha(fecha_inicio, fecha_fin, usuario=None):
    """Mapa {date_local: RegistroEmocional} para el rango dado, filtrado por usuario."""
    try:
        inicio_utc, fin_utc = _utc_naive_range(fecha_inicio, fecha_fin)
        qs = (
            RegistroEmocional.objects
            .select_related('id_emocion')
            .filter(fecha_registro__range=(inicio_utc, fin_utc))
            .order_by('fecha_registro')
        )
        if usuario is not None:
            qs = qs.filter(id_usuario=usuario)
        return {
            _to_local_date(r.fecha_registro): r
            for r in qs
        }
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


# ─────────────────────────────────────────────────────────────────────────────
# Builders de contexto (reutilizados por el dashboard)
# ─────────────────────────────────────────────────────────────────────────────
def _build_week_context(hoy, usuario=None):
    """Resumen de los últimos 7 días. Consumido por usuarios.views.dashboard."""
    fecha_inicio = hoy - timedelta(days=6)
    registros_por_fecha = _obtener_registros_por_fecha(fecha_inicio, hoy, usuario)

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


def _build_month_context(anio, mes, start_day, hoy, usuario=None):
    """Malla mensual completa con estado emocional por día."""
    firstweekday = pycalendar.SUNDAY if start_day == 'sunday' else pycalendar.MONDAY
    month_calendar = pycalendar.Calendar(firstweekday=firstweekday)
    first_day = date(anio, mes, 1)
    last_day = date(anio, mes, pycalendar.monthrange(anio, mes)[1])
    registros_por_fecha = _obtener_registros_por_fecha(first_day, last_day, usuario)

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
                'aria_label': (
                    f"{_weekday_name(fecha)} {fecha.day} de "
                    f"{MONTH_NAMES[fecha.month].lower()} de {fecha.year}"
                ),
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


def _get_dashboard_summary(hoy, usuario=None):
    """Tarjetas-resumen del dashboard (estado de hoy, riesgo, racha)."""
    registros_por_fecha = _obtener_registros_por_fecha(hoy - timedelta(days=6), hoy, usuario)
    registro_hoy = registros_por_fecha.get(hoy)

    dias_con_registro = sum(1 for r in registros_por_fecha.values() if r)
    racha = {
        'dias': dias_con_registro,
        'hint': 'Registros en los últimos 7 días',
    }

    if not registro_hoy:
        return {
            'estado_hoy': None,
            'riesgo': None,
            'racha': racha,
            'sin_datos': True,
        }

    _nivel_legible = {
        "muy_bajo": "Muy Bajo",
        "bajo":     "Bajo",
        "moderado": "Moderado",
        "alto":     "Alto",
        "critico":  "Crítico",
    }
    nivel_raw = registro_hoy.nivel_riesgo or ""
    nivel_label = _nivel_legible.get(nivel_raw, nivel_raw.replace("_", " ").title() if nivel_raw else "Sin evaluación")
    return {
        'estado_hoy': {
            'label': getattr(registro_hoy.id_emocion, 'nombre_emocion', '') or 'Registro',
            'hint': 'Basado en tu encuesta de hoy',
        },
        'riesgo': {
            'label': nivel_label,
            'severity': nivel_raw or 'warning',
            'hint': 'Calculado desde la encuesta de hoy',
        },
        'racha': racha,
        'sin_datos': False,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Vista funcional
# ─────────────────────────────────────────────────────────────────────────────
@login_required(login_url="login_step1")
def calendario(request: HttpRequest) -> HttpResponse:
    """
    Calendario mensual del estado emocional.

    Acepta `?anio=`, `?mes=` y `?start_day=monday|sunday`. Por defecto
    muestra el mes corriente con la semana iniciando en lunes.
    """
    hoy = timezone.localdate()
    try:
        anio = int(request.GET.get('anio', hoy.year))
        mes = int(request.GET.get('mes', hoy.month))
    except (TypeError, ValueError):
        anio, mes = hoy.year, hoy.month
    if not 1 <= mes <= 12:
        mes = hoy.month

    start_day = request.GET.get('start_day', 'monday')
    if start_day not in ('monday', 'sunday'):
        start_day = 'monday'

    usuario = getattr(request.user, 'usuario_dominio', None)

    evaluacion_hoy = bool(
        _obtener_registros_por_fecha(hoy, hoy, usuario).get(hoy)
    )

    contexto = {
        'active_section': 'calendario',
        'evaluacion_hoy': evaluacion_hoy,
        **_build_month_context(anio, mes, start_day, hoy, usuario),
    }
    return render(request, 'calendario.html', contexto)
