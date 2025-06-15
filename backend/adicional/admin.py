from django.contrib import admin
from .models import Cadastro_adicional, HistoricoCadastro
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.contrib import messages

class HistoricoCadastroInline(admin.TabularInline):
    model = HistoricoCadastro
    extra = 0
    readonly_fields = ('data_alteracao', 'usuario_alteracao', 'situacao_adicional', 'status_adicional')
    fields = ('data_alteracao', 'usuario_alteracao', 'situacao_adicional', 'status_adicional')
    ordering = ('-data_alteracao',)
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(Cadastro_adicional)
class CadastroAdicionalAdmin(admin.ModelAdmin):
    list_display = (
        're_militar', 
        'posto_graduacao', 
        'numero_adicional', 
        'status_adicional_badge', 
        'proximo_adicional', 
        'dias_faltantes',
        'acoes'
    )
    list_filter = (
        'status_adicional', 
        'situacao_adicional', 
        'sexta_parte', 
        'confirmacao_6parte',
    )
    search_fields = (
        'cadastro__re', 
        'cadastro__nome', 
        # CORREÇÃO: Removido nome_guerra que não existe
        'numero_adicional',
        'bol_g_pm_adicional'
    )
    readonly_fields = (
        'dias_faltantes', 
        'user_created', 
        'created_at', 
        'user_updated', 
        'updated_at',
        'proximo_adicional',
        'link_cadastro'
    )
    fieldsets = (
        ('Identificação', {
            'fields': (
                'link_cadastro', 
                'numero_adicional',
                'numero_prox_adicional'
            )
        }),
        ('Datas Chave', {
            'fields': (
                'data_ultimo_adicional', 
                'proximo_adicional',
                'dias_faltantes',
                'dias_desconto_adicional'
            )
        }),
        ('Situação', {
            'fields': (
                'situacao_adicional', 
                'status_adicional',
                'sexta_parte',
                'confirmacao_6parte'
            )
        }),
        ('Publicação', {
            'fields': (
                'data_concessao_adicional', 
                'bol_g_pm_adicional',
                'data_publicacao_adicional'
            )
        }),
        ('Metadados', {
            'classes': ('collapse',),
            'fields': (
                'user_created', 
                'created_at', 
                'user_updated', 
                'updated_at',
                'usuario_conclusao',
                'data_conclusao'
            )
        }),
    )
    inlines = [HistoricoCadastroInline]
    date_hierarchy = 'proximo_adicional'
    list_per_page = 20
    list_select_related = ('cadastro',)  # Removido detalhes problemático
    actions = ['marcar_como_concluido']

    def re_militar(self, obj):
        # CORREÇÃO: Usando campo 'nome' que existe em vez de 'nome_guerra'
        return f"{obj.cadastro.re} - {obj.cadastro.nome}"
    re_militar.short_description = 'Militar'
    re_militar.admin_order_field = 'cadastro__re'

    def posto_graduacao(self, obj):
        # Acesso seguro ao posto/graduação
        try:
            # CORREÇÃO: Acessando diretamente o campo de posto/graduação
            # Supondo que seja um campo CharField no modelo Cadastro
            return obj.cadastro.posto_graduacao
        except AttributeError:
            return "N/A"
    posto_graduacao.short_description = 'Posto/Grad'
    
    def status_adicional_badge(self, obj):
        cores = {
            'aguardando_requisitos': 'blue',
            'faz_jus': 'green',
            'lancado_sipa': 'orange',
            'publicado': 'purple',
            'concluido': 'gray',
            'encerrado': 'black'
        }
        cor = cores.get(obj.status_adicional, 'gray')
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 8px; border-radius: 4px;">{}</span>',
            cor,
            obj.get_status_adicional_display()
        )
    status_adicional_badge.short_description = 'Status'
    status_adicional_badge.admin_order_field = 'status_adicional'

    def dias_faltantes(self, obj):
        if obj.proximo_adicional:
            hoje = timezone.now().date()
            faltantes = (obj.proximo_adicional - hoje).days
            if faltantes > 0:
                return f"{faltantes} dias"
            return format_html('<span style="color: red; font-weight: bold;">VENCIDO</span>')
        return '-'
    dias_faltantes.short_description = 'Dias Faltantes'

    def acoes(self, obj):
        return format_html(
            '<a href="{}" class="button">Editar</a>&nbsp;'
            '<a href="{}" class="button" style="background-color: #417690">Histórico</a>',
            reverse('admin:adicional_cadastro_adicional_change', args=[obj.id]),
            reverse('admin:adicional_historicocadastro_changelist') + f'?cadastro_adicional__id__exact={obj.id}'
        )
    acoes.short_description = 'Ações'
    acoes.allow_tags = True

    def link_cadastro(self, obj):
        url = reverse('admin:efetivo_cadastro_change', args=[obj.cadastro.id])
        return mark_safe(f'<a href="{url}">{obj.cadastro}</a>')
    link_cadastro.short_description = 'Cadastro Militar'

    def marcar_como_concluido(self, request, queryset):
        atualizados = 0
        for obj in queryset:
            if obj.status_adicional != 'concluido':
                obj.status_adicional = 'concluido'
                obj.situacao_adicional = 'Concluído'
                obj.save()
                atualizados += 1
        self.message_user(
            request, 
            f"{atualizados} adicionais marcados como concluídos com sucesso!",
            messages.SUCCESS
        )
    marcar_como_concluido.short_description = "Marcar como concluído"

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user_created = request.user
        obj.user_updated = request.user
        super().save_model(request, obj, form, change)

@admin.register(HistoricoCadastro)
class HistoricoCadastroAdmin(admin.ModelAdmin):
    list_display = (
        'cadastro_adicional_link', 
        'data_alteracao', 
        'usuario_alteracao',
        'situacao_adicional',
        'status_adicional'
    )
    list_filter = ('status_adicional', 'situacao_adicional')
    search_fields = (
        'cadastro_adicional__cadastro__re', 
        'cadastro_adicional__cadastro__nome',
        'usuario_alteracao__username'
    )
    date_hierarchy = 'data_alteracao'
    list_select_related = ('cadastro_adicional', 'usuario_alteracao')  # Campos válidos
    readonly_fields = [f.name for f in HistoricoCadastro._meta.fields]

    def cadastro_adicional_link(self, obj):
        url = reverse('admin:adicional_cadastro_adicional_change', args=[obj.cadastro_adicional.id])
        return mark_safe(f'<a href="{url}">{obj.cadastro_adicional}</a>')
    cadastro_adicional_link.short_description = 'Adicional'
    cadastro_adicional_link.admin_order_field = 'cadastro_adicional__id'

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.method == 'GET'

    def has_delete_permission(self, request, obj=None):
        return False