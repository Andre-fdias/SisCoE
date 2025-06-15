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
    cadastro = models.ForeignKey('efetivo.Cadastro', on_delete=models.CASCADE, verbose_name="Cadastro")
    user_created = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lps_criadas',
        verbose_name="Criado por"
    )
    user_updated = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lps_modificadas',
        verbose_name="Modificado por"
    )
    usuario_conclusao = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lps_concluidas',
        verbose_name="Concluído por"
    )
    data_cadastro = models.DateField( # Este é o campo 'created_at' que o admin estava procurando
        default=timezone.now,
        verbose_name="Data de Cadastro"
    )
    data_atualizacao = models.DateField( # Este é o campo 'updated_at' que o admin estava procurando
        auto_now=True,
        verbose_name="Última Atualização"
    )
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )
    dias_desconto_lp = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Dias de Desconto LP"
    )

    # Campos específicos da LP
    numero_lp = models.PositiveSmallIntegerField(
        choices=N_CHOICES,
        verbose_name="Número da LP"
    )
    data_ultimo_lp = models.DateField(
        verbose_name="Data do Último LP" # Esta deve ser a data do último bloco aquisitivo finalizado
    )

    
    numero_prox_lp = models.PositiveSmallIntegerField(
        choices=N_CHOICES,
        verbose_name="Próximo Número da LP",
        null=True, blank=True 
    )
    proximo_lp = models.DateField(
        null=True,
        blank=True,
        verbose_name="Próximo LP" 
    )
    mes_proximo_lp = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Mês do Próximo LP"
    )
    ano_proximo_lp = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Ano do Próximo LP"
    )
    situacao_lp = models.CharField(
        max_length=30,
        choices=situacao_choices,
        default="Aguardando",
        verbose_name="Situação da LP"
    )
    data_concessao_lp = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de Concessão da LP"
    )
    bol_g_pm_lp = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="BOL GPm LP"
    )
    data_publicacao_lp = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data Publicação LP"
    )
    lancamento_sipa = models.BooleanField(
        default=False,
        verbose_name="Lançamento no SIPA"
    )

    class StatusLP(models.TextChoices):
        AGUARDANDO_REQUISITOS = 'AGUARDANDO_REQUISITOS', 'Aguardando Requisitos'
        APTA_CONCESSAO = 'APTA_CONCESSAO', 'Apta para Concessão'
        CONCEDIDA = 'CONCEDIDA', 'Concedida'
        EM_GOZO = 'EM_GOZO', 'Em Gozo'
        CONCLUIDA = 'CONCLUIDA', 'Concluída'
        PENDENTE_SIPA = 'PENDENTE_SIPA', 'Pendente Lançamento SIPA'
        INDENIZADA = 'INDENIZADA', 'Indenizada'
        SOBRESTADA = 'SOBRESTADA', 'Sobrestada'

    status_lp = models.CharField(
        max_length=30,
        choices=StatusLP.choices,
        default=StatusLP.AGUARDANDO_REQUISITOS,
        verbose_name="Status da LP"
    )

    class Meta:
        verbose_name = "Licença Prêmio"
        verbose_name_plural = "Licenças Prêmio"
        # CORREÇÃO: Usando 'cadastro__nome_de_guerra' em vez de 'cadastro__nome_guerra'
        ordering = ['cadastro__nome_de_guerra', 'numero_lp'] 
        unique_together = ('cadastro', 'numero_lp')

    def __str__(self):
        return f"LP {self.numero_lp} de {self.cadastro.nome_guerra}"

    def clean(self):
        if self.data_concessao_lp and self.data_publicacao_lp and self.data_publicacao_lp < self.data_concessao_lp:
            raise ValidationError({'data_publicacao_lp': 'A data de publicação não pode ser anterior à data de concessão.'})

        if self.status_lp == self.StatusLP.CONCLUIDA and not self.data_concessao_lp:
            raise ValidationError({'data_concessao_lp': 'A data de concessão é obrigatória para LPs Concluídas.'})
        
        if not self.data_inicio_periodo:
            raise ValidationError({'data_inicio_periodo': 'A data de início do período aquisitivo é obrigatória.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        
        if self.data_ultimo_lp:
            data_base_proximo_periodo = self.data_ultimo_lp + timedelta(days=1)
            self.proximo_lp = data_base_proximo_periodo + relativedelta(years=5) - timedelta(days=1)
            
            if self.proximo_lp:
                self.mes_proximo_lp = self.proximo_lp.month
                self.ano_proximo_lp = self.proximo_lp.year
            
            if self.numero_lp:
                self.numero_prox_lp = self.numero_lp + 1
        
        super().save(*args, **kwargs)

class HistoricoLP(models.Model):
    lp = models.ForeignKey(LP, on_delete=models.CASCADE, related_name='historicos_lp')
    usuario_alteracao = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    data_alteracao = models.DateTimeField(auto_now_add=True)
    
    situacao_lp = models.CharField(max_length=30, choices=situacao_choices, verbose_name="Situacao da LP")
    status_lp = models.CharField(max_length=30, choices=LP.StatusLP.choices, verbose_name="Status da LP")
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
        ordering = ['-data_alteracao']
        
    def __str__(self):
        return f"Histórico LP {self.lp.numero_lp} de {self.lp.cadastro.nome_guerra} em {self.data_alteracao.strftime('%d/%m/%Y %H:%M')}"
