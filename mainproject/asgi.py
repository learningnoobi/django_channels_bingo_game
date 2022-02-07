import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mainproject.settings")
django.setup()
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import bingo.routing




application = ProtocolTypeRouter({
  "http": get_asgi_application(),
  "websocket": AuthMiddlewareStack(
        URLRouter(
            bingo.routing.websocket_urlpatterns
        )
    ),
})