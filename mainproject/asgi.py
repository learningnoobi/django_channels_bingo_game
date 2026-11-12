import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mainproject.settings")

# Initialise Django before importing anything that touches models.
django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack  # noqa: E402
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.security.websocket import AllowedHostsOriginValidator  # noqa: E402

import bingo.routing  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        # Reject WebSocket handshakes from origins that are not in ALLOWED_HOSTS.
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter(bingo.routing.websocket_urlpatterns))
        ),
    }
)
