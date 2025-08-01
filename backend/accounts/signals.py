from django.dispatch import Signal

user_login_password_failed = Signal()



# accounts/signals.py
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

@receiver(pre_save, sender=User)
def update_online_status(sender, instance, **kwargs):
    """Atualiza o status online baseado no último login"""
    if instance.last_login:
        # Considera offline se não houve atividade nos últimos 15 minutos
        threshold = timezone.now() - timezone.timedelta(minutes=15)
        instance.is_online = instance.last_login > threshold