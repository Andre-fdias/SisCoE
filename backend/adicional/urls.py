from django.urls import path
from . import views

app_name = 'adicional'

urlpatterns = [
    path('cadastrar/', views.cadastrar_lp, name='cadastrar_lp'),
    path('listar/', views.listar_lp, name='listar_lp'),
    
    # URLs para Adicional
    path('ver-adicional/<int:id>/', views.ver_adicional, name='ver_adicional'),
    path('editar-adicional/<int:id>/', views.editar_adicional, name='editar_adicional'),
    path('excluir-adicional/<int:id>/', views.excluir_adicional, name='excluir_adicional'),
    path('historico-adicional/<int:id>/', views.historico_adicional, name='historico_adicional'),
    path('concluir-adicional/<int:id>/', views.concluir_adicional, name='concluir_adicional'),
    path('editar-dias-desconto/<int:pk>/', views.editar_dias_desconto, name='editar_dias_desconto'),
    path('editar-concessao/<int:pk>/', views.editar_concessao, name='editar_concessao'),
    path('confirmar-6parte/<int:pk>/', views.confirmar_6parte, name='confirmar_6parte'),
    path('confirmar-sipa/<int:pk>/', views.confirmar_sipa, name='confirmar_sipa'),
    path('carregar-dados-sipa/<int:pk>/', views.carregar_dados_sipa, name='carregar_dados_sipa'),
    path('concluir-processo-ats/<int:pk>/', views.concluir_processo_ats, name='concluir_processo_ats'),
    path('novo-adicional/', views.novo_adicional, name='novo_adicional'),

    # URLs para LP
    path('ver-lp/<int:id>/', views.ver_lp, name='ver_lp'),
    path('editar-lp/<int:id>/', views.editar_lp, name='editar_lp'),
    path('excluir-lp/<int:id>/', views.excluir_lp, name='excluir_lp'),
    path('historico-lp/<int:id>/', views.historico_lp, name='historico_lp'),
    path('concluir-lp/<int:id>/', views.concluir_lp, name='concluir_lp'),
    
    path('buscar-militar/', views.buscar_militar_adicional, name='buscar_militar'),
]