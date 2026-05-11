#!/usr/bin/env python
"""MindMetrics - Utilidad de línea de comandos para la gestión del proyecto Django."""

import os
import sys


def main():
    """Ejecuta las tareas administrativas de MindMetrics."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_plataforma.settings')

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. Asegúrate de que esté instalado y "
            "disponible en tu variable de entorno PYTHONPATH. ¿Olvidaste "
            "activar el entorno virtual (venv)? ¿O verificar la instalación "
            "de dependencias con 'pip install -r requirements.txt'?"
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
