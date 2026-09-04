import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django_asgi_application = get_asgi_application()

from bloomerp.router import router
from config.project_channels import websocket_urlpatterns as project_websocket_urlpatterns


websocket_urlpatterns = [
    *router.create_websocket_url_patterns(),
    *project_websocket_urlpatterns,
]

application = ProtocolTypeRouter(
    {
        "http": django_asgi_application,
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
