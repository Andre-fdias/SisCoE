from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError

class Categoria(models.Model):
    # Categorias principais alinhadas às funcionalidades do sistema
    TIPO_PROBLEMA_CHOICES = (
        ('gestao_usuarios', 'Gestão de Usuários e Acessos'),
        ('cadastro_efetivo', 'Cadastro do Efetivo'),
        ('relatorios_documentos', 'Relatórios e Documentos'),
        ('ferramentas_sistema', 'Ferramentas do Sistema'),
        ('cursos_qualificacoes', 'Cursos e Qualificações'),
        ('outros', 'Outros'),
    )

    # Subcategorias associadas a cada categoria principal
    SUBCATEGORIA_CHOICES = (
        # Gestão de Usuários
        ('erro_login', 'Erro ao fazer login'),
        ('alteracao_senha', 'Dificuldade para alterar a senha'),
        ('problema_permissao', 'Usuário sem permissão para uma área'),
        ('cadastro_usuario', 'Problema no cadastro de novo usuário'),

        # Cadastro do Efetivo
        ('erro_buscar_militar', 'Não consigo encontrar um militar'),
        ('dados_desatualizados', 'Dados do militar estão desatualizados'),
        ('problema_promocao', 'Erro ao registrar promoção'),
        ('erro_situacao', 'Erro ao alterar situação do militar'),

        # Relatórios e Documentos
        ('geracao_relatorio', 'Relatório não gera ou apresenta erro'),
        ('exportacao_dados', 'Exportação de dados (CSV/Excel) falhou'),
        ('upload_documento', 'Não consigo anexar um documento'),
        ('visualizacao_documento', 'Erro ao visualizar um documento'),

        # Ferramentas do Sistema
        ('erro_calculadora', 'Erro na Calculadora'),
        ('problema_agenda', 'Problema na Agenda/Calendário'),
        ('erro_busca_global', 'Busca global não retorna resultados'),

        # Cursos e Qualificações
        ('inscricao_curso', 'Erro ao inscrever em um curso'),
        ('visualizacao_historico', 'Histórico de cursos não aparece'),

        # Outros
        ('duvida_geral', 'Dúvida sobre como usar uma função'),
        ('sugestao_melhoria', 'Sugestão de melhoria para o sistema'),
        ('outro_problema', 'Outro tipo de problema não listado'),
    )

    categoria = models.CharField(
        max_length=50,
        choices=TIPO_PROBLEMA_CHOICES,
        verbose_name="Categoria do Problema"
    )
    subcategoria = models.CharField(
        max_length=50,
        choices=SUBCATEGORIA_CHOICES,
        verbose_name="Subcategoria"
    )
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ['categoria', 'subcategoria']
        unique_together = ['categoria', 'subcategoria']

    def __str__(self):
        return f"{self.get_categoria_display()} - {self.get_subcategoria_display()}"

def gerar_protocolo():
    """Gera um número de protocolo único no formato TCK-ANO-SEQUENCIAL."""
    ano = timezone.now().year
    ultimo_chamado = Chamado.objects.filter(protocolo__startswith=f'TCK-{ano}').order_by('protocolo').last()
    
    if not ultimo_chamado:
        sequencial = 1
    else:
        sequencial = int(ultimo_chamado.protocolo.split('-')[-1]) + 1
        
    return f'TCK-{ano}-{sequencial:05d}'

def validate_file_size(value):
    """Valida o tamanho do arquivo (máximo 2MB)"""
    filesize = value.size
    if filesize > 2 * 1024 * 1024:  # 2MB
        raise ValidationError("O tamanho máximo do arquivo é 2MB.")
    return value

class Chamado(models.Model):
    STATUS_CHOICES = (
        ('aberto', 'Aberto'),
        ('em_atendimento', 'Em Atendimento'),
        ('aguardando_usuario', 'Aguardando Resposta do Usuário'),
        ('resolvido', 'Resolvido'),
        ('fechado', 'Fechado'),
    )

    protocolo = models.CharField(max_length=20, unique=True, default=gerar_protocolo, editable=False)
    
    # Dados do solicitante (vinculados ao cadastro do efetivo)
    solicitante_nome = models.CharField(max_length=150, verbose_name="Nome do Solicitante", blank=True, null=True)
    solicitante_email = models.EmailField(verbose_name="Email do Solicitante", blank=True, null=True)
    solicitante_cpf = models.CharField(max_length=14, verbose_name="CPF do Solicitante", blank=True, null=True)
    solicitante_telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone do Solicitante")
    
    # Dados do efetivo (preenchidos automaticamente)
    re = models.CharField(max_length=7, blank=True, null=True, verbose_name="RE")
    posto_grad = models.CharField(max_length=100, blank=True, null=True, verbose_name="Posto/Graduação")
    sgb = models.CharField(max_length=9, blank=True, null=True, verbose_name="SGB")
    posto_secao = models.CharField(max_length=100, blank=True, null=True, verbose_name="Posto/Seção")
    
    # Foto do militar (opcional)
    foto_militar = models.ImageField(upload_to='chamados_fotos/', blank=True, null=True, verbose_name="Foto do Militar")

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
        # CORREÇÃO: Use is_admin em vez de is_staff
        limit_choices_to={'is_admin': True},
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
    arquivo = models.FileField(
        upload_to='chamados_anexos/%Y/%m/%d/', 
        verbose_name="Arquivo",
        validators=[validate_file_size]
    )
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