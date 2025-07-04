from django.conf import settings
from django.db import models
from django.utils.safestring import mark_safe
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.utils import timezone

# Definições de escolhas compartilhadas (mantidas como estão no seu arquivo)
N_CHOICES = [(i, f'{i:02d}') for i in range(1, 9)]
situacao_choices = (
    ("Aguardando", "Aguardando"),
    ("Concedido", "Concedido"),
    ("Concluído", "Concluído"),
)
dias_CHOICES = [
    (15, '15 Dias'), (30, '30 Dias'), (45, '45 Dias'),
    (60, '60 Dias'), (75, '75 Dias'), (90, '90 Dias'),
]
TIPO_CHOICE_OPTIONS = [
    ('fruicao', 'Fruição'), ('pecunia', 'Pecúnia'),
]


class LP(models.Model):
    # ... (O modelo LP permanece inalterado) ...
    class StatusLP(models.TextChoices):
        AGUARDANDO_REQUISITOS = 'aguardando_requisitos', 'Aguardando Requisitos'
        APTA_CONCESSAO = 'apta_concessao', 'Apta para Concessão'
        LANCADO_SIPA = 'lancado_sipa', 'Lançado no SIPA'
        CONCEDIDO = 'concedido', 'Concedido'
        PUBLICADO = 'publicado', 'Publicado'
        CONCLUIDO = 'concluido', 'Concluído'

    cadastro = models.ForeignKey('efetivo.Cadastro', on_delete=models.CASCADE, verbose_name="Cadastro")
    user_created = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='lps_criadas', verbose_name="Criado por")
    user_updated = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='lps_modificadas', verbose_name="Modificado por")
    usuario_conclusao = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='lps_concluidas', verbose_name="Concluído por")
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")
    data_conclusao = models.DateTimeField(null=True, blank=True, verbose_name="Data de Conclusão")

    numero_lp = models.PositiveSmallIntegerField(choices=N_CHOICES, verbose_name="Número da LP")
    data_ultimo_lp = models.DateField(null=True, blank=True, verbose_name="Data do Último LP")
    numero_prox_lp = models.PositiveSmallIntegerField(choices=N_CHOICES, verbose_name="Próximo Número da LP", null=True, blank=True)
    proximo_lp = models.DateField(null=True, blank=True, verbose_name="Próximo LP")
    mes_proximo_lp = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Mês do Próximo LP")
    ano_proximo_lp = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Ano do Próximo LP")
    dias_desconto_lp = models.PositiveSmallIntegerField(default=0, verbose_name="Dias de Desconto LP")
    bol_g_pm_lp = models.CharField(max_length=50, null=True, blank=True, verbose_name="BOL GPm LP")
    data_publicacao_lp = models.DateField(null=True, blank=True, verbose_name="Data Publicação LP")
    data_concessao_lp = models.DateField(null=True, blank=True, verbose_name="Data de Concessão da LP")
    lancamento_sipa = models.BooleanField(default=False, verbose_name="Lançamento no SIPA")
    
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    situacao_lp = models.CharField(max_length=30, choices=situacao_choices, default="Aguardando", verbose_name="Situação da LP")
    status_lp = models.CharField(
        max_length=30,
        choices=StatusLP.choices,
        default=StatusLP.AGUARDANDO_REQUISITOS,
        verbose_name="Status da LP"
    )
    _status_order_map = {
        StatusLP.AGUARDANDO_REQUISITOS: 0,
        StatusLP.APTA_CONCESSAO: 1,
        StatusLP.LANCADO_SIPA: 2,
        StatusLP.CONCEDIDO: 3,
        StatusLP.PUBLICADO: 4,
        StatusLP.CONCLUIDO: 5,
    }


    def get_progress_percentage(self):
        """
        Retorna a porcentagem de progresso da LP.
        """
        current_index = self._status_order_map.get(self.status_lp, 0)
        total_steps = len(self._status_order_map)
        
        if total_steps <= 1: 
            return 100 if current_index == 0 else 0
        
        return (current_index / (total_steps - 1)) * 100

    def get_progress_percentage_by_status(self):
        """
        Retorna o índice numérico do status atual (baseado em 0).
        Usado para a lógica de 'maior que forloop.counter0' no template.
        """
        return self._status_order_map.get(self.status_lp, 0)

    
    class Meta:
        verbose_name = "Licença Prêmio"
        verbose_name_plural = "Licenças Prêmio"
        unique_together = ('cadastro', 'numero_lp') # <--- ADICIONE ESTA LINHA
        # ordering = ['sua_ordem_aqui']
    def __str__(self):
        return f"LP {self.numero_lp} - {self.cadastro.nome_de_guerra}"

    def clean(self):
        # Validação para garantir que data_ultimo_lp não é futura
        if self.data_ultimo_lp and self.data_ultimo_lp > timezone.localdate():
            raise ValidationError({'data_ultimo_lp': 'A data do último LP não pode ser futura.'})

        # Validação para garantir que data_concessao_lp não é futura
        if self.data_concessao_lp and self.data_concessao_lp > timezone.localdate():
            raise ValidationError({'data_concessao_lp': 'A data de concessão não pode ser futura.'})
            
        # Validação para garantir que data_publicacao_lp não é futura
        if self.data_publicacao_lp and self.data_publicacao_lp > timezone.localdate():
            raise ValidationError({'data_publicacao_lp': 'A data de publicação não pode ser futura.'})
            
        # Validação para garantir que data_publicacao_lp não é anterior a data_concessao_lp
        if self.data_concessao_lp and self.data_publicacao_lp and \
           self.data_publicacao_lp < self.data_concessao_lp:
            raise ValidationError({'data_publicacao_lp': 'A data de publicação não pode ser anterior à data de concessão.'})
    


    
    def get_situacao_lp_choices(self):
        return self._meta.get_field('situacao_lp').choices
    

    @property
    def data_fim_periodo_lp(self):
        """
        Calcula a data de fim do período aquisitivo (último LP + 5 anos)
        Retorna None se data_ultimo_lp não estiver definida
        """
        if self.data_ultimo_lp:
            return self.data_ultimo_lp + timedelta(days=1825)
        return None
    
    @property
    def get_progress_percentage(self):
        # Calcula a porcentagem de progresso baseada nos status da LP
        status_order = [choice[0] for choice in self.StatusLP.choices]
        try:
            current_index = status_order.index(self.status_lp)
        except ValueError:
            current_index = 0
        
        if len(status_order) <= 1:
            return 0
        
        return (current_index / (len(status_order) - 1)) * 100

    def save(self, *args, **kwargs):
        # Atualiza o status automaticamente quando o período aquisitivo termina
        if self.status_lp == self.StatusLP.AGUARDANDO_REQUISITOS:
            if self.data_fim_periodo_lp and self.data_fim_periodo_lp <= date.today():
                self.status_lp = self.StatusLP.APTA_CONCESSAO
        super().save(*args, **kwargs)

    @property
    def get_progress_percentage_by_status(self):
        # Retorna o índice numérico do status atual para a barra de progresso da LP
        status_order = [choice[0] for choice in self.StatusLP.choices]
        try:
            return status_order.index(self.status_lp)
        except ValueError:
            return 0


class HistoricoLP(models.Model):
    # ... (O modelo HistoricoLP permanece inalterado) ...
    lp = models.ForeignKey(LP, on_delete=models.CASCADE, verbose_name="LP")
    usuario_alteracao = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Usuário da Alteração")
    data_alteracao = models.DateTimeField(auto_now_add=True, verbose_name="Data da Alteração")
    
    usuario_conclusao = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='historico_lps_concluidas', verbose_name="Concluído por (Histórico)")
    
    situacao_lp = models.CharField(max_length=30, choices=situacao_choices, verbose_name="Situação da LP")
    status_lp = models.CharField(max_length=30, choices=LP.StatusLP.choices, verbose_name="Status da LP")
    
    numero_lp = models.PositiveSmallIntegerField(choices=N_CHOICES, verbose_name="Número da LP")
    data_ultimo_lp = models.DateField(null=True, blank=True, verbose_name="Data do Último LP")
    numero_prox_lp = models.PositiveSmallIntegerField(choices=N_CHOICES, verbose_name="Próximo Número da LP", null=True, blank=True)
    proximo_lp = models.DateField(null=True, blank=True, verbose_name="Próximo LP")
    mes_proximo_lp = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Mês do Próximo LP")
    ano_proximo_lp = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Ano do Próximo LP")
    dias_desconto_lp = models.PositiveSmallIntegerField(default=0, verbose_name="Dias de Desconto LP")
    bol_g_pm_lp = models.CharField(max_length=50, null=True, blank=True, verbose_name="BOL GPm LP")
    data_publicacao_lp = models.DateField(null=True, blank=True, verbose_name="Data Publicação LP")
    data_concessao_lp = models.DateField(null=True, blank=True, verbose_name="Data de Concessão da LP")
    lancamento_sipa = models.BooleanField(default=False, verbose_name="Lançamento no SIPA")
    data_conclusao = models.DateTimeField(null=True, blank=True, verbose_name="Data de Conclusão (Histórico)")
    observacoes_historico = models.TextField(blank=True, verbose_name="Observações do Histórico")

    class Meta:
        verbose_name = "Histórico da LP"
        verbose_name_plural = "Histórico das LPs"

    def __str__(self):
        return f"Histórico LP {self.lp.numero_lp} ({self.lp.cadastro}) - {self.status_lp} em {self.data_alteracao.strftime('%d/%m/%Y %H:%M')}"
    


class LP_fruicao(models.Model):
    """
    Modelo para armazenar informações de fruição de LP, incluindo afastamentos.
    """

    DIAS_CHOICES = [
        (15, '15 Dias'), (30, '30 Dias'), (45, '45 Dias'),
        (60, '60 Dias'), (75, '75 Dias'), (90, '90 Dias'),
    ]
    TIPO_CHOICES = [
        ('fruicao', 'Fruição'), ('pecunia', 'Pecúnia'),
    ]

    cadastro = models.ForeignKey('efetivo.Cadastro', on_delete=models.CASCADE, verbose_name="Cadastro")
    lp_concluida = models.OneToOneField(LP, on_delete=models.CASCADE, related_name='previsao_associada', verbose_name="LP Concluída Associada")
    
    numero_lp = models.PositiveSmallIntegerField(verbose_name="Número da LP Concluída")
    data_concessao_lp = models.DateField(null=True, blank=True, verbose_name="Data de Concessão da LP")
    bol_g_pm_lp = models.CharField(max_length=50, null=True, blank=True, verbose_name="BOL G PM")
    data_publicacao_lp = models.DateField(null=True, blank=True, verbose_name="Data Publicação LP")

    tipo_periodo_afastamento = models.PositiveSmallIntegerField(
        choices=DIAS_CHOICES,
        null=True, blank=True,
        verbose_name="Tipo de Período de Afastamento"
    )

    tipo_choice = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES,
        null=True, blank=True,
        verbose_name="Tipo de Escolha"
    )

    user_created = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='previsoes_criadas', verbose_name="Criado por")
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")
    user_updated = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='previsoes_modificadas', verbose_name="Modificado por")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")
    dias_disponiveis = models.PositiveSmallIntegerField(default=90, verbose_name="Dias Disponíveis")
    dias_utilizados = models.PositiveSmallIntegerField(default=0, verbose_name="Dias Utilizados")
    data_inicio_afastamento = models.DateField(null=True, blank=True, verbose_name="Data de Início do Afastamento")
    data_termino_afastamento = models.DateField(null=True, blank=True, verbose_name="Data de Término do Afastamento")
    bol_int = models.CharField(max_length=50, null=True, blank=True, verbose_name="BOL Int")
    data_bol_int = models.DateField(null=True, blank=True, verbose_name="Data do BOL Int")
   
    class Meta:
        verbose_name = "Fruição de LP"
        verbose_name_plural = "Fruições de LPs"
        ordering = ['cadastro', 'numero_lp']

    def __str__(self):
        return f"Fruição para LP {self.numero_lp} de {self.cadastro.nome_de_guerra}"

    def clean(self):
        if self.data_inicio_afastamento and self.data_termino_afastamento:
            if self.data_termino_afastamento < self.data_inicio_afastamento:
                raise ValidationError("A data de término não pode ser anterior à data de início")
            
            delta = self.data_termino_afastamento - self.data_inicio_afastamento
            dias_calculados = delta.days + 1
            
            if self.tipo_periodo_afastamento and self.tipo_periodo_afastamento != dias_calculados:
                raise ValidationError(
                    f"O período selecionado ({self.tipo_periodo_afastamento} dias) não corresponde "
                    f"ao intervalo de datas ({dias_calculados} dias)"
                )
        
        if self.dias_utilizados < 0:
            raise ValidationError("Dias utilizados não podem ser negativos")
        
        super().clean()

    # Sobrescrevendo o método save para registrar o histórico de forma inteligente
    def save(self, *args, **kwargs):
        # Garante que os dias disponíveis sejam sempre calculados corretamente
        if self.dias_utilizados > 90:
            raise ValidationError("Dias utilizados não podem exceder 90 dias")
        
        self.dias_disponiveis = 90 - self.dias_utilizados
        
        # Verifica se é uma nova instância ou uma atualização
        is_new = not self.pk
        old_instance = None
        
        if not is_new:
            old_instance = LP_fruicao.objects.get(pk=self.pk)
        
        super().save(*args, **kwargs)
        
        # Cria registro de histórico se necessário
        if is_new:
            HistoricoFruicaoLP.criar_registro(self)
        elif old_instance:
            campos_rastreados = [
                'tipo_periodo_afastamento', 'dias_disponiveis', 'dias_utilizados',
                'tipo_choice', 'data_inicio_afastamento', 'data_termino_afastamento',
                'bol_int', 'data_bol_int'
            ]
            
            if any(getattr(old_instance, campo) != getattr(self, campo) for campo in campos_rastreados):
                HistoricoFruicaoLP.criar_registro(self)

    @property
    def dias_utilizados_percent(self):
        """Retorna a porcentagem de dias utilizados para a barra de progresso"""
        return (self.dias_utilizados / 90) * 100 if self.dias_utilizados else 0

class HistoricoFruicaoLP(models.Model):
    # ... (O modelo HistoricoFruicaoLP permanece inalterado, exceto pela classe Meta.ordering) ...
    fruicao = models.ForeignKey(LP_fruicao, on_delete=models.CASCADE, related_name='historico')
    data_alteracao = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    # Campos copiados da fruição
    tipo_periodo_afastamento = models.PositiveSmallIntegerField(
        choices=LP_fruicao.DIAS_CHOICES, 
        null=True, 
        blank=True,
        verbose_name="Dias de Afastamento"
    )
    dias_disponiveis = models.PositiveSmallIntegerField(verbose_name="Dias Disponíveis")
    dias_utilizados = models.PositiveSmallIntegerField(verbose_name="Dias Utilizados")
    tipo_choice = models.CharField(
        max_length=10, 
        choices=LP_fruicao.TIPO_CHOICES, 
        null=True, 
        blank=True,
        verbose_name="Tipo de Escolha"
    )
    
    data_inicio_afastamento = models.DateField(
        null=True, 
        blank=True, 
        verbose_name="Data de Início do Afastamento"
    )
    data_termino_afastamento = models.DateField(
        null=True, 
        blank=True, 
        verbose_name="Data de Término do Afastamento"
    )
    bol_int = models.CharField(
        max_length=50, 
        null=True, 
        blank=True, 
        verbose_name="BOL Int"
    )
    data_bol_int = models.DateField(
        null=True, 
        blank=True, 
        verbose_name="Data do BOL Int"
    )
    
    class Meta:
        ordering = ['-data_alteracao'] # Garante que os registros mais recentes apareçam primeiro
        verbose_name = "Histórico de Fruição"
        verbose_name_plural = "Históricos de Fruições"
    
    @classmethod
    def criar_registro(cls, fruicao):
        return cls.objects.create(
            fruicao=fruicao,
            usuario=getattr(fruicao, 'user_updated', None) or getattr(fruicao, 'user_created', None),
            tipo_periodo_afastamento=fruicao.tipo_periodo_afastamento,
            dias_disponiveis=fruicao.dias_disponiveis,
            dias_utilizados=fruicao.dias_utilizados,
            tipo_choice=fruicao.tipo_choice,
            data_inicio_afastamento=fruicao.data_inicio_afastamento,
            data_termino_afastamento=fruicao.data_termino_afastamento,
            bol_int=fruicao.bol_int,
            data_bol_int=fruicao.data_bol_int
        )