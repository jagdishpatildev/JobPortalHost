import os
import django

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'job_portal.settings.production'
)

# MUST call setup() before importing anything from Django apps.
# This is what fixes AppRegistryNotReady.
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from jobs import routing

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(routing.websocket_urlpatterns)
    ),
})
