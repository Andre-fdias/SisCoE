from django.conf import settings
from django.db import models
from django.utils.safestring import mark_safe
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.db import transaction
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils import timezone

# Definições de escolhas compartilhadas
n_choices = [(i, f'{i:02d}') for i in range(1, 9)]
situacao_choices = (
    ("Aguardando", "Aguardando"),
    ("Concedido", "Concedido"),
    ("Concluído", "Concluído"),
)

class Cadastro_adicional(models.Model):
    """
    Modelo para representar os Adicionais de um servidor.
    """
    # Campos comuns
    cadastro = models.ForeignKey('efetivo.Cadastro', on_delete=models.CASCADE, verbose_name="Cadastro")
    
    # Controle de usuário e datas
    user_created = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='adicionais_criados',
        verbose_name="Criado por"
    )
    user_updated = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='adicionais_modificados',
        verbose_name="Modificado por"
    )
    usuario_conclusao = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='adicionais_concluidos',
        verbose_name="Concluído por"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    data_conclusao = models.DateTimeField(null=True, blank=True, verbose_name="Data de Conclusão")

    # Campos do adicional
    numero_adicional = models.PositiveSmallIntegerField(choices=n_choices, verbose_name="Número do Adicional")
    data_ultimo_adicional = models.DateField(verbose_name="Data do Último Adicional")
    numero_prox_adicional = models.PositiveSmallIntegerField(choices=n_choices, default=1, verbose_name="Próximo Número do Adicional")
    proximo_adicional = models.DateField(null=True, blank=True, verbose_name="Próximo Adicional")
    mes_proximo_adicional = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Mês do Próximo Adicional")
    ano_proximo_adicional = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Ano do Próximo Adicional")
    dias_desconto_adicional = models.PositiveSmallIntegerField(default=0, verbose_name="Dias de Desconto Adicional")
    situacao_adicional = models.CharField(max_length=30, choices=situacao_choices, default="Aguardando", verbose_name="Situação do Adicional")
    
    # Campos específicos da 6ª parte
    sexta_parte = models.BooleanField(default=False, verbose_name="6ª Parte Concluída")
    confirmacao_6parte = models.BooleanField(default=False, verbose_name="6ª Parte Confirmada")
    
    # Campos de publicação
    data_concessao_adicional = models.DateField(null=True, blank=True, verbose_name="Data de Concessão do Adicional")
    bol_g_pm_adicional = models.CharField(max_length=50, null=True, blank=True, verbose_name="BOL GPm Adicional")
    data_publicacao_adicional = models.DateField(null=True, blank=True, verbose_name="Data Publicação Adicional")

    # Status workflow
    class StatusAdicional(models.TextChoices):
        AGUARDANDO_REQUISITOS = 'aguardando_requisitos', 'Aguardando Requisitos'
        FAZ_JUS = 'faz_jus', 'Faz Jus'
        LANCADO_SIPA = 'lancado_sipa', 'Lançado em SIPA'
        AGUARDANDO_PUBLICACAO = 'aguardando_publicacao', 'Aguardando Publicação'
        PUBLICADO = 'publicado', 'Publicado'
        ENCERRADO = 'encerrado', 'Encerrado'

    status_adicional = models.CharField(
        max_length=30,
        choices=StatusAdicional.choices,
        default=StatusAdicional.AGUARDANDO_REQUISITOS,
        verbose_name="Status do Adicional"
    )

    class Meta:
        verbose_name = "Cadastro de Adicional"
        verbose_name_plural = "Cadastros de Adicionais"
        db_table = "adicional_cadastro_adicional"
        ordering = ['-created_at']
        permissions = [
            ("can_concluir_adicional", "Pode concluir adicional"),
        ]

    def __str__(self):
        return f'Adicional {self.numero_adicional} - {self.cadastro.nome}'

    def clean(self):
        """Validação personalizada para o modelo"""
        if self.situacao_adicional == "Concluído":
            if not self.data_concessao_adicional:
                raise ValidationError({
                    'data_concessao_adicional': "Data de concessão é obrigatória quando o status é Concluído"
                })
            if not self.usuario_conclusao:
                raise ValidationError({
                    'usuario_conclusao': "Usuário que concluiu é obrigatório"
                })
            if not self.data_conclusao:
                raise ValidationError({
                    'data_conclusao': "Data de conclusão é obrigatória"
                })

        if self.numero_prox_adicional == 4 and not self.sexta_parte:
            self.sexta_parte = True

    def save(self, *args, **kwargs):
    # Atualiza status automaticamente antes de salvar
        hoje = timezone.now().date()
        
        if self.proximo_adicional and self.proximo_adicional <= hoje and self.status_adicional == self.StatusAdicional.AGUARDANDO_REQUISITOS:
            self.status_adicional = self.StatusAdicional.FAZ_JUS
            
        if self.status_adicional == self.StatusAdicional.LANCADO_SIPA:
            if self.updated_at and (hoje - self.updated_at.date()).days >= 1:
                self.status_adicional = self.StatusAdicional.AGUARDANDO_PUBLICACAO
        
        super().save(*args, **kwargs)


    # Métodos de exibição de usuário
    def user_created_display(self):
        if self.user_created and hasattr(self.user_created, 'profile'):
            return f"{self.user_created.profile.posto_grad} {self.user_created.profile.re}-{self.user_created.profile.dig} {self.user_created.last_name}"
        elif self.user_created:
            return self.user_created.get_full_name() or self.user_created.username
        return "-"

    def user_updated_display(self):
        if self.user_updated and hasattr(self.user_updated, 'profile'):
            return f"{self.user_updated.profile.posto_grad} {self.user_updated.profile.re}-{self.user_updated.profile.dig} {self.user_updated.last_name}"
        elif self.user_updated:
            return self.user_updated.get_full_name() or self.user_updated.username
        return "-"

    def usuario_conclusao_display(self):
        if self.usuario_conclusao and hasattr(self.usuario_conclusao, 'profile'):
            return f"{self.usuario_conclusao.profile.posto_grad} {self.usuario_conclusao.profile.re}-{self.usuario_conclusao.profile.dig} {self.usuario_conclusao.last_name}"
        elif self.usuario_conclusao:
            return self.usuario_conclusao.get_full_name() or self.usuario_conclusao.username
        return "-"

    # Propriedades calculadas
    @property
    def status_adicional_display(self):
        hoje = timezone.now().date()
        if self.situacao_adicional == "Concluído":
            if self.data_concessao_adicional:
                return mark_safe(f'<span class="bg-purple-500 text-white px-2 py-1 rounded">Concluído em {self.data_concessao_adicional.strftime("%d/%m/%Y")}</span>')
            return mark_safe('<span class="bg-purple-500 text-white px-2 py-1 rounded">Concluído</span>')

        if self.proximo_adicional:
            diferenca = (self.proximo_adicional - hoje).days
            if diferenca > 30:
                return mark_safe('<span class="bg-green-500 text-white px-2 py-1 rounded">Aguardar</span>')
            elif 0 <= diferenca <= 30:
                return mark_safe('<span class="bg-yellow-500 text-white px-2 py-1 rounded">Lançar</span>')
            else:
                return mark_safe('<span class="bg-red-500 text-white px-2 py-1 rounded">Vencido</span>')
        return "Data não definida"

    @property
    def tempo_ats_detalhada(self):
        hoje = timezone.now().date()
        delta = relativedelta(hoje, self.data_ultimo_adicional)
        return f"{delta.years} anos, {delta.months} meses e {delta.days} dias"

    @property
    def mes_abreviado_proximo_adicional(self):
        meses = {
            1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr',
            5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago',
            9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
        }
        return meses.get(self.mes_proximo_adicional, '-')

    @property
    def is_concluido(self):
        return self.situacao_adicional == "Concluído"

    # Workflow methods
    def pode_concluir(self, user):
        """Verifica se o usuário pode concluir este adicional"""
        return (user.has_perm('adicional.can_concluir_adicional') and 
               not self.is_concluido and
               self.status_adicional in ['faz_jus', 'lancado_sipa', 'aguardando_publicacao', 'publicado'])

    @classmethod
    def get_n_choices(cls):
        return cls.n_choices


    @property
    def status_adicional_ordenacao(self):
        ordem = {
            'aguardando_requisitos': 1,
            'faz_jus': 2,
            'lancado_sipa': 3,
            'aguardando_publicacao': 4,
            'publicado': 5,
            'encerrado': 6  # Ordem máxima
        }
        return ordem.get(self.status_adicional, 0)

    @property
    def total_etapas(self):
        return len(self.StatusAdicional.choices)



    def atualizar_status_automatico(self):
        """Atualiza o status automaticamente baseado em condições"""
        hoje = timezone.now().date()
        
        # Se ainda não foi lançado no SIPA
        if self.status_adicional == self.StatusAdicional.AGUARDANDO_REQUISITOS:
            if self.proximo_adicional and self.proximo_adicional <= hoje:
                self.status_adicional = self.StatusAdicional.FAZ_JUS
                
        # Se foi lançado no SIPA, aguardar 1 dia para mudar para aguardando publicação
        elif self.status_adicional == self.StatusAdicional.LANCADO_SIPA:
            if self.updated_at and (hoje - self.updated_at.date()) >= timedelta(days=1):
                self.status_adicional = self.StatusAdicional.AGUARDANDO_PUBLICACAO
                
        # Salva apenas se houve mudança
        if self.has_changed('status_adicional'):
            self.save()

    def has_changed(self, field):
        """Verifica se um campo foi alterado"""
        if not self.pk:
            return False
        old_value = self.__class__._default_manager.filter(pk=self.pk).values(field).get()[field]
        return getattr(self, field) != old_value


    def ultima_imagem(self):
        return self.imagens.order_by('-id').first()

class LP(models.Model):
    """
    Modelo para representar a Licença Prêmio (LP) de um servidor.
    """
    # Campos comuns
    cadastro = models.ForeignKey('efetivo.Cadastro', on_delete=models.CASCADE, verbose_name="Cadastro")
    user_created = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Use settings.AUTH_USER_MODEL em vez de User diretamente
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lps_criadas',  # Alterado related_name
        verbose_name="Criado por"
    )
    user_updated = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Use settings.AUTH_USER_MODEL aqui também
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lps_modificadas',  # Alterado related_name
        verbose_name="Modificado por"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    # Campos específicos da LP
    numero_lp = models.PositiveSmallIntegerField(choices=n_choices, verbose_name="Número da LP")
    data_ultimo_lp = models.DateField(verbose_name="Data do Último LP")
    numero_prox_lp = models.PositiveSmallIntegerField(choices=n_choices, default=1, verbose_name="Próximo Número da LP")
    proximo_lp = models.DateField(null=True, blank=True, verbose_name="Próximo LP")
    mes_proximo_lp = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Mês do Próximo LP")
    ano_proximo_lp = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Ano do Próximo LP")
    dias_desconto_lp = models.PositiveSmallIntegerField(default=0, verbose_name="Dias de Desconto LP")
    situacao_lp = models.CharField(max_length=30, choices=situacao_choices, default="Aguardando", verbose_name="Situação da LP")
    bol_g_pm_lp = models.CharField(max_length=50, null=True, blank=True, verbose_name="BOL GPm LP")
    data_publicacao_lp = models.DateField(null=True, blank=True, verbose_name="Data Publicação LP")
    data_concessao_lp = models.DateField(null=True, blank=True, verbose_name="Data de Concessão da LP")

    # Status para LP
    class StatusLP(models.TextChoices):
        AGUARDANDO_REQUISITOS = 'aguardando_requisitos', 'Aguardando Requisitos'
        FAZ_JUS = 'faz_jus', 'Faz Jus'
        LANCADO_SIPA = 'lancado_sipa', 'Lançado em SIPA'
        AGUARDANDO_PUBLICACAO = 'aguardando_publicacao', 'Aguardando Publicação'
        PUBLICADO = 'publicado', 'Publicado'
        ENCERRADO = 'encerrado', 'Encerrado'

    status_lp = models.CharField(
        max_length=30,
        choices=StatusLP.choices,
        default=StatusLP.AGUARDANDO_REQUISITOS,
        verbose_name="Status da LP"
    )
    
    class Meta:
        verbose_name = "Licença Prêmio"
        verbose_name_plural = "Licenças Prêmio"
        db_table = "adicional_lp"  # Nome explícito da tabela
        ordering = ['-created_at']

    def __str__(self):
        return f'LP {self.numero_lp} - {self.cadastro.nome}'

    def clean(self):
        """Validação personalizada para o modelo"""
        if self.situacao_lp == "Concluído" and not self.data_concessao_lp:
            raise ValidationError({
                'data_concessao_lp': "Data de concessão é obrigatória quando o status é Concluído"
            })

    def save(self, *args, **kwargs):
        """Lógica personalizada ao salvar"""
        self.full_clean()  # Executa as validações
        super().save(*args, **kwargs)

    def user_created_display(self):
        if self.user_created and hasattr(self.user_created, 'profile'):
            return f"{self.user_created.profile.posto_grad} {self.user_created.profile.re}-{self.user_created.profile.dig} {self.user_created.last_name}"
        elif self.user_created:
            return self.user_created.get_full_name() or self.user_created.username
        return "-"

    def user_updated_display(self):
        if self.user_updated and hasattr(self.user_updated, 'profile'):
            return f"{self.user_updated.profile.posto_grad} {self.user_updated.profile.re}-{self.user_updated.profile.dig} {self.user_updated.last_name}"
        elif self.user_updated:
            return self.user_updated.get_full_name() or self.user_updated.username
        return "-"


    @property
    def status_lp_display(self):
        """Retorna o status formatado com cores"""
        hoje = timezone.now().date()
        
        if self.situacao_lp == "Concluído":
            if self.data_concessao_lp:
                return mark_safe(f'<span class="bg-purple-500 text-white px-2 py-1 rounded">Concluído em {self.data_concessao_lp.strftime("%d/%m/%Y")}</span>')
            return mark_safe('<span class="bg-purple-500 text-white px-2 py-1 rounded">Concluído</span>')

        if self.proximo_lp:
            diferenca = (self.proximo_lp - hoje).days
            if diferenca > 30:
                return mark_safe('<span class="bg-green-500 text-white px-2 py-1 rounded">Aguardar</span>')
            elif 0 <= diferenca <= 30:
                return mark_safe('<span class="bg-yellow-500 text-white px-2 py-1 rounded">Lançar</span>')
            else:
                return mark_safe('<span class="bg-red-500 text-white px-2 py-1 rounded">Vencido</span>')
        return "Data não definida"

    @property
    def tempo_lp_detalhada(self):
        """Calcula o tempo desde a última LP"""
        hoje = timezone.now().date()
        delta = relativedelta(hoje, self.data_ultimo_lp)
        return f"{delta.years} anos, {delta.months} meses e {delta.days} dias"

    @property
    def mes_abreviado_proximo_lp(self):
        meses = {
            1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 
            5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago',
            9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
        }
        return meses.get(self.mes_proximo_lp, '-')

    def ultima_imagem(self):
        return self.imagens.order_by('-id').first()

class HistoricoCadastro(models.Model):
    """
    Modelo para armazenar o histórico completo de alterações do Cadastro_adicional
    """
    cadastro_adicional = models.ForeignKey(
        Cadastro_adicional,
        on_delete=models.CASCADE,
        related_name='historicos',
        verbose_name="Adicional Relacionado"
    )
    
    # Controle de alterações
    data_alteracao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data da Alteração"
    )
    usuario_alteracao = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Responsável pela Alteração"
    )

    # Réplica exata dos campos do Cadastro_adicional
    cadastro = models.ForeignKey(
        'efetivo.Cadastro',
        on_delete=models.CASCADE,
        verbose_name="Cadastro"
    )
    user_created = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historicos_criados',
        verbose_name="Criado por"
    )
    user_updated = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historicos_modificados',
        verbose_name="Modificado por"
    )
    usuario_conclusao = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historicos_concluidos',
        verbose_name="Concluído por"
    )
    created_at = models.DateTimeField(verbose_name="Criado em")
    updated_at = models.DateTimeField(verbose_name="Atualizado em")
    data_conclusao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de Conclusão"
    )
    numero_adicional = models.PositiveSmallIntegerField(
        choices=n_choices,
        verbose_name="Número do Adicional"
    )
    data_ultimo_adicional = models.DateField(
        verbose_name="Data do Último Adicional"
    )
    numero_prox_adicional = models.PositiveSmallIntegerField(
        choices=n_choices,
        verbose_name="Próximo Número do Adicional"
    )
    proximo_adicional = models.DateField(
        null=True,
        blank=True,
        verbose_name="Próximo Adicional"
    )
    mes_proximo_adicional = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Mês do Próximo Adicional"
    )
    ano_proximo_adicional = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Ano do Próximo Adicional"
    )
    dias_desconto_adicional = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Dias de Desconto Adicional"
    )
    situacao_adicional = models.CharField(
        max_length=30,
        choices=situacao_choices,
        default="Aguardando",
        verbose_name="Situação do Adicional"
    )
    sexta_parte = models.BooleanField(
        default=False,
        verbose_name="6ª Parte Concluída"
    )
    confirmacao_6parte = models.BooleanField(
        default=False,
        verbose_name="6ª Parte Confirmada"
    )
    data_concessao_adicional = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de Concessão do Adicional"
    )
    bol_g_pm_adicional = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="BOL GPm Adicional"
    )
    data_publicacao_adicional = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data Publicação Adicional"
    )
    status_adicional = models.CharField(
        max_length=30,
        choices=Cadastro_adicional.StatusAdicional.choices,
        default=Cadastro_adicional.StatusAdicional.AGUARDANDO_REQUISITOS,
        verbose_name="Status do Adicional"
    )

    class Meta:
        verbose_name = "Histórico de Adicional"
        verbose_name_plural = "Históricos de Adicionais"
        ordering = ['-data_alteracao']

    def __str__(self):
        return (f"Histórico #{self.id} - "
                f"Adicional {self.numero_adicional} "
                f"({self.data_alteracao.strftime('%d/%m/%Y %H:%M')})")
    

class HistoricoLP(models.Model):
    """
    Modelo para armazenar o histórico de alterações em LP.
    """
    lp = models.ForeignKey(LP, on_delete=models.CASCADE)
    data_alteracao = models.DateTimeField(auto_now_add=True, verbose_name="Data da Alteração")
    situacao_lp = models.CharField(max_length=30, verbose_name="Situação da LP")
    usuario_alteracao = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Usuário que Alterou")
    numero_prox_lp = models.IntegerField(verbose_name="Próximo Número da LP")
    proximo_lp = models.DateField(verbose_name="Próximo LP")
    mes_proximo_lp = models.IntegerField(verbose_name="Mês do Próximo LP")
    ano_proximo_lp = models.IntegerField(verbose_name="Ano do Próximo LP")
    dias_desconto_lp = models.IntegerField(verbose_name="Dias de Desconto LP")

    def __str__(self):
        return f'Histórico de {self.lp} em {self.data_alteracao}'


@transaction.atomic
def cadastrar_adicional_lp(cadastro, user, n_bloco_adicional, data_ultimo_adicional, n_bloco_lp, data_ultimo_lp, dias_desconto_adicional=0, dias_desconto_lp=0):
    """
    Cadastra Adicional e LP para um militar, calculando os próximos períodos.
    """
    # Adicional
    numero_adicional = int(n_bloco_adicional)
    proximo_adicional = data_ultimo_adicional + timedelta(days=1825 + dias_desconto_adicional)
    mes_proximo_adicional = proximo_adicional.month
    ano_proximo_adicional = proximo_adicional.year
    numero_prox_adicional = numero_adicional + 1

    adicional = Cadastro_adicional.objects.create(
        cadastro=cadastro,
        user_created=user, 
        numero_adicional=numero_adicional,
        data_ultimo_adicional=data_ultimo_adicional,
        numero_prox_adicional=numero_prox_adicional,
        proximo_adicional=proximo_adicional,
        mes_proximo_adicional=mes_proximo_adicional,
        ano_proximo_adicional=ano_proximo_adicional,
        dias_desconto_adicional=dias_desconto_adicional,
    )

    # LP
    numero_lp = int(n_bloco_lp)
    proximo_lp = data_ultimo_lp + timedelta(days=1825 + dias_desconto_lp)
    mes_proximo_lp = proximo_lp.month
    ano_proximo_lp = proximo_lp.year
    numero_prox_lp = numero_lp + 1
    lp = LP.objects.create(
        cadastro=cadastro,
        user_created=user, 
        numero_lp=numero_lp,
        data_ultimo_lp=data_ultimo_lp,
        numero_prox_lp=numero_prox_lp,
        proximo_lp=proximo_lp,
        mes_proximo_lp=mes_proximo_lp,
        ano_proximo_lp=ano_proximo_lp,
        dias_desconto_lp=dias_desconto_lp,
    )
    return adicional, lp



@receiver(post_save, sender=Cadastro_adicional)
def calcular_proximo_periodo_adicional(sender, instance, created, **kwargs):
    """
    Calcula e atualiza o próximo período de Adicional após salvar.
    """
    if hasattr(instance, '_calculando_proximo_periodo_adicional'):
        return

    instance._calculando_proximo_periodo_adicional = True

    if instance.data_ultimo_adicional:
        data_base = instance.data_ultimo_adicional
        instance.proximo_adicional = data_base + timedelta(days=1825 - (instance.dias_desconto_adicional or 0))
        instance.mes_proximo_adicional = instance.proximo_adicional.month
        instance.ano_proximo_adicional = instance.proximo_adicional.year
        instance.numero_prox_adicional = instance.numero_adicional + 1

    if not created and not instance._state.adding:
        instance.save(update_fields=[
            'proximo_adicional',
            'mes_proximo_adicional',
            'ano_proximo_adicional',
            'numero_prox_adicional'
        ])

    del instance._calculando_proximo_periodo_adicional



@receiver(post_save, sender=LP)
def calcular_proximo_periodo_lp(sender, instance, created, **kwargs):
    """
    Calcula e atualiza o próximo período de LP após salvar.
    """
    if hasattr(instance, '_calculando_proximo_periodo_lp'):
        return

    instance._calculando_proximo_periodo_lp = True

    if instance.data_ultimo_lp:
        data_base_lp = instance.data_ultimo_lp
        instance.proximo_lp = data_base_lp + timedelta(days=1825 - (instance.dias_desconto_lp or 0))
        instance.mes_proximo_lp = instance.proximo_lp.month
        instance.ano_proximo_lp = instance.proximo_lp.year
        instance.numero_prox_lp = instance.numero_lp + 1

    if not created and not instance._state.adding:
        instance.save(update_fields=[
            'proximo_lp',
            'mes_proximo_lp',
            'ano_proximo_lp',
            'numero_prox_lp'
        ])

    del instance._calculando_proximo_periodo_lp
