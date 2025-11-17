from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.apps import apps
from .metrics import (
    efetivo_militares_por_categoria,
    efetivo_situacao_funcional_updates_total,
)

# ==============================================================================
# SIGNAL HANDLERS PARA ATUALIZAR MÉTRICAS DO PROMETHEUS
# ==============================================================================


@receiver(post_save, sender="efetivo.DetalhesSituacao")
@receiver(post_delete, sender="efetivo.DetalhesSituacao")
def metric_update_detalhes_situacao(sender, instance, **kwargs):
    """
    Incrementa o contador de atualizações da situação funcional sempre que um
    registro de DetalhesSituacao é salvo (criado ou atualizado).
    """
    efetivo_situacao_funcional_updates_total.inc()


@receiver(post_save, sender="efetivo.CatEfetivo")
@receiver(post_delete, sender="efetivo.CatEfetivo")
def metric_update_militares_por_categoria(sender, instance, **kwargs):
    """
    Atualiza o Gauge de militares por categoria.
    Esta função é chamada sempre que um registro de CatEfetivo é salvo ou deletado.

    Ela recalcula o total de militares para cada categoria e atualiza o Gauge.
    Esta abordagem é mais resiliente do que incrementar/decrementar, pois evita
    discrepâncias em caso de falhas.
    """
    CatEfetivo = apps.get_model("efetivo", "CatEfetivo")

    # Obtém todas as categorias possíveis a partir dos choices do modelo
    categorias = [choice[0] for choice in CatEfetivo.TIPO_CHOICES if choice[0]]

    # Itera sobre cada categoria para obter a contagem e atualizar a métrica
    for categoria in categorias:
        # Filtra apenas os registros ativos para a categoria específica
        count = CatEfetivo.objects.filter(tipo=categoria, ativo=True).count()

        # Atualiza o Gauge para a categoria correspondente
        efetivo_militares_por_categoria.labels(categoria=categoria).set(count)
