# backend/lp/admin.py
from django.contrib import admin
from .models import LP, HistoricoLP, LP_fruicao # Importe seus modelos LP e HistoricoLP
from backend.efetivo.models import Cadastro # Importe Cadastro se for usado aqui para exibir campos relacionados

@admin.register(LP)
class LPAdmin(admin.ModelAdmin):
    list_display = (
        'cadastro', 'numero_lp', 'data_ultimo_lp', 
        'proximo_lp', 'situacao_lp', 'status_lp', 'data_concessao_lp', 'lancamento_sipa'
    )
    list_filter = (
        'situacao_lp', 'status_lp', 'lancamento_sipa', 
        'mes_proximo_lp', 'ano_proximo_lp',
        ('data_ultimo_lp', admin.DateFieldListFilter), # Filtro por data
    )
    search_fields = (
        'cadastro__nome', 'cadastro__re', 'cadastro__nome_de_guerra', # Use 'nome_de_guerra'
        'observacoes', 'bol_g_pm_lp'
    )
    # CORREÇÃO: Usando 'data_cadastro' e 'data_atualizacao' que são os campos reais no modelo LP
    readonly_fields = (
        'data_cadastro', 'data_atualizacao', 'user_created', 'user_updated', 
        'usuario_conclusao', 'proximo_lp', 'mes_proximo_lp', 'ano_proximo_lp'
    ) 
    
    # CORREÇÃO: Usando 'data_cadastro' para a hierarquia de datas
    date_hierarchy = 'data_cadastro' 
    
    fieldsets = (
        (None, {
            'fields': ('cadastro', ('numero_lp',  'data_ultimo_lp')),
        }),
        ('Datas e Situação', {
            'fields': ('dias_desconto_lp', 'situacao_lp', 'status_lp'),
        }),
        ('Concessão e Publicação', {
            'fields': ('data_concessao_lp', 'bol_g_pm_lp', 'data_publicacao_lp', 'lancamento_sipa'),
        }),
        ('Informações de Sistema', {
            'fields': ('user_created', 'data_cadastro', 'user_updated', 'data_atualizacao', 'usuario_conclusao',
                       ('numero_prox_lp', 'proximo_lp'), 'mes_proximo_lp', 'ano_proximo_lp'),
            'classes': ('collapse',), # Oculta esta seção por padrão
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',),
        }),
    )

@admin.register(HistoricoLP)
class HistoricoLPAdmin(admin.ModelAdmin):
    list_display = (
        'lp', 'usuario_alteracao', 'data_alteracao', 'situacao_lp', 'status_lp'
    )
    list_filter = ('situacao_lp', 'status_lp', 'data_alteracao')
    search_fields = (
        'lp__cadastro__nome', 'lp__cadastro__re', 'lp__cadastro__nome_de_guerra', # Use 'nome_de_guerra'
        'observacoes_historico'
    )
    readonly_fields = ('lp', 'usuario_alteracao', 'data_alteracao', 'situacao_lp', 'status_lp', 
                       'numero_lp', 'data_ultimo_lp',  'numero_prox_lp', 
                       'proximo_lp', 'mes_proximo_lp', 'ano_proximo_lp', 'dias_desconto_lp', 
                       'bol_g_pm_lp', 'data_publicacao_lp', 'data_concessao_lp', 'lancamento_sipa', 
                       'observacoes_historico')
    date_hierarchy = 'data_alteracao'



@admin.register(LP_fruicao)
class LPFruicaoAdmin(admin.ModelAdmin):
    list_display = (
        'cadastro', 'numero_lp', 'data_concessao_lp', 
        'tipo_choice', 'tipo_periodo_afastamento', 'data_publicacao_lp'
    )
    list_filter = (
        'tipo_choice', 'tipo_periodo_afastamento',
        ('data_concessao_lp', admin.DateFieldListFilter),
        ('data_publicacao_lp', admin.DateFieldListFilter),
    )
    search_fields = (
        'cadastro__nome', 'cadastro__re', 'cadastro__nome_de_guerra',
        'bol_g_pm_lp', 'lp_concluida__numero_lp'
    )
    readonly_fields = (
        'data_cadastro', 'data_atualizacao', 'user_created', 'user_updated',
        'cadastro', 'lp_concluida'
    )
    date_hierarchy = 'data_cadastro'
    
    fieldsets = (
        (None, {
            'fields': (
                'cadastro', 'lp_concluida', 'numero_lp',
                ('data_concessao_lp', 'data_publicacao_lp'),
            )
        }),
        ('Fruição da LP', {
            'fields': (
                'tipo_choice', 'tipo_periodo_afastamento', 'bol_g_pm_lp'
            ),
        }),
        ('Auditoria', {
            'fields': (
                'user_created', 'data_cadastro', 
                'user_updated', 'data_atualizacao'
            ),
            'classes': ('collapse',),
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Otimiza as consultas relacionadas
        return qs.select_related('cadastro', 'lp_concluida')
    
    def numero_lp(self, obj):
        return obj.lp_concluida.numero_lp
    numero_lp.short_description = 'Nº LP'
    numero_lp.admin_order_field = 'lp_concluida__numero_lp'