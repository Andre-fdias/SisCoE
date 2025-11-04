import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

# Importa o roteamento do app de chat
from backend.chat import routing as chat_routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.dev")

# Aplicação ASGI principal que suporta HTTP e WebSocket
application = ProtocolTypeRouter(
    {
        # HTTP (síncrono) - Django views normais
        "http": get_asgi_application(),
        
        # WebSocket (assíncrono) - Chat em tempo real
        "websocket": AuthMiddlewareStack(
            URLRouter(
                chat_routing.websocket_urlpatterns
            )
        ),
    }
)