import os
from pathlib import Path
from django.contrib.messages import constants
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # Ajuste para 3 níveis (settings dentro de pasta)

SECRET_KEY = config('SECRET_KEY')

DEBUG = False  # Definido apenas em dev ou prod

ALLOWED_HOSTS = []

# Aplicativos instalados
INSTALLED_APPS = [
    'backend.accounts',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Terceiros
    'import_export',
    'django_extensions',
    'widget_tweaks',
    'compressor',
    'django_seed',
    'fontawesomefree',

    # Apps do projeto
    'backend.core',
    'backend.crm',
    'backend.efetivo',
    'backend.adicional',
    'backend.lp', 
    'backend.rpt',
    'backend.bm',
    'backend.municipios',
    'backend.documentos',
    'backend.agenda',
    'backend.calculadora',
    'backend.cursos',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'backend.accounts.middleware.UserActionLoggingMiddleware',
    'backend.core.middleware.JSONMessagesMiddleware',
    'backend.accounts.middleware.ForcePasswordChangeMiddleware',
    'backend.accounts.middleware.UpdateLastActivityMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

# Configurações de autenticação
AUTH_USER_MODEL = 'accounts.User'
LOGIN_REDIRECT_URL = 'core:index'

# Internacionalização
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR = True
DECIMAL_SEPARATOR = ','

# Arquivos estáticos e mídias
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Compressor
COMPRESS_ENABLED = True
COMPRESS_ROOT = BASE_DIR / 'staticfiles'

# Mensagens Django com classes CSS
MESSAGE_TAGS = {
    constants.DEBUG: 'alert-primary',
    constants.ERROR: 'alert-danger',
    constants.SUCCESS: 'alert-success',
    constants.INFO: 'alert-info',
    constants.WARNING: 'alert-warning',
}

# Logging com rotação
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '{levelname} {asctime} {module} {message}', 'style': '{'},
        'simple': {'format': '{levelname} {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'simple'},
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'debug.log',
            'maxBytes': 5 * 1024 * 1024,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {'handlers': ['console', 'file'], 'level': 'INFO'},
    'loggers': {
        'django': {'handlers': ['console', 'file'], 'level': 'INFO', 'propagate': False},
    },
}

# Configurações comuns de e-mail
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='siscoe.suporte@gmail.com')

# APIs
GROQ_API_KEY = config('GROQ_API_KEY', default=None)
WEATHER_API_KEY = config('WEATHER_API_KEY', default=None)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
