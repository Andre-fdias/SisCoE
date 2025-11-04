import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.dev')

# Aplicação WSGI para servidores tradicionais (síncronos)
application = get_wsgi_application()