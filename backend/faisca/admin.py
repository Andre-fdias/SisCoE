from django.contrib import admin
from .models import Chat, Conversation, SystemAgentInteraction,FaiscaAgentChat, FaiscaAgentConversation


# registra os modelos de dados(models.py) no admin/django .
admin.site.register(Chat)
admin.site.register(Conversation)



# backend/faisca/admin.py
@admin.register(SystemAgentInteraction)
class SystemAgentInteractionAdmin(admin.ModelAdmin):
    list_display = ('user', 'tipo_acao', 'executado_com_sucesso', 'criado_em')
    list_filter = ('tipo_acao', 'executado_com_sucesso')
    search_fields = ('comando', 'resposta')

    # backend/faisca/admin.py
@admin.register(FaiscaAgentConversation)
class FaiscaAgentConversationAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'active')

@admin.register(FaiscaAgentChat)
class FaiscaAgentChatAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'created_at')