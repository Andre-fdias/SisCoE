# backend/lp/urls.py
from django.urls import path
from . import views

app_name = 'lp' 

urlpatterns = [
    path('cadastrar/', views.cadastrar_lp, name='cadastrar_lp'),
    
    path('<int:pk>/', views.ver_lp, name='ver_lp'),
    # CORREÇÃO CRÍTICA AQUI: Removido o prefixo 'lp/' duplicado
    path('editar_concessao_lp/<int:pk>/', views.editar_concessao_lp, name='editar_concessao_lp'),
    
    # ADICIONE ESTA LINHA PARA A URL DE EDIÇÃO COMPLETA
    path('editar/<int:pk>/', views.editar_lp, name='editar_lp'), # <-- NOVA LINHA

    path('<int:pk>/concluir/', views.concluir_lp, name='concluir_lp'),
    path('<int:pk>/editar-dias-desconto/', views.editar_dias_desconto_lp, name='editar_dias_desconto_lp'),
    path('<int:pk>/confirmar-sipa/', views.confirmar_sipa_lp, name='confirmar_sipa_lp'),
    path('<int:pk>/excluir/', views.excluir_lp, name='excluir_lp'),
    path('buscar-militar/', views.buscar_militar_lp, name='buscar_militar_lp'),  # NOVA URL
    path('lista/', views.listar_lp, name='listar_lp'), 

    path('<int:pk>/carregar-dados-sipa/', views.carregar_dados_sipa_lp, name='carregar_dados_sipa_lp'),



   path('fruicao/<int:pk>/', views.detalhar_fruicao, name='detalhar_fruicao'),




]