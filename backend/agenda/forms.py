from django import forms
from .models import Lembrete, Tarefa

# forms.py
class LembreteForm(forms.ModelForm):
    class Meta:
        model = Lembrete
        fields = ['titulo', 'assunto', 'descricao', 'data', 'local', 'visibilidade', 'cor']
        widgets = {
            'visibilidade': forms.RadioSelect(choices=Lembrete.VISIBILIDADE_CHOICES)
        }

class TarefaForm(forms.ModelForm):
    class Meta:
        model = Tarefa
        fields = ['titulo', 'assunto', 'descricao', 'data_inicio', 'data_fim', 'local', 'visibilidade', 'cor']
        widgets = {
            'visibilidade': forms.RadioSelect(choices=Tarefa.VISIBILIDADE_CHOICES)
        }