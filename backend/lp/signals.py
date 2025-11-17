# backend/lp/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import LP, LP_fruicao


@receiver(post_save, sender=LP)
def criar_fruicao_ao_concluir_lp(sender, instance, created, **kwargs):
    """
    Signal para criar automaticamente um registro de fruição (saldo inicial)
    quando uma LP é marcada como concluída.
    """
    if instance.status_lp == LP.StatusLP.CONCLUIDO:
        # Usar get_or_create para garantir que só haja uma LP_fruicao por LP_concluida
        lp_fruicao_instance, fruicao_created = LP_fruicao.objects.get_or_create(
            lp_concluida=instance,
            defaults={
                "cadastro": instance.cadastro,
                "numero_lp": instance.numero_lp,
                "data_concessao_lp": instance.data_concessao_lp,
                "bol_g_pm_lp": instance.bol_g_pm_lp,
                "data_publicacao_lp": instance.data_publicacao_lp,
                "tipo_periodo_afastamento": None,  # Não defina aqui; este campo é para o período atualmente utilizado
                "dias_disponiveis": 90,  # Saldo inicial total de 90 dias
                "dias_utilizados": 0,  # Inicia com 0 dias utilizados
                "user_created": instance.usuario_conclusao,
            },
        )
        # Se a fruição foi criada agora, o método save() dela já foi chamado
        # e o histórico inicial (90 dias disponíveis) já será registrado lá.
        # Não é necessário chamar save() novamente aqui.
