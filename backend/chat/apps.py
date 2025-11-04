from django.apps import AppConfig

class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.chat'
    
    def ready(self):
        # Remova ou comente esta linha por enquanto
        # import backend.chat.signals
        pass