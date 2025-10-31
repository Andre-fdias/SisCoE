from django.contrib import admin
from .models import Chamado, Categoria, Anexo, Comentario

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome',)

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
        ('Atribuição e Prazos', {
            'fields': ('tecnico_responsavel', 'criado_em', 'atualizado_em', 'data_resolucao', 'data_fechamento')
        }),
    )
    inlines = [AnexoInline, ComentarioInline]

    def save_model(self, request, obj, form, change):
        # Preenche o autor de comentários e anexos automaticamente
        if form.changed_data:
            if 'comentarios' in form.changed_data:
                for comentario in form.cleaned_data['comentarios']:
                    if not comentario.autor_id:
                        comentario.autor = request.user
            if 'anexos' in form.changed_data:
                for anexo in form.cleaned_data['anexos']:
                    if not anexo.autor_id:
                        anexo.autor = request.user
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