import os
import django
from django.core.asgi import get_asgi_application

# ⚠️ CONFIGURAÇÃO CRÍTICA - Deve vir primeiro
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

# ⚠️ INICIALIZA DJANGO ANTES de importar Channels
django.setup()

# Agora importe os componentes do Channels
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
import backend.chat.routing

# Aplicação HTTP padrão do Django
django_asgi_app = get_asgi_application()

print("🚀 Inicializando ASGI Application com Daphne...")
print("✅ Django configurado")
print("✅ Channels carregado")
print("✅ WebSocket patterns:", backend.chat.routing.websocket_urlpatterns)

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