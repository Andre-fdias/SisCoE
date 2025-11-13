from .base import *
from decouple import config

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Cache em memória para dev
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-siscoe-dev',
    }
}

# Emails no console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Cookies e CSRF relaxados no dev
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
