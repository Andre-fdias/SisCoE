from django.contrib.auth import get_user_model
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class Lembrete(models.Model):
    """
    Modelo para representar um lembrete.
    Campos:
    - titulo: Título do lembrete.
    - descricao: Descrição detalhada do lembrete.
    - data: Data e hora do lembrete.
    - tipo: Tipo do evento (padrão: 'Lembrete').
    - cor: Cor associada ao lembrete (padrão: azul).
    - user: Usuário associado ao lembrete.
    """
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    data = models.DateTimeField()
    tipo = models.CharField(max_length=50, default='Lembrete')
    cor = models.CharField(max_length=7, default='#3788d8')
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.titulo

class Tarefa(models.Model):
    """
    Modelo para representar uma tarefa.
    Campos:
    - titulo: Título da tarefa.
    - descricao: Descrição detalhada da tarefa.
    - data_inicio: Data e hora de início da tarefa.
    - data_fim: Data e hora de término da tarefa.
    - tipo: Tipo do evento (padrão: 'Tarefa').
    - cor: Cor associada à tarefa (padrão: azul).
    - user: Usuário associado à tarefa.
    """
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField()
    tipo = models.CharField(max_length=50, default='Tarefa')
    cor = models.CharField(max_length=7, default='#3788d8')
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.titulo

    def clean(self):
        """
        Valida se a data de término não é anterior à data de início.
        """
        super().clean()  # Chama o método clean da classe pai

        if self.data_fim < self.data_inicio:
            raise ValidationError(_('A data de término não pode ser anterior à data de início.'))