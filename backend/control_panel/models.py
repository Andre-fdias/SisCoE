# backend/control_panel/models.py
from django.db import models
from django.conf import settings  # Importação importante
from django.utils import timezone

class SystemSettings(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.key
    
    class Meta:
        verbose_name = "Configuração do Sistema"
        verbose_name_plural = "Configurações do Sistema"

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('create', 'Criar'),
        ('update', 'Atualizar'),
        ('delete', 'Deletar'),
        ('view', 'Visualizar'),
        ('backup', 'Backup'),
        ('restart', 'Reiniciar'),
    ]
    
    STATUS_CHOICES = [
        ('success', 'Sucesso'),
        ('error', 'Erro'),
        ('warning', 'Aviso'),
    ]
    
    timestamp = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)  # ← CORRIGIDO
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    resource = models.CharField(max_length=100)
    details = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.resource}"
    
    class Meta:
        verbose_name = "Log de Auditoria"
        verbose_name_plural = "Logs de Auditoria"
        ordering = ['-timestamp']

class BackupConfig(models.Model):
    SCHEDULE_CHOICES = [
        ('daily', 'Diário'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensal'),
        ('manual', 'Manual'),
    ]
    
    name = models.CharField(max_length=100)
    enabled = models.BooleanField(default=True)
    schedule = models.CharField(max_length=10, choices=SCHEDULE_CHOICES, default='daily')
    backup_path = models.CharField(max_length=255, default='/backups/')
    retain_days = models.IntegerField(default=30)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Configuração de Backup"
        verbose_name_plural = "Configurações de Backup"

class UsefulLink(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nome")
    url = models.URLField(max_length=2000, verbose_name="URL")
    icon = models.CharField(max_length=50, blank=True, help_text="Ex: fas fa-link, fab fa-docker, ou um emoji 🐳", verbose_name="Ícone")
    description = models.CharField(max_length=255, blank=True, verbose_name="Descrição")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordem")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Link Útil"
        verbose_name_plural = "Links Úteis"
        ordering = ['order', 'name']

        