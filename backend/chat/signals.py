from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Presence

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_presence(sender, instance, created, **kwargs):
    """
    Cria um registro de presença quando um novo usuário é criado.
    """
    if created:
        Presence.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_presence(sender, instance, **kwargs):
    """
    Garante que o usuário tenha um registro de presença.
    """
    Presence.objects.get_or_create(user=instance)
