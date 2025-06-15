# adicional/urls.py
from django.urls import path
from . import views

app_name = 'adicional'

urlpatterns = [
    # URLs para cadastro e listagem
    path('cadastrar/', views.cadastrar_adicional, name='cadastrar_adicional'),
    path('listar/', views.listar_adicional, name='listar_adicional'),
    path('novo-adicional/', views.novo_adicional, name='novo_adicional'),
    
    # URLs para operações com Adicional
    path('ver-adicional/<int:id>/', views.ver_adicional, name='ver_adicional'),
    path('editar-geral/<int:id>/', views.editar_cadastro_adicional, name='editar_geral'),
    path('excluir-adicional/<int:id>/', views.excluir_adicional, name='excluir_adicional'),
    
    # URLs para histórico e ações específicas
    path('historico-adicional/<int:id>/', views.historico_adicional, name='historico_adicional'),
    path('concluir-adicional/<int:id>/', views.concluir_adicional, name='concluir_adicional'),
    
    # URLs para operações específicas
    path('editar-dias-desconto/<int:pk>/', views.editar_dias_desconto, name='editar_dias_desconto'),
    path('editar-concessao/<int:pk>/', views.editar_concessao, name='editar_concessao'),
    path('confirmar-6parte/<int:pk>/', views.confirmar_6parte, name='confirmar_6parte'),
    path('confirmar-sipa/<int:pk>/', views.confirmar_sipa, name='confirmar_sipa'),
    path('carregar-dados-sipa/<int:pk>/', views.carregar_dados_sipa, name='carregar_dados_sipa'),
    
    # URL para busca de militar
    path('buscar-militar/', views.buscar_militar_adicional, name='buscar_militar'),
]