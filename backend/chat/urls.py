from django.urls import path, include
from rest_framework_nested import routers
from . import views

app_name = 'chat'

# Roteador para /conversations/
router = routers.SimpleRouter()
router.register(r'conversations', views.ConversationViewSet, basename='conversation')

# Roteador aninhado para /conversations/{conversation_pk}/messages/
messages_router = routers.NestedSimpleRouter(router, r'conversations', lookup='conversation')
messages_router.register(r'messages', views.MessageViewSet, basename='conversation-messages')

# Este arquivo deve conter apenas as URLs da API para o app de chat.
# A URL da view principal (ChatView) deve ser gerenciada no urls.py raiz do projeto.
urlpatterns = router.urls + messages_router.urls + [
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('users/<int:user_id>/profile/', views.UserProfileAPIView.as_view(), name='user-profile'),
    path('presence/', views.UserPresenceView.as_view(), name='user-presence'),
    path('attachments/', views.AttachmentViewSet.as_view({'post': 'create'}), name='attachment-create'),
]