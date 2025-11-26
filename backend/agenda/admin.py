from django.contrib import admin
from .models import Lembrete, Tarefa


@admin.register(Lembrete)
class LembreteAdmin(admin.ModelAdmin):
    list_display = ("titulo", "user", "data", "cor")
    search_fields = ("titulo", "descricao", "user__username")
    list_filter = ("data",)
    raw_id_fields = ("user",)
    list_select_related = ("user",)


@admin.register(Tarefa)
class TarefaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "user", "data_inicio", "data_fim", "cor")
    search_fields = ("titulo", "descricao", "user__username")
    list_filter = ("data_inicio", "data_fim")
    raw_id_fields = ("user",)
    list_select_related = ("user",)
