from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    path('abrir-chamado/', views.abrir_chamado, name='abrir_chamado'),
    path('chamado-sucesso/<str:protocolo>/', views.chamado_sucesso, name='chamado_sucesso'),
    path('meus-chamados/', views.meus_chamados, name='meus_chamados'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('chamado/<int:chamado_id>/', views.chamado_detail, name='chamado_detail'),
    path('buscar-dados-cpf/', views.buscar_dados_cpf, name='buscar_dados_cpf'),  # Nova URL
]