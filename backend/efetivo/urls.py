# backend/efetivo/urls.py
from django.urls import path
from . import views

app_name = 'efetivo'

urlpatterns = [
    # --- Gerenciamento Básico de Militares ---
    path('cadastrar_militar/', views.cadastrar_militar, name="cadastrar_militar"),
    path('listar_militar/', views.listar_militar, name="listar_militar"),
    path('lista_militares/', views.ListaMilitaresView.as_view(), name='lista_militares'),
    path('ver_militar/<int:id>/', views.ver_militar, name="ver_militar"),
    path('excluir_militar/<int:id>/', views.excluir_militar, name='excluir_militar'),
     
     
      # Rota para o perfil público de um militar específico (com ID)
    path('publico/<int:id>/', views.visualizar_militar_publico, name='visualizar_militar_publico'),
    path('editar_imagem_user/<int:id>/', views.editar_imagem_user, name='editar_imagem_user'),
    
    # --- Edição de Dados Específicos de Militares ---
    path('editar_posto_graduacao/<int:id>/', views.editar_posto_graduacao, name='editar_posto_graduacao'),
    path('editar_dados_pessoais_contatos/<int:id>/', views.editar_dados_pessoais_contatos, name='editar_dados_pessoais_contatos'),
    path('editar_imagem/<int:id>/', views.editar_imagem, name='editar_imagem'),
     # urls.py
    path('editar_averbacao_militar/<int:id>/', views.editar_averbacao_militar, name='editar_averbacao_militar'),
    path('editar_averbacao_inss/<int:id>/', views.editar_averbacao_inss, name='editar_averbacao_inss'),
    path('editar_telefone/<int:id>/', views.editar_telefone, name='editar_telefone'),


    # --- Históricos e Outros Status ---
    path('historico_movimentacoes/<int:id>/', views.historico_movimentacoes, name='historico_movimentacoes'),
    path('check_rpt/<int:id>/', views.check_rpt, name='check_rpt'), # Mantido conforme o original
    path('listar_outros_status/', views.listar_outros_status_militar, name='listar_outros_status'),
   
    # --- Gerenciamento de Categorias de Efetivo (Férias, Restrição, DS, DR, etc.) ---
    path('militar/<int:militar_id>/adicionar-categoria/',
         views.adicionar_categoria_efetivo, name='adicionar_categoria_efetivo'),
    
    # URL para visualizar o histórico de categorias de efetivo de um militar.
    path('militar/<int:militar_id>/historico-categorias/',
         views.historico_categorias, name='historico_categorias'),
    
    # URL para excluir um registro específico do histórico de categorias de efetivo.
    path('excluir-historico-categoria/<int:historico_id>/',
         views.excluir_historico_categoria,
         name='excluir_historico_categoria'),

    # URL para excluir uma categoria de efetivo completa (e seu histórico).
    path('excluir-categoria-efetivo/<int:categoria_id>/',
         views.excluir_categoria_efetivo,
         name='excluir_categoria_efetivo'),

    # --- Novas URLs para Exclusão de Histórico de Movimentações ---
    path('excluir_historico_promocao/<int:promocao_id>/',
         views.excluir_historico_promocao, name='excluir_historico_promocao'),
    path('excluir_historico_detalhe_situacao/<int:detalhe_id>/',
         views.excluir_historico_detalhe_situacao, name='excluir_historico_detalhe_situacao'),

    # --- Funcionalidades de Etiqueta PDF ---
    path('buscar_militar/', views.pagina_buscar_militar, name='buscar_militar_page'),
    path('gerar_etiqueta_pdf/', views.gerar_etiqueta_pdf, name='gerar_etiqueta_pdf'),
    path('gerar_cadastros_fake/', views.gerar_cadastros_fake, name='gerar_cadastros_fake'),
    # URL para editar situação funcional.
    path('editar_situacao_funcional/<int:id>/', views.editar_situacao_funcional, name='editar_situacao_funcional'),
    path('nova_situacao_funcional/<int:id>/', views.nova_situacao_funcional, name='nova_situacao_funcional'),
]