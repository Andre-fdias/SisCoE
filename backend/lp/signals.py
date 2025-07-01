# backend/lp/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import LP, LP_fruicao

@receiver(post_save, sender=LP)
def criar_fruicao_ao_concluir_lp(sender, instance, created, **kwargs):
    """
    Signal para criar automaticamente um registro de fruição quando uma LP é marcada como concluída
    com 90 dias de afastamento padrão.
    """
    # Verificar se o status foi alterado para CONCLUIDO
    if instance.status_lp == LP.StatusLP.CONCLUIDO:
        # Verificar se já existe uma fruição para esta LP (evitar duplicatas)
        if not hasattr(instance, 'previsao_associada'):
            # Criar a fruição com os dados da LP
            LP_fruicao.objects.create(
                cadastro=instance.cadastro,
                lp_concluida=instance,
                numero_lp=instance.numero_lp,
                data_concessao_lp=instance.data_concessao_lp,
                bol_g_pm_lp=instance.bol_g_pm_lp,
                data_publicacao_lp=instance.data_publicacao_lp,
                tipo_periodo_afastamento=90,  # 90 dias padrão
                user_created=instance.usuario_conclusao,
            )