"""
WSGI entry point — used by gunicorn for standard HTTP.
Daphne (ASGI) is used in production for WebSocket support.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'job_portal.settings.production'
)
application = get_wsgi_application()
