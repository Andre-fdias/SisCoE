from django.contrib.auth.signals import user_login_failed
from django.dispatch import receiver
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
