import os
from pathlib import Path
from django.contrib.messages import constants
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY: Use config com valor padrão para desenvolvimento
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-only')

# DEBUG deve ser configurável por ambiente
DEBUG = config('DEBUG', default=False, cast=bool)

# ALLOWED_HOSTS deve ser configurável
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())

# Configuração de banco de dados - compatível com Docker e local
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django_prometheus.db.backends.postgresql'),
        'NAME': config('DB_NAME', default=config('DATABASE_URL', default='siscoe_db')),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Se DATABASE_URL estiver definida, usa ela (para compatibilidade)
if config('DATABASE_URL', default=None):
    import dj_database_url
    DATABASES['default'] = dj_database_url.config(
        default=config('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )

# ============ CONFIGURAÇÕES DE EMAIL CORRIGIDAS ============

# Configuração específica para Brevo API (usada pelo seu código)
BREVO_API_KEY = config('BREVO_API_KEY', default='')

# Configurações SMTP para fallback (se necessário)
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp-relay.brevo.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='andrefonsecadias21@gmail.com')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default=BREVO_API_KEY)  # Usa a mesma API Key

DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='andrefonsecadias21@gmail.com')
DEFAULT_FROM_NAME = config('DEFAULT_FROM_NAME', default='SisCoE Sistema')

# ============ FIM DAS CONFIGURAÇÕES DE EMAIL ============

# Restante das configurações permanecem iguais...
INSTALLED_APPS = [
    'django_prometheus',
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
    'backend.tickets',
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
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
    'django_prometheus.middleware.PrometheusAfterMiddleware',
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
                'backend.core.context_processors.version_context_processor',
                'backend.tickets.context_processors.tickets_count',
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

# APIs
GROQ_API_KEY = config('GROQ_API_KEY', default=None)
WEATHER_API_KEY = config('WEATHER_API_KEY', default=None)

# Telegram (para alertas)
TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN', default=None)
TELEGRAM_CHAT_ID = config('TELEGRAM_CHAT_ID', default=None)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging
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
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {'handlers': ['console', 'file'], 'level': 'INFO'},
    'loggers': {
        'django': {'handlers': ['console', 'file'], 'level': 'INFO', 'propagate': False},
        'backend.accounts': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}