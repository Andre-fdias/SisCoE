from django.urls import path
from . import views

app_name = 'faisca'

urlpatterns = [
    # Faisca AI (Chatbot Geral)
    path('ai/chat', views.faisca_ai_chat, name='faisca_ai_chat'),
    path('ai/chat/', views.faisca_ai_chat),  # Versão com barra
    path('ai/history', views.faisca_ai_history, name='faisca_ai_history'),
    path('ai/reset', views.reset_faisca_ai_chat, name='reset_faisca_ai_chat'),
    
    # Faisca Agent (Dados do Sistema)
    path('agent/chat', views.faisca_agent_chat, name='faisca_agent_chat'),
    path('agent/chat/', views.faisca_agent_chat),  # Versão com barra
    path('agent/history', views.faisca_agent_history, name='faisca_agent_history'),
    path('agent/reset', views.reset_faisca_agent_chat, name='reset_faisca_agent_chat'),
]