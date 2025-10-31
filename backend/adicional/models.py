# adicional/models.py
from django.conf import settings
from django.db import models
from django.utils.safestring import mark_safe
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.utils import timezone

# Definições de escolhas compartilhadas
N_CHOICES = [(i, f'{i:02d}') for i in range(1, 9)]
situacao_choices = (
    ("Aguardando", "Aguardando"),
    ("Concedido", "Concedido"),
    ("Concluído", "Concluído"),
)

class Cadastro_adicional(models.Model):
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
    numero_adicional = models.PositiveSmallIntegerField(choices=N_CHOICES, verbose_name="Número do Adicional")
    data_ultimo_adicional = models.DateField(verbose_name="Data do Último Adicional")
    numero_prox_adicional = models.PositiveSmallIntegerField(choices=N_CHOICES, default=1, verbose_name="Próximo Número do Adicional")
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

        if self.numero_prox_adicional > 8:
            raise ValidationError({'numero_prox_adicional': 'O próximo número do adicional não pode ser maior que 8'})
        
        if self.numero_prox_adicional < 1:
            raise ValidationError({'numero_prox_adicional': 'O próximo número do adicional não pode ser menor que 1'})

    # Métodos de exibição de usuário
    def user_created_display(self):
        if self.user_created and hasattr(self.user_created, 'profile'):
            return f"{self.user_created.profile.posto_grad} {self.user_created.profile.re}-{self.user_created.profile.dig} {self.user_created.last_name}"
        elif self.user_created:
            # Use email em vez de username
            return self.user_created.get_full_name() or self.user_created.email
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

    def get_search_result(self):
        return {
            'title': f"Adicional {self.numero_adicional} - {self.cadastro.nome}",
            'fields': {
                'Número': self.numero_adicional,
                'BOL GPm': self.bol_g_pm_adicional,
                'Situação': self.situacao_adicional
            }
        }


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
        return cls.N_CHOICES

    @property
    def status_adicional_ordenacao(self):
        ordem = {
            'aguardando_requisitos': 1,
            'faz_jus': 2,
            'lancado_sipa': 3,
            'aguardando_publicacao': 4,
            'publicado': 5,
            'encerrado': 6,
        }
        return ordem.get(self.status_adicional, 0)

    @property
    def total_etapas(self):
        return len(self.StatusAdicional.choices)

    def ultimo_adicional(self):
        return self.cadastro_adicional_set.order_by('-created_at').first()

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

    # Réplica dos campos do Cadastro_adicional
    cadastro = models.ForeignKey(
        'efetivo.Cadastro',
        on_delete=models.CASCADE,
        verbose_name="Cadastro",
        null=False,
        blank=False
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
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")
    data_conclusao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de Conclusão"
    )
    numero_adicional = models.PositiveSmallIntegerField(
        choices=N_CHOICES,
        verbose_name="Número do Adicional",
        default=1
    )
    data_ultimo_adicional = models.DateField(
        verbose_name="Data do Último Adicional",
        default=timezone.now
    )
    numero_prox_adicional = models.PositiveSmallIntegerField(
        choices=N_CHOICES,
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
    
    def get_search_result(self):
        return {
            'title': f"Histórico Adicional {self.numero_adicional} - {self.cadastro.nome}",
            'fields': {
                'Número': self.numero_adicional,
                'Situação': self.situacao_adicional,
                'Data Alteração': self.data_alteracao.strftime('%d/%m/%Y %H:%M')
            }
        }