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

        import os
        import sys
        from django.core.management import call_command

        # Evita a execução duplicada do código em processos filhos do runserver
        if os.environ.get('RUN_MAIN') == 'true' or 'gunicorn' in sys.argv[0]:
            # Verifica se o ambiente é de desenvolvimento ou Docker
            # A verificação de 'gunicorn' é uma forma de identificar o ambiente do Docker
            if any(cmd in sys.argv for cmd in ['runserver', 'gunicorn']):
                call_command('create_superuser')