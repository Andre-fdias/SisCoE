from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth import get_user_model # Importar o modelo de usuário
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from import_export.admin import ImportExportModelAdmin # Importar ImportExportModelAdmin

from .models import Posto, Cidade, Contato, Pessoal

# --- Classes Inline existentes (mantidas) ---
class ContatoInline(admin.TabularInline):
    model = Contato
    extra = 1
    classes = ('collapse',)
    fields = ('telefone', 'email', 'cep', 'cidade')

class PessoalInline(admin.TabularInline):
    model = Pessoal
    extra = 1
    classes = ('collapse',)
    fieldsets = (
        (None, {
            'fields': ('cel', 'ten_cel', 'maj', 'cap', 'tenqo', 'tenqa', 'asp', 'st_sgt', 'cb_sd')
        }),
    )

class CidadeInline(admin.StackedInline):
    model = Cidade
    extra = 1
    fields = ('municipio', 'bandeira', 'latitude', 'longitude')
    readonly_fields = ('bandeira_preview',)

    def bandeira_preview(self, instance):
        if instance.bandeira:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                instance.bandeira.url
            )
        return "Sem imagem"
    bandeira_preview.short_description = "Pré-visualização"

# --- Resources para Exportação/Importação (Novas) ---

class PostoResource(resources.ModelResource):
    # O campo 'usuario' é uma ForeignKey para o modelo de usuário.
    # Usamos ForeignKeyWidget para permitir que o import/export use o 'username'
    # para identificar o usuário, em vez do ID.
    usuario = fields.Field(
        column_name='usuario',
        attribute='usuario',
        widget=ForeignKeyWidget(get_user_model(), 'username')
    )

    class Meta:
        model = Posto
        # Campos que serão incluídos na exportação/importação
        fields = (
            'id', 'sgb', 'posto_secao', 'posto_atendimento',
            'cidade_posto', 'tipo_cidade', 'op_adm',
            'data_criacao', 'usuario'
        )
        # Define a ordem das colunas no arquivo exportado
        export_order = fields
        # Exclua campos como 'quartel' (ImageField) se não quiser importá-los/exportá-los diretamente
        exclude = ('quartel',) # Excluindo o campo de imagem para importação/exportação direta


class ContatoResource(resources.ModelResource):
    # O campo 'posto' é uma ForeignKey para o modelo Posto.
    # Usamos ForeignKeyWidget para vincular pelo 'posto_atendimento' do Posto.
    posto = fields.Field(
        column_name='posto_atendimento',  # Nome da coluna no arquivo de importação/exportação
        attribute='posto',
        widget=ForeignKeyWidget(Posto, 'posto_atendimento') # Vincula pelo campo 'posto_atendimento' do modelo Posto
    )

    class Meta:
        model = Contato
        fields = (
            'posto', 'telefone', 'rua', 'numero', 'complemento',
            'bairro', 'cidade', 'cep', 'email', 'longitude', 'latitude'
        )
        export_order = fields


class PessoalResource(resources.ModelResource):
    # O campo 'posto' é uma ForeignKey para o modelo Posto.
    # Usamos ForeignKeyWidget para vincular pelo 'posto_atendimento' do Posto.
    posto = fields.Field(
        column_name='posto_atendimento',
        attribute='posto',
        widget=ForeignKeyWidget(Posto, 'posto_atendimento')
    )

    class Meta:
        model = Pessoal
        fields = (
            'posto', 'cel', 'ten_cel', 'maj', 'cap',
            'tenqo', 'tenqa', 'asp', 'st_sgt', 'cb_sd'
        )
        export_order = fields


class CidadeResource(resources.ModelResource):
    # O campo 'posto' é uma ForeignKey para o modelo Posto.
    # Usamos ForeignKeyWidget para vincular pelo 'posto_atendimento' do Posto.
    posto = fields.Field(
        column_name='posto_atendimento',
        attribute='posto',
        widget=ForeignKeyWidget(Posto, 'posto_atendimento')
    )

    class Meta:
        model = Cidade
        fields = (
            'posto', 'descricao', 'municipio', 'longitude', 'latitude'
        )
        export_order = fields
        # Exclua campos como 'bandeira' (ImageField) se não quiser importá-los/exportá-los diretamente
        exclude = ('bandeira',) # Excluindo o campo de imagem para importação/exportação direta

# --- Classes Admin existentes (modificadas para ImportExportModelAdmin) ---

@admin.register(Posto)
class PostoAdmin(ImportExportModelAdmin): # Herda de ImportExportModelAdmin
    resource_class = PostoResource # Associa o Resource
    readonly_fields = ('quartel_preview',)

    def quartel_preview(self, obj):
        if obj.quartel:
            return format_html(
                '<img src="{}" style="max-height: 200px;"/>',
                obj.quartel.url
            )
        return "Nenhuma imagem cadastrada"
    quartel_preview.short_description = "Pré-visualização do Quartel"

    fieldsets = (
        ('Identificação', {
            'fields': ('sgb', 'posto_secao', 'posto_atendimento', 'quartel', 'quartel_preview')
        }),
        ('Localização', {
            'fields': ('cidade_posto', 'tipo_cidade', 'op_adm')
        }),
        ('Registro', {
            'classes': ('collapse',),
            'fields': ('usuario', 'data_criacao'),
        }),
    )

    inlines = [CidadeInline, ContatoInline, PessoalInline]
    list_display = ('posto_atendimento', 'sgb_display', 'cidade_posto', 'tipo_cidade')
    search_fields = ('posto_atendimento', 'cidade_posto')
    list_filter = ('sgb', 'op_adm')
    ordering = ('-data_criacao',)

    def sgb_display(self, obj):
        return obj.get_sgb_display()
    sgb_display.short_description = 'SGB'

@admin.register(Cidade)
class CidadeAdmin(ImportExportModelAdmin): # Herda de ImportExportModelAdmin
    resource_class = CidadeResource # Associa o Resource
    list_display = ('municipio', 'posto_link', 'bandeira_preview')
    search_fields = ('municipio', 'posto__posto_atendimento')
    list_select_related = ('posto',)

    def posto_link(self, obj):
        return format_html(
            '<a href="/admin/municipios/posto/{}/change/">{}</a>',
            obj.posto.id,
            obj.posto.posto_atendimento
        )
    posto_link.short_description = 'Posto'

    def bandeira_preview(self, obj):
        if obj.bandeira:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px;" />',
                obj.bandeira.url
            )
        return "N/A"
    bandeira_preview.short_description = 'Bandeira'

@admin.register(Contato)
class ContatoAdmin(ImportExportModelAdmin): # Herda de ImportExportModelAdmin
    resource_class = ContatoResource # Associa o Resource
    list_display = ('posto', 'telefone', 'email', 'cep')
    search_fields = ('posto__posto_atendimento', 'telefone', 'email')

@admin.register(Pessoal)
class PessoalAdmin(ImportExportModelAdmin): # Herda de ImportExportModelAdmin
    resource_class = PessoalResource # Associa o Resource
    list_display = ('posto', 'total_efetivo')
    search_fields = ('posto__posto_atendimento',)

    def total_efetivo(self, obj):
        return sum([
            obj.cel, obj.ten_cel, obj.maj, obj.cap,
            obj.tenqo, obj.tenqa, obj.asp, obj.st_sgt, obj.cb_sd
        ])
    total_efetivo.short_description = 'Total de Militares'
