from django.contrib import admin
from .models import Cadastro, DetalhesSituacao, Promocao, HistoricoDetalhesSituacao,HistoricoPromocao, Imagem


# registra os modelos de dados(models.py) no admin/django .
admin.site.register(Cadastro)
admin.site.register(DetalhesSituacao)
admin.site.register(Promocao)
admin.site.register(HistoricoDetalhesSituacao)
admin.site.register(HistoricoPromocao)
admin.site.register(Imagem)

from django.contrib import admin
from .models import CatEfetivo, HistoricoCatEfetivo

class HistoricoCatEfetivoInline(admin.TabularInline):
    model = HistoricoCatEfetivo
    extra = 0
    readonly_fields = ('data_registro', 'usuario_alteracao')
    can_delete = False

@admin.register(CatEfetivo)
class CatEfetivoAdmin(admin.ModelAdmin):
    inlines = [HistoricoCatEfetivoInline]
    list_display = ('cadastro', 'tipo_badge', 'data_inicio', 'data_termino', 'status_badge')
    # ... outros campos do admin

@admin.register(HistoricoCatEfetivo)
class HistoricoCatEfetivoAdmin(admin.ModelAdmin):
    list_display = ('cat_efetivo', 'data_registro', 'usuario_alteracao', 'tipo_badge')
    readonly_fields = ('data_registro',)
    list_filter = ('data_registro', 'tipo')
    search_fields = ('cat_efetivo__cadastro__nome_de_guerra',)
