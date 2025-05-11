from django.apps import AppConfig

class AdicionalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.adicional' # Ajuste para o nome correto do seu app

    def ready(self):
        import backend.adicional.signals