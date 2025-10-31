from django.db import models
from django.conf import settings
from django.utils import timezone

class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome da Categoria")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ['nome']

    def __str__(self):
        return self.nome

def gerar_protocolo():
    """Gera um número de protocolo único no formato TCK-ANO-SEQUENCIAL."""
    ano = timezone.now().year
    ultimo_chamado = Chamado.objects.filter(protocolo__startswith=f'TCK-{ano}').order_by('protocolo').last()
    
    if not ultimo_chamado:
        sequencial = 1
    else:
        sequencial = int(ultimo_chamado.protocolo.split('-')[-1]) + 1
        
    return f'TCK-{ano}-{sequencial:05d}'

class Chamado(models.Model):
    STATUS_CHOICES = (
        ('aberto', 'Aberto'),
        ('em_atendimento', 'Em Atendimento'),
        ('aguardando_usuario', 'Aguardando Resposta do Usuário'),
        ('resolvido', 'Resolvido'),
        ('fechado', 'Fechado'),
    )

    protocolo = models.CharField(max_length=20, unique=True, default=gerar_protocolo, editable=False)
    
    # Usuário que abriu o chamado. Pode ser um usuário registrado ou um cliente externo.
    solicitante_nome = models.CharField(max_length=150, verbose_name="Nome do Solicitante")
    solicitante_email = models.EmailField(verbose_name="Email do Solicitante")
    solicitante_cpf = models.CharField(max_length=11, verbose_name="CPF do Solicitante", blank=True, null=True)
    solicitante_telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone do Solicitante")
    
    # Se o solicitante for um usuário registrado no sistema, ele será vinculado aqui.
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='chamados_criados',
        verbose_name="Usuário Registrado"
    )

    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, verbose_name="Categoria")
    assunto = models.CharField(max_length=255, verbose_name="Assunto")
    descricao = models.TextField(verbose_name="Descrição do Problema")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aberto', verbose_name="Status")
    
    tecnico_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='chamados_atribuidos',
        limit_choices_to={'is_staff': True},
        verbose_name="Técnico Responsável"
    )
    
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    data_resolucao = models.DateTimeField(null=True, blank=True, verbose_name="Data de Resolução")
    data_fechamento = models.DateTimeField(null=True, blank=True, verbose_name="Data de Fechamento")

    class Meta:
        verbose_name = "Chamado"
        verbose_name_plural = "Chamados"
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.protocolo} - {self.assunto}'

class Anexo(models.Model):
    chamado = models.ForeignKey(Chamado, on_delete=models.CASCADE, related_name='anexos')
    arquivo = models.FileField(upload_to='chamados_anexos/%Y/%m/%d/', verbose_name="Arquivo")
    descricao = models.CharField(max_length=255, blank=True, null=True, verbose_name="Descrição do Anexo")
    enviado_em = models.DateTimeField(auto_now_add=True)
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Anexo"
        verbose_name_plural = "Anexos"
        ordering = ['-enviado_em']

    def __str__(self):
        return f'Anexo para o chamado {self.chamado.protocolo}'

class Comentario(models.Model):
    chamado = models.ForeignKey(Chamado, on_delete=models.CASCADE, related_name='comentarios')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Autor")
    texto = models.TextField(verbose_name="Comentário")
    criado_em = models.DateTimeField(auto_now_add=True)
    privado = models.BooleanField(default=False, verbose_name="Comentário Privado", help_text="Comentários privados são visíveis apenas para a equipe técnica.")

    class Meta:
        verbose_name = "Comentário"
        verbose_name_plural = "Comentários"
        ordering = ['criado_em']

    def __str__(self):
        return f'Comentário de {self.autor} em {self.chamado.protocolo}'