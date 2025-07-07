# efetivo/admin.py
from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.urls import reverse
from django.db.models import Q
from django.utils import timezone
from .models import (
    Cadastro, DetalhesSituacao, Promocao, Imagem,
    HistoricoDetalhesSituacao, HistoricoPromocao,
    CatEfetivo, HistoricoCatEfetivo
)

# ======================
# FILTROS PERSONALIZADOS
# ======================
class StatusInatividadeFilter(admin.SimpleListFilter):
    title = 'Status de Inatividade'
    parameter_name = 'status_inatividade'

    def lookups(self, request, model_admin):
        return (
            ('inativo', 'Inativo'),
            ('6_meses', 'Falta menos de 6 meses'),
            ('1_ano', 'Falta menos de 1 ano'),
            ('mais_1_ano', 'Falta mais de 1 ano'),
        )

    def queryset(self, request, queryset):
        hoje = timezone.now().date()
        if self.value() == 'inativo':
            return queryset.filter(previsao_de_inatividade__lte=hoje)
        elif self.value() == '6_meses':
            seis_meses = hoje + timezone.timedelta(days=180)
            return queryset.filter(
                previsao_de_inatividade__gt=hoje,
                previsao_de_inatividade__lte=seis_meses
            )
        elif self.value() == '1_ano':
            um_ano = hoje + timezone.timedelta(days=365)
            return queryset.filter(
                previsao_de_inatividade__gt=hoje,
                previsao_de_inatividade__lte=um_ano
            )
        elif self.value() == 'mais_1_ano':
            return queryset.filter(previsao_de_inatividade__gt=hoje + timezone.timedelta(days=365))

# ======================
# INLINES
# ======================
class DetalhesSituacaoInline(admin.StackedInline):
    model = DetalhesSituacao
    extra = 0
    fields = ('situacao', 'cat_efetivo', 'sgb', 'posto_secao', 'esta_adido', 
              'funcao', 'op_adm', 'prontidao_badge', 'apresentacao_na_unidade', 'saida_da_unidade')
    readonly_fields = ('prontidao_badge',)

class PromocaoInline(admin.StackedInline):
    model = Promocao
    extra = 0
    fields = ('posto_grad', 'quadro', 'grupo', 'ultima_promocao', 'grad')
    readonly_fields = ('grad',)

class ImagemInline(admin.TabularInline):
    model = Imagem
    extra = 0
    fields = ('image_tag',)
    readonly_fields = ('image_tag',)
    
    def image_tag(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="50" height="50" style="border-radius: 50%;" />')
        return "Sem imagem"
    image_tag.short_description = 'Foto'

class CatEfetivoInline(admin.StackedInline):
    model = CatEfetivo
    extra = 0
    fields = ('tipo_badge', 'data_inicio', 'data_termino', 'status_badge', 'restricoes_selecionadas_badges')
    readonly_fields = ('tipo_badge', 'status_badge', 'restricoes_selecionadas_badges')

# ======================
# ADMINS PRINCIPAIS
# ======================
@admin.register(Cadastro)
class CadastroAdmin(admin.ModelAdmin):
    list_display = ('re_dig', 'nome_de_guerra', 'posto_grad', 'idade', 'tempo_admissao', 'inativa_status', 'acoes')
    list_filter = (StatusInatividadeFilter, 'genero')
    search_fields = ('re', 'nome', 'nome_de_guerra')
    inlines = [DetalhesSituacaoInline, PromocaoInline, ImagemInline, CatEfetivoInline]
    readonly_fields = ('inativa_status',)
    list_per_page = 25
    
    def re_dig(self, obj):
        return f"{obj.re}-{obj.dig}"
    re_dig.short_description = 'RE'
    re_dig.admin_order_field = 're'

    def posto_grad(self, obj):
        return obj.ultima_promocao.posto_grad if hasattr(obj, 'ultima_promocao') and obj.ultima_promocao else '-'
    posto_grad.short_description = 'Posto/Grad'

    def idade(self, obj):
        return obj.idade_detalhada
    idade.short_description = 'Idade'

    def tempo_admissao(self, obj):
        return obj.admissao_detalhada()
    tempo_admissao.short_description = 'Tempo de Admissão'

    def acoes(self, obj):
        url = reverse('admin:efetivo_cadastro_change', args=[obj.id])
        return format_html('<a class="button" href="{}">Editar</a>', url)
    acoes.short_description = 'Ações'

@admin.register(DetalhesSituacao)
class DetalhesSituacaoAdmin(admin.ModelAdmin):
    list_display = ('cadastro_re', 'cadastro_nome_guerra', 'situacao_badge', 'cat_efetivo_badge', 'prontidao_badge', 'apresentacao_na_unidade')
    search_fields = ('cadastro__re', 'cadastro__nome_de_guerra')
    list_filter = ('situacao', 'cat_efetivo', 'prontidao')
    list_per_page = 25

    def cadastro_re(self, obj):
        return obj.cadastro.re
    cadastro_re.short_description = 'RE'

    def cadastro_nome_guerra(self, obj):
        return obj.cadastro.nome_de_guerra
    cadastro_nome_guerra.short_description = 'Nome de Guerra'

    def situacao_badge(self, obj):
        return obj.status
    situacao_badge.short_description = 'Situação'
    situacao_badge.allow_tags = True

    def cat_efetivo_badge(self, obj):
        return obj.status_cat
    cat_efetivo_badge.short_description = 'Categoria'
    cat_efetivo_badge.allow_tags = True

@admin.register(Promocao)
class PromocaoAdmin(admin.ModelAdmin):
    list_display = ('cadastro_re', 'cadastro_nome_guerra', 'posto_grad_badge', 'ultima_promocao', 'tempo_na_patente')
    search_fields = ('cadastro__re', 'cadastro__nome_de_guerra', 'posto_grad')
    list_filter = ('posto_grad', 'quadro', 'grupo')
    list_per_page = 25

    def cadastro_re(self, obj):
        return obj.cadastro.re
    cadastro_re.short_description = 'RE'

    def cadastro_nome_guerra(self, obj):
        return obj.cadastro.nome_de_guerra
    cadastro_nome_guerra.short_description = 'Nome de Guerra'

    def posto_grad_badge(self, obj):
        return obj.grad
    posto_grad_badge.short_description = 'Posto/Grad'
    posto_grad_badge.allow_tags = True

    def tempo_na_patente(self, obj):
        return obj.ultima_promocao_detalhada
    tempo_na_patente.short_description = 'Tempo na Patente'

@admin.register(Imagem)
class ImagemAdmin(admin.ModelAdmin):
    list_display = ('cadastro_re', 'cadastro_nome_guerra', 'image_tag', 'create_at')
    search_fields = ('cadastro__re', 'cadastro__nome_de_guerra')
    list_per_page = 25

    def cadastro_re(self, obj):
        return obj.cadastro.re
    cadastro_re.short_description = 'RE'

    def cadastro_nome_guerra(self, obj):
        return obj.cadastro.nome_de_guerra
    cadastro_nome_guerra.short_description = 'Nome de Guerra'

    def image_tag(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="50" height="50" style="border-radius: 50%;" />')
        return "Sem imagem"
    image_tag.short_description = 'Foto'

# ======================
# ADMIN PARA CATEGORIAS DE EFETIVO
# ======================
class HistoricoCatEfetivoInline(admin.TabularInline):
    model = HistoricoCatEfetivo
    extra = 0
    readonly_fields = ('data_registro', 'usuario_alteracao', 'tipo_badge', 'status_info_badge')
    fields = ('data_registro', 'usuario_alteracao', 'tipo_badge', 'status_info_badge')
    can_delete = False
    
    def tipo_badge(self, obj):
        return obj.tipo_badge
    tipo_badge.short_description = 'Tipo'
    tipo_badge.allow_tags = True
    
    def status_info_badge(self, obj):
        return obj.status_info_badge
    status_info_badge.short_description = 'Status'
    status_info_badge.allow_tags = True

@admin.register(CatEfetivo)
class CatEfetivoAdmin(admin.ModelAdmin):
    inlines = [HistoricoCatEfetivoInline]
    list_display = ('cadastro_re', 'cadastro_nome_guerra', 'tipo_badge', 'data_inicio', 'data_termino', 'status_badge', 'restricoes_count')
    list_filter = ('tipo', 'ativo')
    search_fields = ('cadastro__re', 'cadastro__nome_de_guerra')
    list_per_page = 25
    readonly_fields = ('tipo_badge', 'status_badge', 'restricoes_selecionadas_badges', 'regras_restricoes_badges')
    
    fieldsets = (
        (None, {
            'fields': ('cadastro', 'tipo_badge', 'data_inicio', 'data_termino', 'status_badge', 'observacao')
        }),
        ('Campos Específicos', {
            'fields': ('boletim_concessao_lsv', 'data_boletim_lsv'),
            'classes': ('collapse',),
        }),
        ('Restrições', {
            'fields': ('restricoes_selecionadas_badges', 'regras_restricoes_badges'),
            'classes': ('collapse',),
        }),
    )
    
    def cadastro_re(self, obj):
        return obj.cadastro.re
    cadastro_re.short_description = 'RE'
    cadastro_re.admin_order_field = 'cadastro__re'

    def cadastro_nome_guerra(self, obj):
        return obj.cadastro.nome_de_guerra
    cadastro_nome_guerra.short_description = 'Nome de Guerra'
    cadastro_nome_guerra.admin_order_field = 'cadastro__nome_de_guerra'

    def restricoes_count(self, obj):
        if obj.tipo == 'RESTRICAO':
            count = sum(1 for field in obj._meta.get_fields() 
                       if field.name.startswith('restricao_') and getattr(obj, field.name))
            return f"{count} restrições"
        return "-"
    restricoes_count.short_description = 'Restrições'

@admin.register(HistoricoCatEfetivo)
class HistoricoCatEfetivoAdmin(admin.ModelAdmin):
    list_display = ('cat_efetivo_link', 'data_registro', 'usuario_alteracao', 'tipo_badge', 'status_info_badge')
    list_filter = ('tipo', 'data_registro')
    search_fields = ('cat_efetivo__cadastro__re', 'cat_efetivo__cadastro__nome_de_guerra')
    list_per_page = 25
    readonly_fields = ('tipo_badge', 'status_info_badge', 'restricoes_selecionadas_siglas')
    
    def cat_efetivo_link(self, obj):
        url = reverse('admin:efetivo_catefetivo_change', args=[obj.cat_efetivo.id])
        return mark_safe(f'<a href="{url}">{obj.cat_efetivo}</a>')
    cat_efetivo_link.short_description = 'Categoria de Efetivo'
    cat_efetivo_link.admin_order_field = 'cat_efetivo__id'
    
    def tipo_badge(self, obj):
        return obj.tipo_badge
    tipo_badge.short_description = 'Tipo'
    tipo_badge.allow_tags = True
    
    def status_info_badge(self, obj):
        return obj.status_info_badge
    status_info_badge.short_description = 'Status'
    status_info_badge.allow_tags = True

# ======================
# ADMIN PARA HISTÓRICOS
# ======================
@admin.register(HistoricoDetalhesSituacao)
class HistoricoDetalhesSituacaoAdmin(admin.ModelAdmin):
    list_display = ('cadastro_re', 'cadastro_nome_guerra', 'situacao', 'data_alteracao')
    search_fields = ('cadastro__re', 'cadastro__nome_de_guerra')
    list_filter = ('situacao', 'data_alteracao')
    list_per_page = 25
    date_hierarchy = 'data_alteracao'

    def cadastro_re(self, obj):
        return obj.cadastro.re
    cadastro_re.short_description = 'RE'

    def cadastro_nome_guerra(self, obj):
        return obj.cadastro.nome_de_guerra
    cadastro_nome_guerra.short_description = 'Nome de Guerra'

@admin.register(HistoricoPromocao)
class HistoricoPromocaoAdmin(admin.ModelAdmin):
    list_display = ('cadastro_re', 'cadastro_nome_guerra', 'posto_grad', 'ultima_promocao', 'data_alteracao')
    search_fields = ('cadastro__re', 'cadastro__nome_de_guerra', 'posto_grad')
    list_filter = ('posto_grad', 'data_alteracao')
    list_per_page = 25
    date_hierarchy = 'data_alteracao'

    def cadastro_re(self, obj):
        return obj.cadastro.re
    cadastro_re.short_description = 'RE'

    def cadastro_nome_guerra(self, obj):
        return obj.cadastro.nome_de_guerra
    cadastro_nome_guerra.short_description = 'Nome de Guerra'