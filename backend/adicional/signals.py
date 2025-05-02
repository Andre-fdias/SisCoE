# signals.py
@receiver(post_save, sender=Cadastro_adicional)
def calcular_proximo_periodo(sender, instance, created, **kwargs):
    if hasattr(instance, '_calculando_proximo_periodo'):
        return

    instance._calculando_proximo_periodo = True

    # Cálculo para Adicional
    if instance.data_ultimo_adicional:
        instance.proximo_adicional = instance.data_ultimo_adicional + timedelta(days=1825 - (instance.dias_desconto_adicional or 0))
        instance.mes_proximo_adicional = instance.proximo_adicional.month
        instance.ano_proximo_adicional = instance.proximo_adicional.year
        instance.numero_prox_adicional = instance.numero_adicional + 1

    # Cálculo para LP
    if instance.data_ultimo_lp:
        instance.proximo_lp = instance.data_ultimo_lp + timedelta(days=1825 - (instance.dias_desconto_lp or 0))
        instance.mes_proximo_lp = instance.proximo_lp.month
        instance.ano_proximo_lp = instance.proximo_lp.year
        instance.numero_prox_lp = instance.numero_lp + 1

    if not created and not instance._state.adding:
        instance.save(update_fields=[
            'proximo_adicional', 'mes_proximo_adicional', 'ano_proximo_adicional', 'numero_prox_adicional',
            'proximo_lp', 'mes_proximo_lp', 'ano_proximo_lp', 'numero_prox_lp'
        ])

    del instance._calculando_proximo_periodo


@receiver(post_save, sender=Cadastro_adicional)
def registrar_historico(sender, instance, created, **kwargs):
    if not created:  # Só registra histórico para atualizações
        HistoricoCadastro.objects.create(
            cadastro_adicional=instance,
            situacao_adicional=instance.situacao_adicional,
            situacao_lp=instance.situacao_lp,
            usuario_alteracao=instance.user,
            numero_prox_adicional=instance.numero_prox_adicional,
            proximo_adicional=instance.proximo_adicional,
            mes_proximo_adicional=instance.mes_proximo_adicional,
            ano_proximo_adicional=instance.ano_proximo_adicional,
            dias_desconto_adicional=instance.dias_desconto_adicional,
            numero_prox_lp=instance.numero_prox_lp,
            proximo_lp=instance.proximo_lp,
            mes_proximo_lp=instance.mes_proximo_lp,
            ano_proximo_lp=instance.ano_proximo_lp,
            dias_desconto_lp=instance.dias_desconto_lp
        )