# backend/chat/urls.py
from django.urls import path, include
from rest_framework_nested import routers
from . import views

app_name = 'chat'

# Roteador principal para /api/chat/conversations/
router = routers.SimpleRouter()
router.register(r'conversations', views.ConversationViewSet, basename='conversation')

# Roteador aninhado para /conversations/{conversation_pk}/messages/
messages_router = routers.NestedSimpleRouter(router, r'conversations', lookup='conversation')
messages_router.register(r'messages', views.MessageViewSet, basename='conversation-messages')

# URLs adicionais
urlpatterns = [
    path("", include(router.urls)),
    path("", include(messages_router.urls)),
    
    # Presença
    path('presence/', views.UserPresenceView.as_view(), name='user-presence'),
    
    # Attachments
    path('attachments/', views.AttachmentViewSet.as_view({'post': 'create'}), name='attachment-create'),
    
    # View principal do chat
    path('', views.ChatView.as_view(), name='chat-main'),
]