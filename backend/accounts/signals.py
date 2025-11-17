from django.conf import settings
from django.db.models.signals import post_save
from django.contrib.auth.signals import user_login_failed
from django.dispatch import receiver
from .models import Profile
from .metrics import accounts_login_failures_total

# ==============================================================================
# SIGNAL HANDLERS PARA MÉTRICAS DE SEGURANÇA
# ==============================================================================


@receiver(user_login_failed)
def metric_user_login_failed(sender, credentials, request, **kwargs):
    """
    Incrementa o contador de falhas de login sempre que o sinal
    `user_login_failed` é disparado pelo Django.
    """
    accounts_login_failures_total.inc()


# ==============================================================================
# SIGNAL HANDLERS PARA CRIAÇÃO DE PERFIL
# ==============================================================================


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_superuser_profile(sender, instance, created, **kwargs):
    """
    Cria um Profile padrão quando um novo superusuário é criado.
    """
    if created and instance.is_superuser:
        Profile.objects.create(user=instance)
