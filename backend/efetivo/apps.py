from django.apps import AppConfig


class EfetivoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.efetivo'

    def ready(self):
        # Importa e conecta os sinais de métricas do Prometheus
        import backend.efetivo.signals
