# backend/efetivo/urls.py
from django.urls import path
from . import views # Importa todas as views do seu aplicativo 'efetivo'

# Define o namespace para este aplicativo.
# Isso permite referenciar as URLs como 'efetivo:nome_da_url'
# Ex: {% url 'efetivo:listar_militar' %}
app_name = 'efetivo'

urlpatterns = [
    # --- Gerenciamento Básico de Militares ---
    path('cadastrar_militar/', views.cadastrar_militar, name="cadastrar_militar"),
    path('listar_militar/', views.listar_militar, name="listar_militar"),
    path('lista_militares/', views.ListaMilitaresView.as_view(), name='lista_militares'),
    path('ver_militar/<int:id>/', views.ver_militar, name="ver_militar"),
    path('excluir_militar/<int:id>/', views.excluir_militar, name='excluir_militar'),
    
    # --- Edição de Dados de Militares ---
    path('editar_posto_graduacao/<int:id>/', views.editar_posto_graduacao, name='editar_posto_graduacao'),
   path('editar_situacao_funcional/<int:id>/', views.editar_situacao_funcional, name='editar_situacao_funcional'),
    path('editar_dados_pessoais_contatos/<int:id>/', views.editar_dados_pessoais_contatos, name='editar_dados_pessoais_contatos'),
    path('editar_imagem/<int:id>/', views.editar_imagem, name='editar_imagem'),
   
    path('cadastrar_nova_situacao/<int:id>/', views.cadastrar_nova_situacao, name='cadastrar_nova_situacao'),

    # --- Históricos e Status ---
    path('historico_movimentacoes/<int:id>/', views.historico_movimentacoes, name='historico_movimentacoes'),
    path('check_rpt/<int:id>/', views.check_rpt, name='check_rpt'), # Rota para verificar RPT (Relação de Prioridade de Transferência?)
    path('detalhes_efetivo/<int:posto_id>/', views.detalhar_efetivo, name='detalhar_efetivo'),
    path('listar_outros_status/', views.listar_outros_status_militar, name='listar_outros_status'),
   
    # --- Categorias de Efetivo (Férias, Restrição, DS, DR, etc.) ---
    path('militar/<int:militar_id>/adicionar-categoria/',
         views.adicionar_categoria_efetivo, name='adicionar_categoria_efetivo'),
    path('militar/<int:militar_id>/historico-categorias/',
         views.historico_categorias, name='historico_categorias'),
    path('categoria/editar/<int:categoria_id>/', views.editar_categoria_modal, name='editar_categoria_modal'),
    path('categoria/salvar-edicao/<int:categoria_id>/', views.SalvarEdicaoCategoriaView.as_view(), name='salvar_edicao_categoria'),
    path('excluir-historico-categoria/<int:historico_id>/',
         views.excluir_historico_categoria,
         name='excluir_historico_categoria'),

    # --- NOVAS ROTAS: Busca de Militar e Geração de Etiqueta PDF ---
    # URL para a página HTML com o formulário de busca por RE.
    # Acessível via /efetivo/buscar_militar/
    path('buscar_militar/', views.pagina_buscar_militar, name='buscar_militar_page'),
    
    # URL para processar a busca e gerar o PDF da etiqueta.
    # Acessível via /efetivo/gerar_etiqueta_pdf/?re=SEU_RE
    path('gerar_etiqueta_pdf/', views.gerar_etiqueta_pdf, name='gerar_etiqueta_pdf'),
]