from django.contrib import admin
from .models import Chamado, Categoria, Anexo, Comentario

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('categoria', 'subcategoria', 'descricao')
    list_filter = ('categoria',)
    search_fields = ('categoria', 'subcategoria', 'descricao')

class AnexoInline(admin.TabularInline):
    model = Anexo
    extra = 1
    readonly_fields = ('enviado_em', 'autor')

class ComentarioInline(admin.TabularInline):
    model = Comentario
    extra = 1
    readonly_fields = ('criado_em', 'autor')
    fields = ('autor', 'texto', 'privado', 'criado_em')

@admin.register(Chamado)
class ChamadoAdmin(admin.ModelAdmin):
    list_display = ('protocolo', 'assunto', 'solicitante_nome', 'categoria', 'status', 'tecnico_responsavel', 'criado_em')
    list_filter = ('status', 'categoria', 'tecnico_responsavel')
    search_fields = ('protocolo', 'assunto', 'descricao', 'solicitante_nome', 'solicitante_email')
    readonly_fields = ('protocolo', 'criado_em', 'atualizado_em', 'data_resolucao', 'data_fechamento')
    fieldsets = (
        ('Detalhes do Chamado', {
            'fields': ('protocolo', 'assunto', 'descricao', 'categoria', 'status')
        }),
        ('Informações do Solicitante', {
            'fields': ('solicitante_nome', 'solicitante_email', 'solicitante_cpf', 'solicitante_telefone', 'usuario')
        }),
        ('Dados do Efetivo', {
            'fields': ('re', 'posto_grad', 'sgb', 'posto_secao', 'foto_militar')
        }),
        ('Atribuição e Prazos', {
            'fields': ('tecnico_responsavel', 'criado_em', 'atualizado_em', 'data_resolucao', 'data_fechamento')
        }),
    )
    inlines = [AnexoInline, ComentarioInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

@admin.register(Anexo)
class AnexoAdmin(admin.ModelAdmin):
    list_display = ('chamado', 'arquivo', 'enviado_em', 'autor')
    search_fields = ('chamado__protocolo',)
    readonly_fields = ('enviado_em', 'autor')

@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = ('chamado', 'autor', 'criado_em', 'privado')
    list_filter = ('privado', 'autor')
    search_fields = ('chamado__protocolo', 'texto')
    readonly_fields = ('criado_em', 'autor')