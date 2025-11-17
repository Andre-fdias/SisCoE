from .base import *
from decouple import config, Csv
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# ============ CONFIGURAÇÕES DE PRODUÇÃO ============
DEBUG = False
ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())

# ============ BANCO DE DADOS PRODUÇÃO ============
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
        "CONN_MAX_AGE": 600,
        "OPTIONS": {
            "connect_timeout": 30,
            "sslmode": (
                "require" if config("DB_SSL", default=True, cast=bool) else "disable"
            ),
        },
    }
}

# ============ CHANNEL LAYERS PRODUÇÃO ============
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [config("REDIS_URL", default="redis://127.0.0.1:6379/0")],
            "capacity": 5000,  # Maior capacidade para produção
            "expiry": 60,  # Expira mensagens após 60 segundos
            "prefix": "siscoe_chat",  # Prefixo para keys Redis
        },
    },
}

# ============ CACHE PRODUÇÃO ============
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config("REDIS_URL", default="redis://127.0.0.1:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
            "IGNORE_EXCEPTIONS": True,  # Redis falha silenciosamente
        },
        "KEY_PREFIX": "siscoe_cache",
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# ============ CONFIGURAÇÕES DE EMAIL PRODUÇÃO ============
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="smtp-relay.brevo.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL")
SERVER_EMAIL = config("SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)

# ============ CONFIGURAÇÕES DE SEGURANÇA PRODUÇÃO ============
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ============ CONFIGURAÇÕES DE ARQUIVOS ESTÁTICOS PRODUÇÃO ============
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ============ SENTRY PARA MONITORAMENTO ============
if config("SENTRY_DSN", default=None):
    sentry_sdk.init(
        dsn=config("SENTRY_DSN"),
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=True,
        environment=config("SENTRY_ENVIRONMENT", default="production"),
    )

# ============ CONFIGURAÇÕES DE LOGGING PRODUÇÃO ============
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "production.log",
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 10,
            "formatter": "verbose",
        },
        "error_file": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "error.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 10,
            "formatter": "verbose",
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file", "console"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.server": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": False,
        },
        "channels": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": False,
        },
        "backend.chat": {
            "handlers": ["file", "console", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "WARNING",
    },
}

# ============ CONFIGURAÇÕES ADICIONAIS DE PERFORMANCE ============
# Otimizações para produção
CHAT_PROD_SETTINGS = {
    "MESSAGE_BATCH_SIZE": 50,
    "WEBSOCKET_HEARTBEAT": 30,
    "MAX_CONVERSATION_PARTICIPANTS": 100,
    "ENABLE_MESSAGE_COMPRESSION": True,
}

# Configurações específicas para o servidor ASGI
ASGI_THREADS = config("ASGI_THREADS", default=100, cast=int)
