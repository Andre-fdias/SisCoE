# dev.py (CORREÇÕES APLICADAS)
from .base import *
from decouple import config

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', 'web']  # ADICIONADO hosts para Docker

# Usar PostgreSQL mesmo em desenvolvimento para consistência
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='siscoe_db'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='davi2807'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Fallback para SQLite se PostgreSQL não estiver disponível
try:
    import psycopg2
    # Testa conexão com PostgreSQL
    conn = psycopg2.connect(
        dbname=config('DB_NAME', default='siscoe_db'),
        user=config('DB_USER', default='postgres'),
        password=config('DB_PASSWORD', default='davi2807'),
        host=config('DB_HOST', default='localhost'),
        port=config('DB_PORT', default='5432'),
    )
    conn.close()
except:
    # Fallback para SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# # Cache em memória para dev
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#         'LOCATION': 'unique-siscoe-dev',
#     }
# }

# Emails no console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Cookies e CSRF relaxados no dev
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# Configurações específicas para desenvolvimento
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'  # Usar em memória para dev
    }
}

# Permitir todos os hosts em desenvolvimento
ALLOWED_HOSTS = ['*']