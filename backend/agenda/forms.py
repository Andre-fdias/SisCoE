
from django import forms
from .models import Lembrete, Tarefa

class LembreteForm(forms.ModelForm):
    class Meta:
        model = Lembrete
        fields = ['titulo', 'descricao', 'data', 'cor']  # Remova 'visibilidade'

class TarefaForm(forms.ModelForm):
    class Meta:
        model = Tarefa
        fields = ['titulo', 'descricao', 'data_inicio', 'data_fim', 'cor']  # Remova 'visibilidade'

    def clean(self):
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get('data_inicio')
        data_fim = cleaned_data.get('data_fim')

        if data_inicio is None or data_fim is None:
            raise forms.ValidationError("As datas de início e término são obrigatórias.")

        if data_fim < data_inicio:
            raise forms.ValidationError("A data de término não pode ser anterior à data de início.")

        return cleaned_data