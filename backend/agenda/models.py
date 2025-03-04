from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


# models.py
class Lembrete(models.Model):
    VISIBILIDADE_CHOICES = [
        ('privado', 'Privado'),
        ('publico', 'Público'),
    ]
    
    titulo = models.CharField(max_length=200)
    assunto = models.CharField(max_length=200)  # Novo campo
    descricao = models.TextField()
    data = models.DateTimeField()
    local = models.CharField(max_length=200)  # Novo campo
    tipo = models.CharField(max_length=50, default='Lembrete')
    cor = models.CharField(max_length=7, default='#3788d8')
    visibilidade = models.CharField(max_length=50, choices=VISIBILIDADE_CHOICES, default='privado')  # Modificado
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    
class Tarefa(models.Model):
    VISIBILIDADE_CHOICES = [
        ('privado', 'Privado'),
        ('publico', 'Público'),
    ]
    
    titulo = models.CharField(max_length=200)
    assunto = models.CharField(max_length=200)  # Novo campo
    descricao = models.TextField()
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField()
    local = models.CharField(max_length=200)  # Novo campo
    tipo = models.CharField(max_length=50, default='Tarefa')
    cor = models.CharField(max_length=7, default='#3788d8')
    visibilidade = models.CharField(max_length=50, choices=VISIBILIDADE_CHOICES, default='privado')  # Modificado
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    