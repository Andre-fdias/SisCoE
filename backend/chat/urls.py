# backend/chat/urls.py
from django.urls import path, include
from rest_framework_nested import routers
from . import views

app_name = "chat"

# Roteador principal para conversas
router = routers.SimpleRouter()
router.register(r"conversations", views.ConversationViewSet, basename="conversation")

# Roteador aninhado para mensagens dentro de conversas
messages_router = routers.NestedSimpleRouter(
    router, r"conversations", lookup="conversation"
)
messages_router.register(
    r"messages", views.MessageViewSet, basename="conversation-messages"
)

# Roteador para grupos
groups_router = routers.SimpleRouter()
groups_router.register(r"groups", views.GroupViewSet, basename="group")

urlpatterns = [
    # URLs principais do router
    path("", include(router.urls)),
    path("", include(messages_router.urls)),
    path("", include(groups_router.urls)),
    # URLs específicas
    path("users/", views.UserListView.as_view(), name="user-list"),
    path(
        "users/<int:user_id>/profile/",
        views.UserProfileAPIView.as_view(),
        name="user-profile",
    ),
    path("presence/", views.UserPresenceView.as_view(), name="user-presence"),
    path(
        "attachments/",
        views.AttachmentViewSet.as_view({"post": "create"}),
        name="attachment-create",
    ),
    # URLs para estatísticas e busca
    path("statistics/", views.ChatStatisticsView.as_view(), name="chat-statistics"),
    # path("search/", views.SearchView.as_view(), name="chat-search"), # Desativado temporariamente
    path("admin/stats/", views.AdminChatView.as_view(), name="admin-chat-stats"),
]

# URLs disponíveis:
# GET/POST    /api/chat/conversations/
# GET/PUT/DELETE /api/chat/conversations/{id}/
# POST        /api/chat/conversations/create_or_open/
# DELETE      /api/chat/conversations/{id}/delete-conversation/
#
# GET/POST    /api/chat/conversations/{conversation_id}/messages/
# GET/PUT/DELETE /api/chat/conversations/{conversation_id}/messages/{id}/
# DELETE      /api/chat/conversations/{conversation_id}/messages/{id}/delete-message/
# POST        /api/chat/conversations/{conversation_id}/messages/{id}/react/
# POST        /api/chat/conversations/{conversation_id}/messages/{id}/mark_read/
#
# GET         /api/chat/users/
# GET         /api/chat/users/{id}/profile/
# GET/POST    /api/chat/presence/
# POST        /api/chat/attachments/
# GET         /api/chat/statistics/
# GET         /api/chat/search/?q=termo
