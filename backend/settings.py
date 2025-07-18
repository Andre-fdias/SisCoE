import os
from pathlib import Path
from django.contrib.messages import constants
from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)


ALLOWED_HOSTS = config('ALLOWED_HOSTS', default=[], cast=Csv())


os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# Application definition

INSTALLED_APPS = [
    'backend.accounts',  # <<<
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # apps de terceiros
    'import_export',
    'django_extensions',
    'widget_tweaks',
    'compressor',
    'django_seed',
    'fontawesomefree',

     
    # minhas apps
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
    'backend.core.middleware.JSONMessagesMiddleware',  # Adicione isto
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

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20,  # Aumenta o timeout para 20 segundos
        }
    }
}

# settings.py


# Email config
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True  # Use TLS para segurança
EMAIL_HOST_USER = config('EMAIL_HOST_USER', '')  # Seu endereço de e-mail do Gmail
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', '') # A Senha de App gerada
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER) # Use o mesmo e-mail como remetente padrão
SERVER_EMAIL = EMAIL_HOST_USER # Para e-mails de erro do Django


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_TZ = True

USE_THOUSAND_SEPARATOR = True

DECIMAL_SEPARATOR = ','


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR.joinpath('staticfiles')


# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
RUN_SERVER_PORT = 8090  # Escolha uma porta diferente (por exemplo, 8081, 8090)


LOGIN_REDIRECT_URL = 'core:index'

MESSAGE_TAGS = {
 constants.DEBUG: 'alert-primary',
 constants.ERROR: 'alert-danger',
 constants.SUCCESS: 'alert-success',
 constants.INFO: 'alert-info',
 constants.WARNING: 'alert-warning',
}

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

GROQ_API_KEY = config('GROQ_API_KEY')



# OpenWeatherMap
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')



AUTH_USER_MODEL = 'accounts.User'

ADMIN_DEFAULT_PERMISSIONS = [
    'add', 'change', 'delete', 'view'
]


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
            'formatter': 'verbose'
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
     'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO', # Mude para 'DEBUG' para logs mais detalhados
            'propagate': False,
        },
        'backend.accounts.views': { # Nome do seu módulo de views
            'handlers': ['console', 'file'],
            'level': 'DEBUG', # Configure este para 'DEBUG' para ver os logs detalhados da sua view
            'propagate': False,
        },
    }
}

# Configurações para AJAX
CSRF_COOKIE_HTTPONLY = False  # Permite que JavaScript leia o CSRF token
CSRF_COOKIE_SECURE = False    # Em desenvolvimento pode ser False
CSRF_COOKIE_SAMESITE = 'Lax'  # Ou 'None' se estiver usando CORS


