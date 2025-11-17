from django.contrib import admin
from .models import Cadastro_bm, Imagem_bm


@admin.register(Cadastro_bm)
class CadastroBmAdmin(admin.ModelAdmin):
    list_display = [
        "nome",
        "nome_de_guerra",
        "situacao",
        "sgb",
        "posto_secao",
        "cpf",
        "esb",
        "ovb",
    ]
    list_filter = ["situacao", "sgb", "posto_secao", "esb", "ovb", "genero"]
    search_fields = ["nome", "nome_de_guerra", "cpf", "rg"]
    readonly_fields = ["create_at", "data_alteracao"]
    fieldsets = [
        (
            "Informações Pessoais",
            {
                "fields": [
                    "nome",
                    "nome_de_guerra",
                    "genero",
                    "cpf",
                    "rg",
                    "nasc",
                    "email",
                    "telefone",
                ]
            },
        ),
        (
            "Situação Militar",
            {
                "fields": [
                    "situacao",
                    "sgb",
                    "posto_secao",
                    "funcao",
                    "admissao",
                    "apresentacao_na_unidade",
                    "saida_da_unidade",
                ]
            },
        ),
        ("Documentos e Veículos", {"fields": ["cnh", "cat_cnh", "esb", "ovb"]}),
        (
            "Auditoria",
            {
                "fields": ["user", "usuario_alteracao", "create_at", "data_alteracao"],
                "classes": ["collapse"],
            },
        ),
    ]

    def save_model(self, request, obj, form, change):
        if not obj.user_id:
            obj.user = request.user
        if change:
            obj.usuario_alteracao = request.user
        super().save_model(request, obj, form, change)


@admin.register(Imagem_bm)
class ImagemBmAdmin(admin.ModelAdmin):
    list_display = ["cadastro", "create_at", "user"]
    list_filter = ["create_at", "user"]
    search_fields = ["cadastro__nome", "cadastro__nome_de_guerra"]
    readonly_fields = ["create_at"]

    def save_model(self, request, obj, form, change):
        if not obj.user_id:
            obj.user = request.user
        super().save_model(request, obj, form, change)
