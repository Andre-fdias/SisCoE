# backend/lp/urls.py
from django.urls import path
from . import views

app_name = "lp"

urlpatterns = [
    # URLs existentes que você já tem
    path("cadastrar/", views.cadastrar_lp, name="cadastrar_lp"),
    path("<int:pk>/", views.ver_lp, name="ver_lp"),
    path(
        "editar_concessao_lp/<int:pk>/",
        views.editar_concessao_lp,
        name="editar_concessao_lp",
    ),
    path("editar/<int:pk>/", views.editar_lp, name="editar_lp"),
    path("<int:pk>/concluir/", views.concluir_lp, name="concluir_lp"),
    path(
        "<int:pk>/editar-dias-desconto/",
        views.editar_dias_desconto_lp,
        name="editar_dias_desconto_lp",
    ),
    path("<int:pk>/confirmar-sipa/", views.confirmar_sipa_lp, name="confirmar_sipa_lp"),
    path("<int:pk>/excluir/", views.excluir_lp, name="excluir_lp"),
    path("buscar-militar/", views.buscar_militar_lp, name="buscar_militar_lp"),
    path("lista/", views.listar_lp, name="listar_lp"),
    path(
        "<int:pk>/carregar-dados-sipa/",
        views.carregar_dados_sipa_lp,
        name="carregar_dados_sipa_lp",
    ),
    # Novas URLs para fruição
    path("fruicao/<int:pk>/", views.detalhar_fruicao, name="detalhar_fruicao"),
    path("fruicao/<int:pk>/editar/", views.editar_fruicao, name="editar_fruicao"),
    path(
        "fruicao/<int:pk>/adicionar-afastamento/",
        views.adicionar_afastamento,
        name="adicionar_afastamento",
    ),
    path(
        "fruicao/get_afastamento_data/<int:afastamento_id>/",
        views.get_afastamento_data,
        name="get_afastamento_data",
    ),
    path(
        "fruicao/remover_afastamento/<int:pk>/<int:afastamento_id>/",
        views.remover_afastamento,
        name="remover_afastamento",
    ),
]
