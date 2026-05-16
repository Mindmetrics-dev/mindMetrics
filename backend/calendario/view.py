"""
calendario/view.py — SHIM DE COMPATIBILIDAD (DEPRECADO)
============================================================
Este archivo quedó obsoleto tras la reorganización modular.
La lógica real vive ahora en `calendario/views.py` (nombre convencional
de Django).

Se conserva únicamente como puente de compatibilidad: cualquier import
antiguo del tipo `from calendario.view import _build_month_context`
sigue funcionando, pero debe migrarse a `from calendario.views import ...`.

TODO: eliminar este archivo cuando se confirme que ningún módulo
      importa `calendario.view` (revisar con: grep -r "calendario.view ").
"""
from .views import (  # noqa: F401  (re-export intencional)
    MESES_CHOICES,
    MONTH_NAMES,
    _build_month_context,
    _build_week_context,
    _get_dashboard_summary,
    _obtener_registros_por_fecha,
    calendario,
)

__all__ = [
    "calendario",
    "_build_week_context",
    "_build_month_context",
    "_get_dashboard_summary",
    "_obtener_registros_por_fecha",
    "MESES_CHOICES",
    "MONTH_NAMES",
]
