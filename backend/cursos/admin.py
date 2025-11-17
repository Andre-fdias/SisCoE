# backend/cursos/admin.py

from django.contrib import admin
from .models import Medalha, Curso  # Certifique-se de importar suas models


@admin.register(Medalha)
class MedalhaAdmin(admin.ModelAdmin):
    list_display = ("id", "cadastro", "honraria", "bol_g_pm_lp", "data_publicacao_lp")
    list_filter = ("honraria", "data_publicacao_lp")
    search_fields = ("cadastro__nome", "honraria", "bol_g_pm_lp")
    raw_id_fields = ("cadastro",)


# Registre o modelo Curso no Admin
@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    # REMOVIDO 'outro_curso' do list_display
    list_display = ("cadastro", "curso", "data_publicacao", "bol_publicacao")

    # list_filter não precisa de 'outro_curso'
    list_filter = ("curso", "data_publicacao")

    # REMOVIDO 'outro_curso' do search_fields
    search_fields = ("cadastro__nome", "cadastro__re", "curso", "bol_publicacao")

    date_hierarchy = "data_publicacao"
    raw_id_fields = ("cadastro",)  # Útil para campos ForeignKey com muitos registros
