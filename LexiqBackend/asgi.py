"""
ASGI config for LexiqBackend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""
import os



from django.core.asgi import get_asgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LexiqBackend.settings')
django_asgi_application = get_asgi_application()
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from Rooms.routing import websocket_urlpatterns
from MainChat.routing import websocket_urlpatterns as chat_websocket_urlpatterns


application = ProtocolTypeRouter({
    "http": django_asgi_application,
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns + chat_websocket_urlpatterns)
    ),
})
