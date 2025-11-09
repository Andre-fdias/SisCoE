# backend/asgi.py
import os
from django.core.asgi import get_asgi_application

# É crucial definir a variável de ambiente ANTES de qualquer importação do Django.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Inicializa a aplicação ASGI do Django. Isso carrega as configurações e prepara o app.
django_asgi_app = get_asgi_application()

# Agora que o Django está configurado, podemos importar os componentes do Channels.
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
import backend.chat.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                backend.chat.routing.websocket_urlpatterns
            )
        )
    ),
})
