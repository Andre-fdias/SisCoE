# backend/chat/views.py
from rest_framework import viewsets, status, mixins, serializers, generics, permissions
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.db.models import Count, Prefetch, Q, Max
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import Conversation, Message, Participant, Attachment, MessageStatus, Reaction, Presence
from .serializers import (
    ConversationSerializer, MessageSerializer, AttachmentSerializer, 
    ReactionSerializer, UserSerializer, UserProfileSerializer
)
from backend.accounts.utils import get_user_display_name

User = get_user_model()

# --- Helpers de Conversão e Lógica Reutilizável ---

def safe_int_conversion(ids):
    """Converte lista de IDs (str) em lista de inteiros válidos."""
    valid_ids = []
    # Lida com strings separadas por vírgula que podem vir de request.GET.getlist
    if isinstance(ids, str):
        ids = ids.split(',')
    
    for uid in ids:
        try:
            valid_ids.append(int(uid))
        except (ValueError, TypeError):
            continue
    return valid_ids

class ChatView(LoginRequiredMixin, TemplateView):
    """Renderiza a página principal do chat."""
    template_name = "chat/conversation.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Otimiza a busca dos usuários excluindo o usuário atual.
        context['all_users'] = User.objects.exclude(pk=self.request.user.pk).order_by('email')
        context['user_display_name'] = get_user_display_name(self.request.user)
        return context

# --- Vistas da API REST (DRF) ---

class UserListView(generics.ListAPIView):
    """API para listar usuários para a lista de contatos."""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        CORREÇÃO: Filtra usuários de forma mais flexível
        """
        # Opção 1: Todos os usuários (exceto o atual)
        queryset = User.objects.exclude(pk=self.request.user.pk)
        
        # Opção 2: Se você tem um campo de permissões específico
        # try:
        #     queryset = User.objects.filter(
        #         profile__is_active=True  # ou outro campo de perfil
        #     ).exclude(pk=self.request.user.pk)
        # except:
        #     queryset = User.objects.exclude(pk=self.request.user.pk)
        
        return queryset.order_by('first_name', 'last_name', 'email')
    
    

class UserProfileAPIView(APIView):
    """API para buscar o perfil de um usuário."""
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id, *args, **kwargs):
        try:
            user = User.objects.select_related('cadastro').prefetch_related(
                'cadastro__promocoes', 
                'cadastro__detalhes_situacao', 
                'cadastro__imagens'
            ).get(pk=user_id)
        except User.DoesNotExist:
            return Response({"error": "Usuário não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = UserProfileSerializer(user, context={'request': request})
        return Response(serializer.data)


class UserPresenceView(APIView):
    """API para gerenciar presença dos usuários."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Obtém status de presença dos usuários especificados por user_ids."""
        user_ids_raw = request.GET.getlist('user_ids', [])
        valid_user_ids = safe_int_conversion(user_ids_raw)
        
        if valid_user_ids:
            presences = Presence.objects.filter(user_id__in=valid_user_ids)
        else:
            # Retorna presença de todos os usuários (limite 100)
            presences = Presence.objects.all()[:100]
        
        presence_data = {
            str(presence.user_id): {
                'status': presence.status,
                'last_seen': presence.last_seen,
                'is_typing': presence.is_typing
            }
            for presence in presences
        }
        
        return Response(presence_data)

    def post(self, request):
        """Atualiza status de presença do usuário logado."""
        status_val = request.data.get('status', 'online')
        
        if status_val not in ['online', 'offline', 'away']:
            return Response(
                {'error': 'Status inválido'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        presence, created = Presence.objects.update_or_create(
            user=request.user,
            defaults={
                'status': status_val,
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
        """Retorna apenas as conversas do usuário logado, com prefetch otimizado."""
        user = self.request.user
        
        queryset = Conversation.objects.filter(
            participants__user=user
        ).prefetch_related(
            Prefetch(
                'participants', 
                queryset=Participant.objects.select_related('user'), 
                to_attr='prefetched_participants'
            )
        ).distinct().order_by('-updated_at')
        
        return queryset

    def get_serializer_context(self):
        """Adiciona request ao contexto do serializer."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def _find_existing_1on1_conversation(self, participants_ids):
        """Encontra conversa 1:1 existente entre os participantes (IDs inteiros)."""
        # Procura conversas com exatamente 2 participantes, ambos presentes na lista.
        conversations = Conversation.objects.filter(
            is_group=False,
            participants__user_id__in=participants_ids
        ).annotate(
            num_participants=Count('participants', distinct=True)
        ).filter(
            num_participants=2
        ).annotate(
            match_count=Count('participants', filter=Q(participants__user_id__in=participants_ids), distinct=True)
        ).filter(match_count=2)
        
        return conversations.first()

    def create(self, request, *args, **kwargs):
        """
        Cria uma nova conversa. A lógica foi movida para o ConversationSerializer.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # O método create do serializer agora retorna a instância e um booleano `created`
        conversation, created = serializer.save()

        # Determina o status code com base se a conversa foi criada ou reutilizada
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        
        # Recarrega a instância para garantir que os dados de prefetch estejam corretos
        instance = self.get_queryset().get(id=conversation.id)
        serializer = self.get_serializer(instance)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status_code, headers=headers)

    @action(detail=False, methods=['post'], url_path='create_or_open')
    def create_or_open_private_conversation(self, request):
        """
        Encontra ou cria uma conversa 1:1 com um usuário específico.
        Espera {'user_id': <id>} no corpo da requisição.
        """
        target_user_id = request.data.get('user_id')
        if not target_user_id:
            return Response({'error': 'user_id é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            target_user = User.objects.get(pk=target_user_id)
        except User.DoesNotExist:
            return Response({'error': 'Usuário não encontrado'}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        participants_ids = [user.id, target_user.id]

        # Usa o helper para encontrar conversa 1:1
        conversation = self._find_existing_1on1_conversation(participants_ids)
        
        status_code = status.HTTP_200_OK
        if not conversation:
            # Cria a conversa se não existir
            conversation = Conversation.objects.create(is_group=False)
            Participant.objects.bulk_create([
                Participant(user=user, conversation=conversation),
                Participant(user=target_user, conversation=conversation)
            ])
            status_code = status.HTTP_201_CREATED

        # Recarrega e serializa a resposta
        instance = self.get_queryset().get(id=conversation.id)
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status_code)

    @action(detail=True, methods=['delete'], url_path='delete-conversation')
    def delete_conversation(self, request, pk=None):
        """Exclui conversa permanentemente"""
        conversation = self.get_object()
        
        # Verifica se usuário é participante
        if not conversation.participants.filter(user=request.user).exists():
            return Response(
                {'error': 'Você não é participante desta conversa'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        conversation_id = str(conversation.id)
        conversation.delete()
        
        return Response({'status': 'conversa excluída'})

class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar mensagens dentro de uma conversa.
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retorna mensagens de uma conversa específica com prefetch otimizado."""
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
            'attachments', 
            Prefetch('reactions', queryset=Reaction.objects.select_related('user')), 
            'statuses'
        ).order_by('-created_at')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        context['conversation_id'] = self.kwargs.get('conversation_pk')
        return context

    def perform_create(self, serializer):
        """Associa a mensagem à conversa e ao remetente e cria MessageStatus para todos."""
        conversation_id = self.kwargs.get('conversation_pk')
        
        try:
            conversation = get_object_or_404(Conversation, pk=conversation_id)
            
            # Valida participação
            if not Participant.objects.filter(conversation=conversation, user=self.request.user).exists():
                raise serializers.ValidationError("O usuário não é participante desta conversa.")
            
            message = serializer.save(conversation=conversation, sender=self.request.user)
            
            # Cria status para todos os participantes. Marca como 'delivered' se não for o remetente.
            participants = Participant.objects.filter(conversation=conversation)
            statuses = []
            for participant in participants:
                is_sender = (participant.user.id == self.request.user.id)
                statuses.append(MessageStatus(
                    message=message, 
                    participant=participant, 
                    status='sent' if is_sender else 'delivered',
                    delivered_at=None if is_sender else timezone.now()
                ))
            MessageStatus.objects.bulk_create(statuses)
            
            # Atualiza timestamp da conversa
            conversation.updated_at = timezone.now()
            conversation.save()
            
        except Exception as e:
            # Captura e eleva erros
            raise serializers.ValidationError(str(e))

    @action(detail=True, methods=['post'])
    def react(self, request, conversation_pk=None, pk=None):
        """Adiciona/remove reação a uma mensagem."""
        message = self.get_object()
        emoji = request.data.get('emoji')
        
        if not emoji:
            return Response(
                {'error': 'Emoji é obrigatório'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Tenta encontrar uma reação existente do usuário com este emoji
            reaction = Reaction.objects.get(
                message=message,
                user=request.user,
                emoji=emoji
            )
            reaction.delete()
            return Response({'status': 'reaction removed'})
        except Reaction.DoesNotExist:
            # Se não existir, cria
            new_reaction = Reaction.objects.create(
                message=message,
                user=request.user,
                emoji=emoji
            )
            serializer = ReactionSerializer(new_reaction)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, conversation_pk=None, pk=None):
        """Marca uma mensagem específica como lida e atualiza o ponteiro do participante."""
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
            
            # Atualiza o ponteiro de última mensagem lida
            participant.last_read_message = message
            participant.save()
            
            return Response({'status': 'message marked as read'})
            
        except Participant.DoesNotExist:
            return Response(
                {'error': 'User is not a participant in this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )

    @action(detail=True, methods=['delete'], url_path='delete-message')
    def delete_message(self, request, conversation_pk=None, pk=None):
        """Exclui mensagem individual"""
        message = self.get_object()
        
        # Verifica permissão: apenas remetente ou admin
        if message.sender != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Sem permissão para excluir esta mensagem'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        message_id = str(message.id)
        message.delete()
        
        # Notifica via WebSocket sobre a exclusão
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'chat_{conversation_pk}',
                {
                    'type': 'message.delete',
                    'message_id': message_id
                }
            )
        except Exception as e:
            print(f"Erro ao notificar WebSocket: {e}")
        
        return Response({'status': 'mensagem excluída'})

class AttachmentViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """ViewSet para gerenciar anexos."""
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Valida que o usuário pode anexar à mensagem."""
        message_id = self.request.data.get('message')
        if message_id:
            try:
                message = Message.objects.get(id=message_id)
                # Verifica se o usuário é participante da conversa
                if not Participant.objects.filter(
                    conversation=message.conversation,
                    user=self.request.user
                ).exists():
                    raise serializers.ValidationError("Você não tem permissão para anexar arquivos nesta conversa.")
            except Message.DoesNotExist:
                raise serializers.ValidationError("Mensagem não encontrada.")
        
        serializer.save()

# --- Views para Grupos ---

class GroupViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciar grupos de conversa."""
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retorna apenas grupos onde o usuário é participante."""
        user = self.request.user
        return Conversation.objects.filter(
            participants__user=user,
            is_group=True
        ).prefetch_related(
            Prefetch(
                'participants',
                queryset=Participant.objects.select_related('user'),
                to_attr='prefetched_participants'
            )
        ).distinct().order_by('-updated_at')

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """Adiciona membro a um grupo."""
        conversation = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({'error': 'user_id é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'Usuário não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        
        # Verifica se o usuário atual é admin do grupo
        participant = Participant.objects.get(conversation=conversation, user=request.user)
        if not participant.is_admin:
            return Response({'error': 'Apenas administradores podem adicionar membros'}, status=status.HTTP_403_FORBIDDEN)
        
        # Adiciona o usuário ao grupo
        Participant.objects.get_or_create(
            conversation=conversation,
            user=user,
            defaults={'is_admin': False}
        )
        
        return Response({'status': 'Membro adicionado com sucesso'})

    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        """Remove membro de um grupo."""
        conversation = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({'error': 'user_id é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verifica se o usuário atual é admin do grupo
        participant = Participant.objects.get(conversation=conversation, user=request.user)
        if not participant.is_admin:
            return Response({'error': 'Apenas administradores podem remover membros'}, status=status.HTTP_403_FORBIDDEN)
        
        # Remove o usuário do grupo (não pode remover a si mesmo)
        if int(user_id) == request.user.id:
            return Response({'error': 'Não é possível remover a si mesmo'}, status=status.HTTP_400_BAD_REQUEST)
        
        Participant.objects.filter(conversation=conversation, user_id=user_id).delete()
        
        return Response({'status': 'Membro removido com sucesso'})

# --- Views para estatísticas e relatórios ---

class ChatStatisticsView(APIView):
    """API para obter estatísticas do chat."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retorna estatísticas do chat para o usuário atual."""
        user = request.user
        
        total_conversations = Conversation.objects.filter(participants__user=user).count()
        total_messages_sent = Message.objects.filter(sender=user).count()
        unread_messages_count = MessageStatus.objects.filter(
            participant__user=user,
            status='delivered'
        ).count()
        
        # Conversas mais ativas
        active_conversations = Conversation.objects.filter(
            participants__user=user
        ).annotate(
            message_count=Count('messages'),
            last_activity=Max('messages__created_at')
        ).order_by('-last_activity')[:5]
        
        active_conversations_data = [
            {
                'id': conv.id,
                'name': conv.name or f"Conversa com {conv.participants.exclude(user=user).first().user.display_name if conv.participants.exclude(user=user).exists() else 'Usuário'}",
                'message_count': conv.message_count,
                'last_activity': conv.last_activity
            }
            for conv in active_conversations
        ]
        
        return Response({
            'total_conversations': total_conversations,
            'total_messages_sent': total_messages_sent,
            'unread_messages': unread_messages_count,
            'active_conversations': active_conversations_data
        })

# --- Views para administração ---

class AdminChatView(APIView):
    """API para administração do chat (apenas staff)."""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """Retorna estatísticas administrativas do chat."""
        total_conversations = Conversation.objects.count()
        total_messages = Message.objects.count()
        total_users = User.objects.count()
        active_today = Message.objects.filter(
            created_at__date=timezone.now().date()
        ).count()
        
        return Response({
            'total_conversations': total_conversations,
            'total_messages': total_messages,
            'total_users': total_users,
            'messages_today': active_today,
            'storage_used': f"{(total_messages * 0.1):.2f} KB"  # Estimativa
        })

    def post(self, request):
        """Executa ações administrativas."""
        action_type = request.data.get('action')
        
        if action_type == 'cleanup_old_messages':
            from .tasks import delete_old_messages
            result = delete_old_messages.delay()
            return Response({'status': 'Limpeza iniciada', 'task_id': result.id})
        
        elif action_type == 'export_statistics':
            # Lógica para exportar estatísticas
            return Response({'status': 'Exportação em desenvolvimento'})
        
        return Response({'error': 'Ação não reconhecida'}, status=status.HTTP_400_BAD_REQUEST)

# --- Views para busca e filtros ---

class SearchView(APIView):
    """API para busca de mensagens e conversas."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Busca mensagens e conversas baseado no termo de busca."""
        search_term = request.GET.get('q', '').strip()
        if not search_term:
            return Response({'error': 'Termo de busca é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        
        # Busca em conversas do usuário
        conversations = Conversation.objects.filter(
            participants__user=user
        ).filter(
            Q(name__icontains=search_term) |
            Q(participants__user__first_name__icontains=search_term) |
            Q(participants__user__last_name__icontains=search_term) |
            Q(participants__user__email__icontains=search_term)
        ).distinct()
        
        # Busca em mensagens do usuário
        messages = Message.objects.filter(
            conversation__participants__user=user,
            text__icontains=search_term
        ).select_related('sender', 'conversation').order_by('-created_at')[:50]
        
        conversation_serializer = ConversationSerializer(conversations, many=True, context={'request': request})
        message_serializer = MessageSerializer(messages, many=True, context={'request': request})
        
        return Response({
            'conversations': conversation_serializer.data,
            'messages': message_serializer.data,
            'search_term': search_term
        })