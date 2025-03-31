from django.urls import path
from . import views

app_name = 'faisca'

urlpatterns = [
    path('chat', views.chatbot, name='chatbot'),
    path('history', views.chat_history, name='chat_history'),
    path('reset_chat', views.reset_chat, name='reset_chat'),  # Adicione esta linha
    path('system_agent', views.system_agent, name='system_agent'),
    path('faisca_agent/chat', views.faisca_agent_chat, name='faisca_agent_chat'),
    path('faisca_agent/reset', views.reset_faisca_agent_chat, name='reset_faisca_agent_chat'),
    ]