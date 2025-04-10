# models.py
from django.db import models
from backend.accounts.models import User
import locale
locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

class Conversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class Chat(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='chats')
    message = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    arquivado = models.BooleanField(default=False)

    def __str__(self):
        return self.message
    

    # backend/faisca/models.py
class SystemAgentInteraction(models.Model):
    TIPOS_ACAO = (
        ('PESQUISA', 'Pesquisa de Dados'),
        ('RELATORIO', 'Geração de Relatório'),
        ('ANALISE', 'Análise Preditiva'),
        ('CONTROLE', 'Controle de Sistema'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comando = models.TextField()
    resposta = models.TextField()
    tipo_acao = models.CharField(max_length=20, choices=TIPOS_ACAO)
    executado_com_sucesso = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)
    modelos_afetados = models.CharField(max_length=255, blank=True)


class FaiscaAgentConversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

class Meta:
        verbose_name = "Conversa do Faisca Agent"
        verbose_name_plural = "Conversas do Faisca Agent"

class FaiscaAgentChat(models.Model):
    conversation = models.ForeignKey(FaiscaAgentConversation, on_delete=models.CASCADE, related_name='chats')
    message = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Meta:
        verbose_name = "Mensagem do Faisca Agent"
        verbose_name_plural = "Mensagens do Faisca Agent"


        # backend/faisca/models.py
class FaiscaAgentQueryLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    query = models.TextField()
    response = models.TextField()
    was_successful = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    execution_time = models.FloatField(help_text="Tempo de execução em segundos")
    
    class Meta:
        verbose_name = "Log de Consulta do Faisca"
        verbose_name_plural = "Logs de Consultas do Faisca"
        ordering = ['-created_at']

    def __str__(self):
        return f"Consulta de {self.user} em {self.created_at}"