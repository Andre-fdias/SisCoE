from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.core'

    def ready(self):
        # Esta linha não carrega signals, apenas urls.
        # Se você moveu o signal para um arquivo signals.py dentro de core,
        # então você precisaria de: import backend.core.signals
        # Mas como o signal do User está no models.py, o Django já o carrega.
        try:
            from . import urls
        except ImportError:
            pass