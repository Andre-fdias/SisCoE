from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils import timezone
from .models import Cadastro_adicional, LP, HistoricoCadastro, HistoricoLP
from datetime import timedelta

# Signal para Cadastro_adicional
@receiver(post_save, sender=Cadastro_adicional)
def calcular_proximo_periodo_adicional(sender, instance, created, **kwargs):
    if hasattr(instance, '_calculando_proximo_periodo'):
        return

    instance._calculando_proximo_periodo = True

    # Cálculo apenas para Adicional
    if instance.data_ultimo_adicional:
        instance.proximo_adicional = instance.data_ultimo_adicional + timedelta(days=1825 - (instance.dias_desconto_adicional or 0))
        instance.mes_proximo_adicional = instance.proximo_adicional.month
        instance.ano_proximo_adicional = instance.proximo_adicional.year
        instance.numero_prox_adicional = instance.numero_adicional + 1

    if not created and not instance._state.adding:
        instance.save(update_fields=[
            'proximo_adicional', 'mes_proximo_adicional', 
            'ano_proximo_adicional', 'numero_prox_adicional'
        ])

    del instance._calculando_proximo_periodo

# Signal para LP
@receiver(post_save, sender=LP)
def calcular_proximo_periodo_lp(sender, instance, created, **kwargs):
    if hasattr(instance, '_calculando_proximo_periodo'):
        return

    instance._calculando_proximo_periodo = True

    # Cálculo apenas para LP
    if instance.data_ultimo_lp:
        instance.proximo_lp = instance.data_ultimo_lp + timedelta(days=1825 - (instance.dias_desconto_lp or 0))
        instance.mes_proximo_lp = instance.proximo_lp.month
        instance.ano_proximo_lp = instance.proximo_lp.year
        instance.numero_prox_lp = instance.numero_lp + 1

    if not created and not instance._state.adding:
        instance.save(update_fields=[
            'proximo_lp', 'mes_proximo_lp', 
            'ano_proximo_lp', 'numero_prox_lp'
        ])

    del instance._calculando_proximo_periodo

@receiver(post_save, sender=Cadastro_adicional)
def registrar_historico_adicional(sender, instance, created, **kwargs):
    """
    Registra um histórico completo do Cadastro_adicional sempre que ele for salvo.
    """
    HistoricoCadastro.objects.create(
        cadastro_adicional=instance,
        data_alteracao=timezone.now(),
        usuario_alteracao=instance.user_updated if not created else instance.user_created,
        cadastro=instance.cadastro,
        numero_adicional=instance.numero_adicional,
        data_ultimo_adicional=instance.data_ultimo_adicional,
        numero_prox_adicional=instance.numero_prox_adicional,
        proximo_adicional=instance.proximo_adicional,
        mes_proximo_adicional=instance.mes_proximo_adicional,
        ano_proximo_adicional=instance.ano_proximo_adicional,
        dias_desconto_adicional=instance.dias_desconto_adicional,
        situacao_adicional=instance.situacao_adicional,
        sexta_parte=instance.sexta_parte,
        confirmacao_6parte=instance.confirmacao_6parte,
        data_concessao_adicional=instance.data_concessao_adicional,
        bol_g_pm_adicional=instance.bol_g_pm_adicional,
        data_publicacao_adicional=instance.data_publicacao_adicional,
        status_adicional=instance.status_adicional,
        user_created=instance.user_created,
        user_updated=instance.user_updated,
        usuario_conclusao=instance.usuario_conclusao,
        created_at=instance.created_at,
        updated_at=instance.updated_at,
        data_conclusao=instance.data_conclusao,
    )

@receiver(post_save, sender=Cadastro_adicional)
def verificar_status_adicional(sender, instance, created, **kwargs):
    """
    Signal para verificar e atualizar o status do adicional quando necessário
    """
    hoje = timezone.now().date()
    
    # Verifica se a data do próximo adicional foi atingida
    if (instance.proximo_adicional and 
        hoje >= instance.proximo_adicional and 
        instance.status_adicional == Cadastro_adicional.StatusAdicional.AGUARDANDO_REQUISITOS):
        instance.status_adicional = Cadastro_adicional.StatusAdicional.FAZ_JUS
        instance.save()