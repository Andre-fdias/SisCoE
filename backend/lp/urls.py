# backend/lp/urls.py
from django.urls import path
from . import views

app_name = 'lp' 

urlpatterns = [
    path('cadastrar/', views.cadastrar_lp, name='cadastrar_lp'),
    
    path('<int:pk>/', views.ver_lp, name='ver_lp'),
    path('<int:pk>/editar-concessao/', views.editar_concessao_lp, name='editar_concessao_lp'),
    path('<int:pk>/concluir/', views.concluir_lp, name='concluir_lp'),
    path('<int:pk>/editar-dias-desconto/', views.editar_dias_desconto_lp, name='editar_dias_desconto_lp'),
    path('<int:pk>/confirmar-sipa/', views.confirmar_sipa_lp, name='confirmar_sipa_lp'),
    path('<int:pk>/excluir/', views.excluir_lp, name='excluir_lp'),
    path('buscar-militar/', views.buscar_militar_lp, name='buscar_militar_lp'),  # NOVA URL
    # URL para a lista geral de LPs (nova view renomeada)
    # Este path pode ser ajustado conforme a sua necessidade, ex: 'lista/'
    path('lista/', views.listar_lp, name='listar_lp'), 
]
