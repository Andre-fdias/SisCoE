

# backend/faisca/admin.py
from django.contrib import admin
from .models import Chat, Conversation, SystemAgentInteraction,FaiscaAgentChat,FaiscaAgentConversation,FaiscaAgentQueryLog


# registra os modelos de dados(models.py) no admin/django .
admin.site.register(Chat)
admin.site.register(Conversation)



@admin.register(SystemAgentInteraction)
class SystemAgentInteractionAdmin(admin.ModelAdmin):
    list_display = ('user', 'tipo_acao', 'executado_com_sucesso', 'criado_em')
    list_filter = ('tipo_acao', 'executado_com_sucesso')
    search_fields = ('comando', 'resposta')



@admin.register(FaiscaAgentConversation)
class FaiscaAgentConversationAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'active')

@admin.register(FaiscaAgentChat)
class FaiscaAgentChatAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'created_at')

@admin.register(FaiscaAgentQueryLog)
class FaiscaAgentQueryLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'truncated_query', 'was_successful', 'created_at', 'execution_time')
    list_filter = ('was_successful', 'user', 'created_at')
    search_fields = ('query', 'response')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    def truncated_query(self, obj):
        return obj.query[:50] + '...' if len(obj.query) > 50 else obj.query
    truncated_query.short_description = 'Consulta'