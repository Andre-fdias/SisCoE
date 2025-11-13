import os
from pathlib import Path
from django.contrib.messages import constants
from decouple import config, Csv

# ============ CONFIGURAÇÕES DE CAMINHOS ============
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ============ CONFIGURAÇÕES BÁSICAS ============
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-change-in-production')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())

# ============ APLICAÇÕES INSTALADAS ============
INSTALLED_APPS = [
    # Apps Django Core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Apps de Terceiros
    'django_prometheus',
    'import_export',
    'django_extensions',
    'widget_tweaks',
    'compressor',
    'django_seed',
    'fontawesomefree',
    'rest_framework',
    
    # Channels (para funcionalidades assíncronas)
    'channels',
    
    # Seus Apps
    'backend.accounts',
    'backend.control_panel',
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
    'backend.chat',
]

# ============ MIDDLEWARES ============
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

# ============ CONFIGURAÇÕES DE URL E TEMPLATES ============
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

# ============ CONFIGURAÇÕES SÍNCRONAS (WSGI) ============
WSGI_APPLICATION = 'backend.wsgi.application'

# ============ CONFIGURAÇÕES ASSÍNCRONAS (ASGI) ============
ASGI_APPLICATION = 'backend.asgi.application'

# Configuração do Channels para desenvolvimento
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

# ============ CONFIGURAÇÕES DE BANCO DE DADOS ============
# Configuração principal do PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='siscoe_db'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 60,
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}

# Suporte para DATABASE_URL (para serviços como Heroku)
if config('DATABASE_URL', default=None):
    import dj_database_url
    DATABASES['default'] = dj_database_url.config(
        default=config('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )

# ============ CONFIGURAÇÕES DE AUTENTICAÇÃO ============
AUTH_USER_MODEL = 'accounts.User'
LOGIN_REDIRECT_URL = 'core:index'
LOGIN_URL = 'accounts:login'
LOGOUT_REDIRECT_URL = 'accounts:login'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ============ CONFIGURAÇÕES DE EMAIL ============
# Configurações do Brevo (Sendinblue)
BREVO_API_KEY = config('BREVO_API_KEY', default='')
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp-relay.brevo.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='94c1c5001@smtp-brevo.com')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='siscoe@localhost.com')
DEFAULT_FROM_NAME = config('DEFAULT_FROM_NAME', default='SisCoE Sistema')
SERVER_EMAIL = config('SERVER_EMAIL', default=DEFAULT_FROM_EMAIL)

# Fallback para console em desenvolvimento se não houver credenciais
if DEBUG and not EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ============ CONFIGURAÇÕES DE INTERNACIONALIZAÇÃO ============
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR = True
DECIMAL_SEPARATOR = ','

# ============ CONFIGURAÇÕES DE ARQUIVOS ESTÁTICOS ============
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ============ CONFIGURAÇÕES DO COMPRESSOR ============
COMPRESS_ENABLED = not DEBUG
COMPRESS_ROOT = STATIC_ROOT

# ============ CONFIGURAÇÕES DO REST FRAMEWORK ============
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day'
    }
}

# ============ CONFIGURAÇÕES DE MENSAGENS ============
MESSAGE_TAGS = {
    constants.DEBUG: 'alert-primary',
    constants.ERROR: 'alert-danger',
    constants.SUCCESS: 'alert-success',
    constants.INFO: 'alert-info',
    constants.WARNING: 'alert-warning',
}

# ============ CONFIGURAÇÕES DE APIS EXTERNAS ============
GROQ_API_KEY = config('GROQ_API_KEY', default='')
WEATHER_API_KEY = config('WEATHER_API_KEY', default='')
TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN', default='')
TELEGRAM_CHAT_ID = config('TELEGRAM_CHAT_ID', default='')

# ============ CONFIGURAÇÕES DE SEGURANÇA ============
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Estas configurações serão sobrescritas em production.py
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False

# ============ CONFIGURAÇÕES DE CACHE ============
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-siscoe',
    }
}

# ============ CONFIGURAÇÕES DE LOGGING ============
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'django.server': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '[{server_time}] {message}',
            'style': '{',
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'debug.log',
            'maxBytes': 5 * 1024 * 1024,  # 5MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'django.server': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'django.server',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['django.server'],
            'level': 'INFO',
            'propagate': False,
        },
        'channels': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'backend': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'backend.chat': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'backend.tickets': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

# ============ CONFIGURAÇÕES ADICIONAIS ============
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configurações específicas do chat
CHAT_SETTINGS = {
    'MESSAGE_BATCH_SIZE': 50,
    'WEBSOCKET_HEARTBEAT': 30,
    'MAX_CONVERSATION_PARTICIPANTS': 100,
    'ENABLE_MESSAGE_COMPRESSION': True,
}

# Configurações de criptografia
CHAT_ENCRYPTION_KEY = config('CHAT_ENCRYPTION_KEY', default='')

# Configurações de upload
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024  # 2MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Configurações de sessão
SESSION_COOKIE_AGE = 1209600  # 2 semanas em segundos
SESSION_SAVE_EVERY_REQUEST = True

# Configurações de timezone para Brasil
USE_L10N = True