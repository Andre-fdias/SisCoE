from django.urls import path
from . import views
from .api_views import buscar_dados_cpf  # Importando do novo arquivo

app_name = 'tickets'

urlpatterns = [
    path('abrir-chamado/', views.abrir_chamado, name='abrir_chamado'),
    path('chamado-sucesso/<str:protocolo>/', views.chamado_sucesso, name='chamado_sucesso'),
    path('meus-chamados/', views.meus_chamados, name='meus_chamados'),  # ✅ Usando a view original
    path('meus-chamados/api/', views.meus_chamados_api, name='meus_chamados_api'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('chamado/<int:chamado_id>/', views.chamado_detail, name='chamado_detail'),
    path('buscar-dados-cpf/', buscar_dados_cpf, name='buscar_dados_cpf'),
]