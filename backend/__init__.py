# backend/__init__.py (CORRETO)
from .celery_app import app as celery_app

__all__ = ('celery_app',)