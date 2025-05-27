# bookstore/urls.py
from django.urls import path
from . import views

app_name = 'efetivo'

urlpatterns = [
    path('cadastrar_militar/', views.cadastrar_militar, name="cadastrar_militar"),
    path('listar_militar/', views.listar_militar, name="listar_militar"),
    path('lista_militares/', views.ListaMilitaresView.as_view(), name='lista_militares'),  # Nova rota
    path('ver_militar/<int:id>/', views.ver_militar, name="ver_militar"),
    path('editar_posto_graduacao/<int:id>/', views.editar_posto_graduacao, name='editar_posto_graduacao'),
    path('editar_situacao_funcional/<int:id>/', views.editar_situacao_funcional, name='editar_situacao_funcional'),
    path('editar_dados_pessoais_contatos/<int:id>/', views.editar_dados_pessoais_contatos, name='editar_dados_pessoais_contatos'),
    path('excluir_militar/<int:id>/', views.excluir_militar, name='excluir_militar'),
    path('editar_imagem/<int:id>/', views.editar_imagem, name='editar_imagem'),
    path('historico_movimentacoes/<int:id>/', views.historico_movimentacoes, name='historico_movimentacoes'),
    path('editar_situacao_atual/<int:id>/', views.editar_situacao_atual, name='editar_situacao_atual'),
    path('cadastrar_nova_situacao/<int:id>/', views.cadastrar_nova_situacao, name='cadastrar_nova_situacao'),
    path('check_rpt/<int:id>/', views.check_rpt, name='check_rpt'),
    path('detalhes_efetivo/<int:posto_id>/', views.detalhar_efetivo, name='detalhar_efetivo'),
    
    # Categorias de Efetivo
    path('militar/<int:militar_id>/adicionar-categoria/', 
         views.adicionar_categoria_efetivo, name='adicionar_categoria_efetivo'),
    path('militar/<int:militar_id>/historico-categorias/', 
         views.historico_categorias, name='historico_categorias'),
    path('categoria/editar/<int:categoria_id>/', 
         views.editar_categoria_efetivo, name='editar_categoria_efetivo'),
    path('categoria/excluir/<int:categoria_id>/', 
         views.excluir_categoria_efetivo, name='excluir_categoria_efetivo'),
    path('excluir-historico-categoria/<int:historico_id>/',
         views.excluir_historico_categoria,
         name='excluir_historico_categoria'),
]