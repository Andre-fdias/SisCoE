# backend/chat/serializers.py
from rest_framework import serializers
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Conversation, Message, Participant, Attachment, MessageStatus, Reaction, Presence

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    presence = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'presence', 'display_name']
    
    def get_presence(self, obj):
        try:
            presence = Presence.objects.get(user=obj)
            return {
                'status': presence.status,
                'last_seen': presence.last_seen,
                'is_typing': presence.is_typing
            }
        except Presence.DoesNotExist:
            return {'status': 'offline', 'last_seen': None, 'is_typing': False}
    
    def get_display_name(self, obj):
        """Retorna o nome para exibição (full name ou email)"""
        full_name = f"{obj.first_name or ''} {obj.last_name or ''}".strip()
        return full_name or obj.email


class AttachmentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Attachment
        fields = ['id', 'file_type', 'file_url', 'thumbnail_url', 'file_size', 'duration', 'uploaded_at']
    
    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None
    
    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            return obj.thumbnail.url
        return None

class ReactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Reaction
        fields = ['id', 'user', 'emoji', 'created_at']

class MessageStatusSerializer(serializers.ModelSerializer):
    participant = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = MessageStatus
        fields = ['id', 'participant', 'status', 'delivered_at', 'read_at']

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    reactions = ReactionSerializer(many=True, read_only=True)
    statuses = MessageStatusSerializer(many=True, read_only=True)
    parent_message = serializers.SerializerMethodField()
    is_own = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'sender', 'text', 'created_at', 'edited_at', 
            'edited', 'parent_message', 'quoted_text', 'attachments', 'reactions', 
            'statuses', 'is_own', 'status'
        ]
        read_only_fields = ['conversation', 'sender', 'created_at']
    
    def get_parent_message(self, obj):
        if obj.parent_message:
            return {
                'id': obj.parent_message.id,
                'sender_name': obj.parent_message.sender.get_full_name() or obj.parent_message.sender.email,
                'text': obj.parent_message.text,
                'has_attachments': obj.parent_message.attachments.exists()
            }
        return None
    
    def get_is_own(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.sender == request.user
        return False
    
    def get_status(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                participant = Participant.objects.get(
                    conversation=obj.conversation,
                    user=request.user
                )
                status_obj = MessageStatus.objects.get(
                    message=obj,
                    participant=participant
                )
                return status_obj.status
            except (Participant.DoesNotExist, MessageStatus.DoesNotExist):
                return 'sent'
        return 'sent'

class ParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Participant
        fields = ['id', 'user', 'is_admin', 'muted_until', 'joined_at', 'last_read_message', 'unread_count']
    
    def get_unread_count(self, obj):
        if obj.last_read_message:
            return obj.conversation.messages.filter(
                created_at__gt=obj.last_read_message.created_at
            ).exclude(sender=obj.user).count()
        return obj.conversation.messages.exclude(sender=obj.user).count()

class ConversationSerializer(serializers.ModelSerializer):
    participants = ParticipantSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    participants_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'name', 'is_group', 'photo', 'created_at', 'updated_at', 
            'participants', 'last_message', 'unread_count', 'participants_ids'
        ]
    
    def get_last_message(self, obj):
        last_message = obj.messages.order_by('-created_at').first()
        if last_message:
            return MessageSerializer(last_message, context=self.context).data
        return None
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                participant = Participant.objects.get(
                    conversation=obj,
                    user=request.user
                )
                if participant.last_read_message:
                    return obj.messages.filter(
                        created_at__gt=participant.last_read_message.created_at
                    ).exclude(sender=request.user).count()
                return obj.messages.exclude(sender=request.user).count()
            except Participant.DoesNotExist:
                return 0
        return 0