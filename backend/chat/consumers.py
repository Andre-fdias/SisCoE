import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Conversation, Participant, Message, MessageStatus, Reaction, Presence

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conversation_id = None
        self.conversation_group_name = None
        self.user = None

    async def connect(self):
        """ Chamado quando o WebSocket é aberto. """
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.conversation_group_name = f'chat_{self.conversation_id}'
        self.user = self.scope['user']

        if self.user.is_anonymous:
            await self.close()
            return

        # Verifica se o usuário tem permissão para entrar na conversa
        if await self.is_participant():
            # Atualiza presença
            await self.update_presence('online')
            
            # Entra no grupo da conversa
            await self.channel_layer.group_add(
                self.conversation_group_name,
                self.channel_name
            )
            await self.accept()
            
            # Notifica que usuário entrou
            await self.channel_layer.group_send(
                self.conversation_group_name,
                {
                    'type': 'presence.update',
                    'user_id': str(self.user.id),
                    'status': 'online'
                }
            )
        else:
            await self.close()

    async def disconnect(self, close_code):
        """ Chamado quando o WebSocket é fechado. """
        if self.user and not self.user.is_anonymous:
            await self.update_presence('offline')
            
            # Notifica que usuário saiu
            await self.channel_layer.group_send(
                self.conversation_group_name,
                {
                    'type': 'presence.update',
                    'user_id': str(self.user.id),
                    'status': 'offline'
                }
            )
        
        # Sai do grupo da conversa
        if self.conversation_group_name:
            await self.channel_layer.group_discard(
                self.conversation_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """ Recebe uma mensagem do WebSocket. """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'message.send':
                await self.handle_message_send(data)
            elif message_type == 'message.read':
                await self.handle_message_read(data)
            elif message_type == 'typing.start':
                await self.handle_typing_start()
            elif message_type == 'typing.stop':
                await self.handle_typing_stop()
            elif message_type == 'message.edit':
                await self.handle_message_edit(data)
            elif message_type == 'message.delete':
                await self.handle_message_delete(data)
            elif message_type == 'message.react':
                await self.handle_message_react(data)
                
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON")
        except Exception as e:
            await self.send_error(str(e))

    # --- Handlers para diferentes tipos de mensagens ---

    async def handle_message_send(self, data):
        """ Lida com envio de mensagem. """
        text = data.get('text', '')
        reply_to = data.get('reply_to')
        attachments = data.get('attachments', [])
        
        # Cria a mensagem
        message = await self.create_message(text, reply_to, attachments)
        
        # Serializa para enviar aos clientes
        serialized_message = await self.serialize_message(message)
        
        # Envia para o grupo
        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'message.receive',
                'message': serialized_message
            }
        )
        
        # Marca como entregue para todos os participantes online
        await self.mark_as_delivered(message)

    async def handle_message_read(self, data):
        """ Marca mensagem como lida. """
        message_id = data.get('message_id')
        await self.mark_as_read(message_id)

    async def handle_typing_start(self):
        """ Inicia indicador de digitação. """
        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'typing.indicator',
                'user_id': self.user.id,
                'user_name': self.user.get_full_name() or self.user.email,
                'action': 'start'
            }
        )

    async def handle_typing_stop(self):
        """ Para indicador de digitação. """
        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'typing.indicator',
                'user_id': self.user.id,
                'user_name': self.user.get_full_name() or self.user.email,
                'action': 'stop'
            }
        )

    async def handle_message_edit(self, data):
        """ Edita uma mensagem existente. """
        message_id = data.get('message_id')
        new_text = data.get('text')
        message = await self.edit_message(message_id, new_text)
        
        if message:
            serialized_message = await self.serialize_message(message)
            await self.channel_layer.group_send(
                self.conversation_group_name,
                {
                    'type': 'message.update',
                    'message': serialized_message
                }
            )

    async def handle_message_delete(self, data):
        """ Exclui uma mensagem. """
        message_id = data.get('message_id')
        success = await self.delete_message(message_id)
        
        if success:
            await self.channel_layer.group_send(
                self.conversation_group_name,
                {
                    'type': 'message.delete',
                    'message_id': message_id
                }
            )

    async def handle_message_react(self, data):
        """ Adiciona/remove reação a mensagem. """
        message_id = data.get('message_id')
        emoji = data.get('emoji')
        reaction = await self.toggle_reaction(message_id, emoji)
        
        if reaction is not None:
            await self.channel_layer.group_send(
                self.conversation_group_name,
                {
                    'type': 'message.reaction',
                    'message_id': message_id,
                    'reaction': {
                        'id': str(reaction.id),
                        'user': {
                            'id': str(self.user.id),
                            'name': self.user.get_full_name() or self.user.email
                        },
                        'emoji': emoji,
                        'action': 'add' if reaction else 'remove'
                    }
                }
            )

    # --- Handlers de eventos do group_send ---

    async def message_receive(self, event):
        """ Envia mensagem recebida para o WebSocket. """
        await self.send(text_data=json.dumps({
            'type': 'message.receive',
            'message': event['message']
        }))

    async def message_update(self, event):
        """ Envia mensagem atualizada para o WebSocket. """
        await self.send(text_data=json.dumps({
            'type': 'message.update',
            'message': event['message']
        }))

    async def message_delete(self, event):
        """ Notifica sobre mensagem excluída. """
        await self.send(text_data=json.dumps({
            'type': 'message.delete',
            'message_id': event['message_id']
        }))

    async def message_reaction(self, event):
        """ Notifica sobre reação a mensagem. """
        await self.send(text_data=json.dumps({
            'type': 'message.reaction',
            'message_id': event['message_id'],
            'reaction': event['reaction']
        }))

    async def typing_indicator(self, event):
        """ Envia indicador de digitação. """
        await self.send(text_data=json.dumps({
            'type': 'typing.indicator',
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'action': event['action']
        }))

    async def presence_update(self, event):
        """ Atualiza status de presença. """
        await self.send(text_data=json.dumps({
            'type': 'presence.update',
            'user_id': event['user_id'],
            'status': event['status']
        }))

    async def message_status(self, event):
        """ Atualiza status da mensagem. """
        await self.send(text_data=json.dumps({
            'type': 'message.status',
            'message_id': event['message_id'],
            'status': event['status'],
            'user_id': event['user_id']
        }))

    # --- Métodos Auxiliares ---

    async def send_error(self, error_message):
        """ Envia mensagem de erro. """
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': error_message
        }))

    @database_sync_to_async
    def is_participant(self):
        """ Verifica se o usuário é participante da conversa. """
        return Participant.objects.filter(
            conversation_id=self.conversation_id,
            user=self.user
        ).exists()

    @database_sync_to_async
    def create_message(self, text, reply_to=None, attachments=None):
        """ Cria e salva uma nova mensagem. """
        from .serializers import MessageSerializer
        
        conversation = Conversation.objects.get(id=self.conversation_id)
        parent_message = None
        
        if reply_to:
            try:
                parent_message = Message.objects.get(id=reply_to)
            except Message.DoesNotExist:
                pass
        
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            text=text,
            parent_message=parent_message,
            quoted_text=parent_message.text if parent_message else None
        )
        
        # Cria status para todos os participantes
        participants = Participant.objects.filter(conversation=conversation)
        statuses = [
            MessageStatus(message=message, participant=participant)
            for participant in participants
        ]
        MessageStatus.objects.bulk_create(statuses)
        
        # Atualiza conversation updated_at
        conversation.save()
        
        return message

    @database_sync_to_async
    def serialize_message(self, message):
        """
        Serializa uma instância de mensagem em um dicionário para transmissão via WebSocket.
        Evita o uso do DRF Serializer para desacoplar do contexto de request.
        """
        sender_data = {
            'id': message.sender.id,
            'display_name': message.sender.get_full_name() or message.sender.email
        }

        conversation_data = {
            'id': str(message.conversation.id),
            'is_group': message.conversation.is_group
        }

        return {
            'id': str(message.id),
            'conversation': conversation_data,
            'sender': sender_data,
            'text': message.text,
            'created_at': message.created_at.isoformat(),
            # 'updated_at': message.updated_at.isoformat(), # Removido, pois o modelo Message não possui este campo
            # Adicione outros campos necessários
        }

    @database_sync_to_async
    def mark_as_delivered(self, message):
        """ Marca mensagem como entregue para participantes online. """
        participants = Participant.objects.filter(conversation_id=self.conversation_id)
        for participant in participants:
            if participant.user != self.user:  # Não marca para o remetente
                try:
                    status = MessageStatus.objects.get(
                        message=message,
                        participant=participant
                    )
                    if status.status == 'sent':
                        status.status = 'delivered'
                        status.delivered_at = timezone.now()
                        status.save()
                except MessageStatus.DoesNotExist:
                    pass

    @database_sync_to_async
    def mark_as_read(self, message_id):
        """ Marca mensagem como lida. """
        try:
            participant = Participant.objects.get(
                conversation_id=self.conversation_id,
                user=self.user
            )
            status = MessageStatus.objects.get(
                message_id=message_id,
                participant=participant
            )
            if status.status != 'read':
                status.status = 'read'
                status.read_at = timezone.now()
                status.save()
                
                # Atualiza última mensagem lida
                participant.last_read_message_id = message_id
                participant.save()
        except (Participant.DoesNotExist, MessageStatus.DoesNotExist):
            pass

    @database_sync_to_async
    def update_presence(self, status):
        """ Atualiza status de presença. """
        Presence.objects.update_or_create(
            user=self.user,
            defaults={
                'status': status,
                'last_seen': timezone.now()
            }
        )

    @database_sync_to_async
    def update_typing_status(self, is_typing):
        """ Atualiza status de digitação. """
        conversation = Conversation.objects.get(id=self.conversation_id)
        Presence.objects.update_or_create(
            user=self.user,
            defaults={
                'is_typing': is_typing,
                'typing_conversation': conversation if is_typing else None
            }
        )

    @database_sync_to_async
    def edit_message(self, message_id, new_text):
        """ Edita uma mensagem existente. """
        try:
            message = Message.objects.get(
                id=message_id,
                sender=self.user  # Só o remetente pode editar
            )
            message.text = new_text
            message.edited = True
            message.edited_at = timezone.now()
            message.save()
            return message
        except Message.DoesNotExist:
            return None

    @database_sync_to_async
    def delete_message(self, message_id):
        """ Exclui uma mensagem (soft delete). """
        try:
            message = Message.objects.get(
                id=message_id,
                sender=self.user  # Só o remetente pode excluir
            )
            message.text = "Esta mensagem foi excluída"
            message.attachments.all().delete()
            message.save()
            return True
        except Message.DoesNotExist:
            return False

    @database_sync_to_async
    def toggle_reaction(self, message_id, emoji):
        """ Adiciona ou remove reação. """
        try:
            message = Message.objects.get(id=message_id)
            # Remove reação existente do mesmo usuário e emoji
            Reaction.objects.filter(
                message=message,
                user=self.user,
                emoji=emoji
            ).delete()
            
            # Se não havia reação, adiciona uma nova
            if not Reaction.objects.filter(message=message, user=self.user, emoji=emoji).exists():
                reaction = Reaction.objects.create(
                    message=message,
                    user=self.user,
                    emoji=emoji
                )
                return reaction
            return None
        except Message.DoesNotExist:
            return None

class NotificationConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.user_notification_group_name = None

    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_anonymous:
            await self.close()
            return

        self.user_notification_group_name = f'notifications_{self.user.id}'
        await self.channel_layer.group_add(
            self.user_notification_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if self.user_notification_group_name:
            await self.channel_layer.group_discard(
                self.user_notification_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        # This consumer is for downstream notifications only.
        pass

    async def notification_new_message(self, event):
        """
        Handles the 'notification.new_message' event and sends it to the client.
        """
        await self.send(text_data=json.dumps({
            'type': 'notification.new_message',
            'message': event['message'],
            'conversation_id': event['conversation_id']
        }))