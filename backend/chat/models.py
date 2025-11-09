from django.db import models
from django.conf import settings
import uuid
from .encryption import encrypt_message, decrypt_message

class Conversation(models.Model):
    """
    Representa uma conversa, que pode ser um chat privado (1:1) ou em grupo.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, blank=True, null=True, help_text="Nome do grupo, se aplicável")
    is_group = models.BooleanField(default=False, help_text="Define se a conversa é em grupo")
    photo = models.ImageField(upload_to='chat_photos/%Y/%m/%d/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-updated_at',)
        indexes = [
            models.Index(fields=['updated_at']),
        ]

    def __str__(self):
        if self.name:
            return self.name
        # Para conversas 1:1, mostra os nomes dos participantes
        participants = self.participants.all()[:2]
        if len(participants) == 2:
            names = [p.user.get_full_name() or p.user.email for p in participants]
            return " & ".join(names)
        return str(self.id)

class Participant(models.Model):
    """
    Tabela de junção para relacionar usuários a conversas.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations")
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="participants")
    is_admin = models.BooleanField(default=False)
    muted_until = models.DateTimeField(null=True, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read_message = models.ForeignKey('Message', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('user', 'conversation')
        ordering = ('-joined_at',)

    def __str__(self):
        return f"{(self.user.get_full_name() or self.user.email)} in {self.conversation}"

class Message(models.Model):
    """
    Representa uma única mensagem dentro de uma conversa.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages")
    text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    edited = models.BooleanField(default=False)
    parent_message = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name="replies")
    quoted_text = models.TextField(blank=True, null=True, help_text="Snapshot do texto da mensagem respondida")

    def save(self, *args, **kwargs):
        """Sobrescreve o método save para criptografar a mensagem."""
        if self.text:
            self.text = encrypt_message(self.text)
        super().save(*args, **kwargs)

    @property
    def decrypted_text(self):
        """Retorna o texto da mensagem descriptografado."""
        return decrypt_message(self.text)

    class Meta:
        ordering = ('created_at',)
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
        ]

    def __str__(self):
        return f"Message from {(self.sender.get_full_name() or self.sender.email)} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class Attachment(models.Model):
    """
    Armazena arquivos anexados a uma mensagem (imagens, áudios, documentos).
    """
    ATTACHMENT_TYPES = (
        ('image', 'Imagem'),
        ('video', 'Vídeo'),
        ('audio', 'Áudio'),
        ('document', 'Documento'),
        ('voice_note', 'Mensagem de Voz'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to='chat_attachments/%Y/%m/%d/')
    file_type = models.CharField(max_length=20, choices=ATTACHMENT_TYPES)
    thumbnail = models.ImageField(upload_to='chat_thumbnails/%Y/%m/%d/', blank=True, null=True)
    file_size = models.BigIntegerField(default=0)
    duration = models.IntegerField(default=0, help_text="Duração em segundos para áudio/vídeo")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('uploaded_at',)

    def __str__(self):
        return f"Attachment {self.file_type} for message {self.message.id}"

class MessageStatus(models.Model):
    """
    Rastreia o status de uma mensagem para cada participante (entregue, lido).
    """
    STATUS_CHOICES = (
        ('sent', 'Enviado'),
        ('delivered', 'Entregue'),
        ('read', 'Lido'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="statuses")
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name="message_statuses")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='sent')
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('message', 'participant')
        ordering = ('-timestamp',)

    def __str__(self):
        return f"{self.message.id} - {(self.participant.user.get_full_name() or self.participant.user.email)}: {self.get_status_display()}"

class Reaction(models.Model):
    """
    Reações emoji para mensagens.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="reactions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    emoji = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('message', 'user', 'emoji')
        ordering = ('created_at',)

    def __str__(self):
        return f"{self.emoji} by {(self.user.get_full_name() or self.user.email)}"

class Presence(models.Model):
    """
    Rastreia presença online dos usuários.
    """
    STATUS_CHOICES = (
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('away', 'Ausente'),
    )
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='offline')
    last_seen = models.DateTimeField(auto_now=True)
    is_typing = models.BooleanField(default=False)
    typing_conversation = models.ForeignKey(Conversation, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ('-last_seen',)

    def __str__(self):
        return f"{(self.user.get_full_name() or self.user.email)} - {self.status}"