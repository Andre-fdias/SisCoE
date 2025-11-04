from django.contrib import admin
from .models import Conversation, Participant, Message, Attachment, MessageStatus, Reaction, Presence

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_group', 'participants_count', 'created_at', 'updated_at')
    search_fields = ('name', 'participants__user__email')
    list_filter = ('is_group', 'created_at')
    filter_horizontal = ()
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    def participants_count(self, obj):
        return obj.participants.count()
    participants_count.short_description = 'Participantes'

@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('user', 'conversation', 'is_admin', 'joined_at')
    search_fields = ('user__email', 'conversation__name')
    list_filter = ('is_admin', 'joined_at')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'sender', 'text_preview', 'created_at', 'edited')
    search_fields = ('sender__email', 'text')
    list_filter = ('created_at', 'conversation', 'edited')
    readonly_fields = ('id', 'created_at')
    
    def text_preview(self, obj):
        return obj.text[:50] + '...' if obj.text and len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Texto'

@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'file_type', 'file_size', 'uploaded_at')
    list_filter = ('file_type', 'uploaded_at')
    readonly_fields = ('id', 'uploaded_at')

@admin.register(MessageStatus)
class MessageStatusAdmin(admin.ModelAdmin):
    list_display = ('message', 'participant', 'status', 'delivered_at', 'read_at')
    list_filter = ('status',)
    readonly_fields = ('timestamp',)

@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ('message', 'user', 'emoji', 'created_at')
    list_filter = ('emoji', 'created_at')
    search_fields = ('user__email', 'message__text')

@admin.register(Presence)
class PresenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'last_seen', 'is_typing')
    list_filter = ('status', 'is_typing')
    search_fields = ('user__email',)
    readonly_fields = ('last_seen',)