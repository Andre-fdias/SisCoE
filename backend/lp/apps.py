from django.apps import AppConfig


class LpConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "backend.lp"

    def ready(self):
        # Importe e registre os signals
        pass
