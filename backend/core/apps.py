from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.core'

    def ready(self):
        # Para usar namespace 'core'
        try:
            from . import urls
        except ImportError:
            pass