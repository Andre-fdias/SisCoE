from .base import *

# Configurações específicas para testes
DEBUG = False

# Banco de dados em memória para testes mais rápidos
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'test_db'),
        'USER': os.environ.get('DB_USER', 'test_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'test_password'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Desabilita compressão durante testes
COMPRESS_ENABLED = False

# Password hashers mais rápidos para testes
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Cache em memória para testes
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Desabilita logging durante testes
LOGGING = {}