from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    path('abrir-chamado/', views.abrir_chamado, name='abrir_chamado'),
    path('chamado-sucesso/<str:protocolo>/', views.chamado_sucesso, name='chamado_sucesso'),
    path('meus-chamados/', views.meus_chamados_lista, name='meus_chamados'),  # ✅ Nova view
    path('meus-chamados/api/', views.meus_chamados_api, name='meus_chamados_api'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('chamado/<int:chamado_id>/', views.chamado_detail, name='chamado_detail'),  # ✅ Corrigida
    path('buscar-dados-cpf/', views.buscar_dados_cpf, name='buscar_dados_cpf'),
]