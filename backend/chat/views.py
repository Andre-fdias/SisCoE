from rest_framework import viewsets, status, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.db.models import Count, Q, Prefetch
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Conversation, Message, Participant, Attachment, MessageStatus, Reaction, Presence
from .serializers import (
    ConversationSerializer, MessageSerializer, ParticipantSerializer,
    AttachmentSerializer, ReactionSerializer, UserSerializer
)

User = get_user_model()

class ChatView(LoginRequiredMixin, TemplateView):
    """ Renderiza a página principal do chat. """
    template_name = "chat/conversation.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_users'] = User.objects.exclude(pk=self.request.user.pk)
        return context

class UserPresenceView(APIView):  # ← ESTA CLASSE PRECISA EXISTIR
    """ API para gerenciar presença dos usuários. """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """ Obtém status de presença dos usuários. """
        user_ids = request.GET.getlist('user_ids', [])
        
        # Se user_ids foi passado como string separada por vírgulas
        if user_ids and isinstance(user_ids[0], str):
            user_ids = user_ids[0].split(',')
        
        # Filtra IDs válidos
        valid_user_ids = []
        for uid in user_ids:
            try:
                valid_user_ids.append(int(uid))
            except (ValueError, TypeError):
                continue
        
        if valid_user_ids:
            presences = Presence.objects.filter(user_id__in=valid_user_ids)
        else:
            # Retorna presença de todos os usuários (com limite)
            presences = Presence.objects.all()[:100]
        
        presence_data = {}
        for presence in presences:
            presence_data[str(presence.user_id)] = {
                'status': presence.status,
                'last_seen': presence.last_seen,
                'is_typing': presence.is_typing
            }
        
        return Response(presence_data)

    def post(self, request):
        """ Atualiza status de presença do usuário. """
        status = request.data.get('status', 'online')
        
        if status not in ['online', 'offline', 'away']:
            return Response(
                {'error': 'Status inválido'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        presence, created = Presence.objects.update_or_create(
            user=request.user,
            defaults={
                'status': status,
                'last_seen': timezone.now()
            }
        )
        
        return Response({
            'status': presence.status,
            'last_seen': presence.last_seen
        })

class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar conversas.
    """
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """ Retorna apenas as conversas do usuário logado. """
        user = self.request.user
        return Conversation.objects.filter(
            participants__user=user
        ).prefetch_related(
            Prefetch('participants', queryset=Participant.objects.select_related('user')),
            Prefetch('messages', queryset=Message.objects.select_related('sender').order_by('-created_at')[:1])
        ).distinct().order_by('-updated_at')

    def get_serializer_context(self):
        """ Adiciona request ao contexto do serializer. """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def create(self, request, *args, **kwargs):
        participants_ids = request.data.get('participants_ids', [])
        is_group = request.data.get('is_group', False)
        name = request.data.get('name', '')

        # Garante que o usuário atual esteja sempre na lista
        if request.user.id not in participants_ids:
            participants_ids.append(request.user.id)

        # Remove duplicatas
        participants_ids = list(set(participants_ids))

        # Lógica para evitar duplicar conversas 1:1
        if not is_group and len(participants_ids) == 2:
            existing_conversation = self._find_existing_1on1_conversation(participants_ids)
            if existing_conversation:
                serializer = self.get_serializer(existing_conversation)
                return Response(serializer.data, status=status.HTTP_200_OK)
        
        # Criação da conversa
        conversation_data = {
            'name': name,
            'is_group': is_group
        }
        serializer = self.get_serializer(data=conversation_data)
        serializer.is_valid(raise_exception=True)
        conversation = serializer.save()

        # Adiciona os participantes
        participants_to_create = [
            Participant(
                conversation=conversation, 
                user_id=user_id,
                is_admin=(user_id == request.user.id)  # Criador é admin
            ) for user_id in participants_ids
        ]
        Participant.objects.bulk_create(participants_to_create)

        # Atualiza o contexto para serialização
        conversation = self.get_queryset().get(id=conversation.id)
        serializer = self.get_serializer(conversation)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def _find_existing_1on1_conversation(self, participants_ids):
        """ Encontra conversa 1:1 existente entre os participantes. """
        conversations = Conversation.objects.filter(
            is_group=False,
            participants__user_id__in=participants_ids
        ).annotate(
            num_participants=Count('participants')
        ).filter(num_participants=2)
        
        # Garante que ambos os participantes estão na conversa
        for conversation in conversations:
            conversation_participants = set(conversation.participants.values_list('user_id', flat=True))
            if conversation_participants == set(participants_ids):
                return conversation
        return None

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """ Marca todas as mensagens da conversa como lidas. """
        conversation = self.get_object()
        
        try:
            participant = Participant.objects.get(
                conversation=conversation,
                user=request.user
            )
            
            # Encontra a última mensagem
            last_message = conversation.messages.order_by('-created_at').first()
            if last_message:
                participant.last_read_message = last_message
                participant.save()
                
                # Atualiza status das mensagens
                MessageStatus.objects.filter(
                    participant=participant,
                    status__in=['sent', 'delivered']
                ).update(
                    status='read',
                    read_at=timezone.now()
                )
            
            return Response({'status': 'conversation marked as read'})
        except Participant.DoesNotExist:
            return Response(
                {'error': 'User is not a participant in this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )

    @action(detail=True, methods=['get'])
    def participants(self, request, pk=None):
        """ Lista participantes da conversa. """
        conversation = self.get_object()
        participants = conversation.participants.all()
        serializer = ParticipantSerializer(participants, many=True)
        return Response(serializer.data)

class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar mensagens dentro de uma conversa.
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """ Retorna mensagens de uma conversa específica. """
        conversation_id = self.kwargs.get('conversation_pk')
        
        if not conversation_id:
            return Message.objects.none()
            
        # Verifica se o usuário é participante
        if not Participant.objects.filter(
            conversation_id=conversation_id,
            user=self.request.user
        ).exists():
            return Message.objects.none()

        return Message.objects.filter(
            conversation_id=conversation_id
        ).select_related(
            'sender', 'conversation', 'parent_message'
        ).prefetch_related(
            'attachments', 'reactions', 'reactions__user', 'statuses'
        ).order_by('created_at')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        """ Associa a mensagem à conversa e ao remetente. """
        conversation_id = self.kwargs.get('conversation_pk')
        
        try:
            conversation = Conversation.objects.get(pk=conversation_id)
            # Verifica se o usuário é participante
            if not Participant.objects.filter(
                conversation=conversation,
                user=self.request.user
            ).exists():
                raise serializers.ValidationError("O usuário não é participante desta conversa.")
            
            serializer.save(conversation=conversation, sender=self.request.user)
            
            # Atualiza timestamp da conversa
            conversation.updated_at = timezone.now()
            conversation.save()
            
        except Conversation.DoesNotExist:
            raise serializers.ValidationError("Conversa não encontrada.")

    @action(detail=True, methods=['post'])
    def react(self, request, conversation_pk=None, pk=None):
        """ Adiciona/remove reação a uma mensagem. """
        message = self.get_object()
        emoji = request.data.get('emoji')
        
        if not emoji:
            return Response(
                {'error': 'Emoji é obrigatório'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Remove reação existente do mesmo usuário
        Reaction.objects.filter(
            message=message,
            user=request.user,
            emoji=emoji
        ).delete()
        
        # Se não havia reação, adiciona nova
        if not Reaction.objects.filter(message=message, user=request.user, emoji=emoji).exists():
            reaction = Reaction.objects.create(
                message=message,
                user=request.user,
                emoji=emoji
            )
            serializer = ReactionSerializer(reaction)
            return Response(serializer.data)
        
        return Response({'status': 'reaction removed'})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, conversation_pk=None, pk=None):
        """ Marca uma mensagem específica como lida. """
        message = self.get_object()
        
        try:
            participant = Participant.objects.get(
                conversation_id=conversation_pk,
                user=request.user
            )
            
            status_obj, created = MessageStatus.objects.get_or_create(
                message=message,
                participant=participant,
                defaults={'status': 'read', 'read_at': timezone.now()}
            )
            
            if not created and status_obj.status != 'read':
                status_obj.status = 'read'
                status_obj.read_at = timezone.now()
                status_obj.save()
            
            return Response({'status': 'message marked as read'})
            
        except Participant.DoesNotExist:
            return Response(
                {'error': 'User is not a participant in this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )

class AttachmentViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """ ViewSet para gerenciar anexos. """
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """ Associa o anexo ao usuário atual. """
        serializer.save()