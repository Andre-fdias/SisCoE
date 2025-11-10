from rest_framework import serializers
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count
from .models import Conversation, Message, Participant, Attachment, MessageStatus, Reaction, Presence
from backend.efetivo.models import Cadastro, Promocao, DetalhesSituacao, Imagem
from backend.accounts.utils import get_user_display_name

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    presence = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'presence', 'display_name', 'image_url']
        read_only_fields = ['id', 'email', 'first_name', 'last_name']
    
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

    def get_image_url(self, obj):
        """
        Retorna a URL absoluta do avatar do usuário.
        """
        request = self.context.get('request')
        if request:
            if hasattr(obj, 'cadastro') and obj.cadastro:
                imagem = obj.cadastro.imagens.order_by('-create_at').first()
                if imagem and imagem.image:
                    return request.build_absolute_uri(imagem.image.url)
        return None
    
    def get_display_name(self, obj):
        """
        Retorna o nome de exibição formatado chamando a função utilitária.
        """
        return get_user_display_name(obj)

class AttachmentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Attachment
        fields = ['id', 'file_type', 'file_url', 'thumbnail_url', 'file_size', 'duration', 'uploaded_at']
        read_only_fields = ['id', 'file_type', 'file_size', 'duration', 'uploaded_at']
    
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
        read_only_fields = ['id', 'user', 'created_at']

class MessageStatusSerializer(serializers.ModelSerializer):
    participant = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = MessageStatus
        fields = ['id', 'participant', 'status', 'delivered_at', 'read_at']
        read_only_fields = ['id', 'participant', 'delivered_at', 'read_at']

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    reactions = ReactionSerializer(many=True, read_only=True)
    statuses = MessageStatusSerializer(many=True, read_only=True)
    parent_message = serializers.SerializerMethodField()
    is_own = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    text = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'sender', 'text', 'created_at', 'edited_at',
            'edited', 'parent_message', 'quoted_text', 'attachments', 'reactions',
            'statuses', 'is_own', 'status'
        ]
        read_only_fields = ['id', 'conversation', 'sender', 'created_at', 'edited_at']

    def get_text(self, obj):
        return obj.decrypted_text

    def get_parent_message(self, obj):
        if obj.parent_message:
            try:
                return {
                    'id': obj.parent_message.id,
                    'sender_name': get_user_display_name(obj.parent_message.sender),
                    'text': obj.parent_message.decrypted_text,
                    'has_attachments': obj.parent_message.attachments.exists()
                }
            except Exception:
                return None
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
        read_only_fields = ['id', 'user', 'joined_at']
    
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
        child=serializers.IntegerField(), 
        write_only=True, 
        required=True
    )
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'name', 'is_group', 'photo', 'created_at', 'updated_at', 
            'participants', 'last_message', 'unread_count', 'participants_ids'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'participants']

    def validate(self, data):
        """Validação cruzada de campos."""
        participants_ids = data.get('participants_ids', [])
        request = self.context.get('request')
        current_user = request.user

        # Garante que o usuário atual esteja na lista e remove duplicatas
        if current_user.id not in participants_ids:
            participants_ids.append(current_user.id)
        
        unique_participants = list(set(participants_ids))

        if len(unique_participants) < 2:
            raise serializers.ValidationError({
                "participants_ids": "São necessários pelo menos dois participantes para uma conversa."
            })
        
        # Adiciona a lista final de participantes de volta aos dados para uso no método create
        data['final_participants'] = unique_participants
        return data

    def get_last_message(self, obj):
        """Busca a última mensagem de forma segura."""
        try:
            last_message = obj.messages.select_related('sender').order_by('-created_at').first()
            if last_message:
                return {
                    'id': last_message.id,
                    'text': last_message.decrypted_text,
                    'created_at': last_message.created_at,
                    'sender': {
                        'id': last_message.sender.id,
                        'name': get_user_display_name(last_message.sender)
                    }
                }
        except Exception:
            pass
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
    
    def create(self, validated_data):
        """
        Cria uma nova conversa ou retorna uma existente se for 1:1.
        Retorna uma tupla (conversation, created).
        """
        participants_ids = validated_data.pop('final_participants')
        validated_data.pop('participants_ids') # Remove o campo original
        is_group = validated_data.get('is_group', False)
        request = self.context.get('request')
        current_user = request.user

        # Evita duplicar conversas 1:1
        if not is_group and len(participants_ids) == 2:
            conversations = Conversation.objects.filter(
                is_group=False
            ).annotate(
                num_participants=Count('participants')
            ).filter(
                num_participants=2
            ).filter(
                participants__user_id=participants_ids[0]
            ).filter(
                participants__user_id=participants_ids[1]
            )
            if conversations.exists():
                return conversations.first(), False  # Retorna conversa existente

        # Cria a conversa
        conversation = Conversation.objects.create(**validated_data)

        # Adiciona participantes individualmente
        for user_id in participants_ids:
            Participant.objects.create(
                conversation=conversation, 
                user_id=user_id,
                is_admin=(user_id == current_user.id) # Criador é admin
            )

        return conversation, True  # Retorna nova conversa


# --- Serializers para Perfil de Usuário ---

class ImagemSerializer(serializers.ModelSerializer):
    """Serializer para o modelo de Imagem do efetivo."""
    class Meta:
        model = Imagem
        fields = ['image']

class PromocaoSerializer(serializers.ModelSerializer):
    """Serializer para o modelo de Promoção do efetivo."""
    class Meta:
        model = Promocao
        fields = ['posto_grad', 'ultima_promocao']

class DetalhesSituacaoSerializer(serializers.ModelSerializer):
    """Serializer para os detalhes da situação do efetivo."""
    class Meta:
        model = DetalhesSituacao
        fields = ['situacao', 'sgb', 'funcao']

class CadastroSerializer(serializers.ModelSerializer):
    """Serializer para o modelo de Cadastro básico do efetivo."""
    class Meta:
        model = Cadastro
        fields = ['re', 'dig', 'nome_de_guerra']

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer completo para o perfil de um usuário, agregando dados
    de `accounts` e `efetivo`.
    """
    cadastro = CadastroSerializer(read_only=True)
    promocao = serializers.SerializerMethodField()
    situacao = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    nome_de_guerra = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name',
            'cadastro', 'promocao', 'situacao', 'avatar', 'nome_de_guerra'
        ]

    def get_promocao(self, obj):
        """Retorna a promoção mais recente do usuário."""
        if hasattr(obj, 'cadastro') and obj.cadastro:
            promocao = obj.cadastro.promocoes.order_by('-ultima_promocao').first()
            if promocao:
                return PromocaoSerializer(promocao).data
        return None

    def get_situacao(self, obj):
        """Retorna a situação funcional mais recente do usuário."""
        if hasattr(obj, 'cadastro') and obj.cadastro:
            situacao = obj.cadastro.detalhes_situacao.order_by('-data_alteracao').first()
            if situacao:
                return DetalhesSituacaoSerializer(situacao).data
        return None

    def get_avatar(self, obj):
        """
        Retorna a URL absoluta do avatar do usuário, buscando primeiro no
        perfil de `accounts` e depois nas imagens de `efetivo`.
        """
        request = self.context.get('request')
        # Tenta buscar no modelo Profile do app accounts
        if hasattr(obj, 'profile') and obj.profile and obj.profile.avatar:
            return request.build_absolute_uri(obj.profile.avatar.url)
        
        # Se não encontrar, tenta buscar no modelo Imagem do app efetivo
        if hasattr(obj, 'cadastro') and obj.cadastro:
            imagem = obj.cadastro.imagens.order_by('-create_at').first()
            if imagem and imagem.image:
                return request.build_absolute_uri(imagem.image.url)
        
        return None

    def get_nome_de_guerra(self, obj):
        """Retorna o nome de guerra do usuário."""
        if hasattr(obj, 'cadastro') and obj.cadastro:
            return obj.cadastro.nome_de_guerra
        return None