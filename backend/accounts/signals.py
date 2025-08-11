# accounts/signals.py
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

@receiver(pre_save, sender=User)
def update_online_status(sender, instance, **kwargs):
    """Atualiza o status online baseado no último login"""
    # Se o usuário está sendo marcado como online explicitamente, não faça nada
    if hasattr(instance, '_force_online'):
        return
        
    # Apenas atualiza se o usuário já tem um last_login registrado
    if instance.last_login:
        # Considera offline se não houve atividade nos últimos 15 minutos
        threshold = timezone.now() - timedelta(minutes=15)
        instance.is_online = instance.last_login > threshold
    else:
        # Se nunca logou, ou se last_login é None, ele não está online
        instance.is_online = False