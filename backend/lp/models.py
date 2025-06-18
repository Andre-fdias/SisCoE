# backend/lp/models.py

from django.conf import settings
from django.db import models
from django.utils.safestring import mark_safe
from datetime import datetime, timedelta, date
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

class LP(models.Model):
    """
    Modelo para representar a Licença Prêmio (LP) de um servidor.
    """
    class StatusLP(models.TextChoices):
        AGUARDANDO_REQUISITOS = 'aguardando_requisitos', 'Aguardando Requisitos'
        APTA_CONCESSAO = 'apta_concessao', 'Apta para Concessão'
        LANCADO_SIPA = 'lancado_sipa', 'Lançado no SIPA' # Ordem corrigida
        CONCEDIDO = 'concedido', 'Concedido'             # Ordem corrigida
        PUBLICADO = 'publicado', 'Publicado'             # Ordem corrigida
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
        total_steps = len(self._status_order_map) # Usar o tamanho do mapa para garantir consistência
        
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
            # 5 anos = 365 * 5 = 1825 dias
            return self.data_ultimo_lp + timedelta(days=1825)
        return None
    
    @property
    def get_progress_percentage(self):
        # Calcula a porcentagem de progresso baseada nos status da LP
        status_order = [choice[0] for choice in self.StatusLP.choices]
        try:
            current_index = status_order.index(self.status_lp)
        except ValueError:
            current_index = 0 # Fallback se o status não for encontrado
        
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
            return 0 # Fallback se o status não for encontrado

class HistoricoLP(models.Model):
    lp = models.ForeignKey(LP, on_delete=models.CASCADE, verbose_name="Licença Prêmio")
    usuario_alteracao = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Usuário da Alteração")
    data_alteracao = models.DateTimeField(auto_now_add=True, verbose_name="Data da Alteração")
    
    # Campos para registrar o estado da LP no momento da alteração
    situacao_lp = models.CharField(max_length=30, choices=situacao_choices, verbose_name="Situação da LP")
    status_lp = models.CharField(
        max_length=30,
        choices=LP.StatusLP.choices,
        verbose_name="Status da LP"
    )
    numero_lp = models.PositiveSmallIntegerField(choices=N_CHOICES, verbose_name="Número da LP")
    data_ultimo_lp = models.DateField(verbose_name="Data do Último LP")
    numero_prox_lp = models.PositiveSmallIntegerField(choices=N_CHOICES, verbose_name="Próximo Número da LP", null=True, blank=True)
    proximo_lp = models.DateField(null=True, blank=True, verbose_name="Próximo LP")
    mes_proximo_lp = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Mês do Próximo LP")
    ano_proximo_lp = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Ano do Próximo LP")
    dias_desconto_lp = models.PositiveSmallIntegerField(default=0, verbose_name="Dias de Desconto LP")
    bol_g_pm_lp = models.CharField(max_length=50, null=True, blank=True, verbose_name="BOL GPm LP")
    data_publicacao_lp = models.DateField(null=True, blank=True, verbose_name="Data Publicação LP")
    data_concessao_lp = models.DateField(null=True, blank=True, verbose_name="Data de Concessão da LP")
    lancamento_sipa = models.BooleanField(default=False, verbose_name="Lançamento no SIPA")
    
    observacoes_historico = models.TextField(blank=True, verbose_name="Observações do Histórico")

    class Meta:
        verbose_name = "Histórico de Licença Prêmio"
        verbose_name_plural = "Históricos de Licenças Prêmio"
        ordering = ['-data_alteracao'] # Ordena pelo mais recente