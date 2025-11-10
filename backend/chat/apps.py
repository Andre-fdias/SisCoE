# backend/chat/apps.py - CORRIGIDO
from django.apps import AppConfig

class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.chat'
    
    def ready(self):
        # Descomente esta linha para ativar os signals
        import backend.chat.signals