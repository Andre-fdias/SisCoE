from rest_framework import viewsets, status, mixins, serializers, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.db.models import Count, Prefetch, Q
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
        return context

# --- Vistas da API REST (DRF) ---

class UserListView(generics.ListAPIView):
    """API para listar usuários para a lista de contatos."""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filtra a lista de contatos para incluir apenas usuários com permissões
        'sgb', 'gestor', ou 'admin', e exclui o usuário atual.
        """
        allowed_permissions = ['sgb', 'gestor', 'admin']
        return User.objects.filter(
            permissoes__in=allowed_permissions
        ).exclude(
            pk=self.request.user.pk
        ).order_by('first_name', 'last_name')

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

class AttachmentViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """ViewSet para gerenciar anexos."""
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated]

    # ATENÇÃO: O modelo Attachment requer 'message' (FK). A API REST 
    # de upload deve incluir o 'message_id' no payload. 
    # O método `perform_create` padrão do DRF tentará salvar.
    def perform_create(self, serializer):
        # A validação de que o usuário pode anexar a esta mensagem é delegada
        # ao serializer ou deve ser adicionada aqui (omitida para simplificação).
        serializer.save()