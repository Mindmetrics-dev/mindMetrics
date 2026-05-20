"""
ASGI config for mi_plataforma project.
"""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_plataforma.settings')

application = get_asgi_application()
