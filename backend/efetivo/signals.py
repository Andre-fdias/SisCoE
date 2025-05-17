from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=CatEfetivo)
def criar_historico_apos_save(sender, instance, created, **kwargs):
    if not created:  # Só cria histórico para atualizações, não para criações
        instance.criar_registro_historico()


from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import CatEfetivo
from datetime import date

@receiver(pre_save, sender=CatEfetivo)
def verificar_data_termino(sender, instance, **kwargs):
    if instance.data_termino and instance.data_termino < date.today():
        # Se a data de término já passou, muda para ATIVO
        instance.tipo = 'ATIVO'
        instance.data_termino = None
        
        # Cria histórico (opcional, se quiser registrar esta mudança automática)
        HistoricoCatEfetivo.objects.create(
            cat_efetivo=instance,
            tipo=instance.tipo,
            data_inicio=instance.data_inicio,
            data_termino=instance.data_termino,
            observacao="Alteração automática para ATIVO - Data de término expirada",
            usuario_alteracao=None
        )
