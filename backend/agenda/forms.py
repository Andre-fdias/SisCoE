from django import forms
from .models import Lembrete, Tarefa


class LembreteForm(forms.ModelForm):
    class Meta:
        model = Lembrete
        fields = ["titulo", "descricao", "data", "cor"]
        widgets = {
            "data": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"},
            ),
            "cor": forms.TextInput(
                attrs={"type": "color", "class": "form-control form-control-color"},
            ),
        }


class TarefaForm(forms.ModelForm):
    class Meta:
        model = Tarefa
        fields = [
            "titulo",
            "descricao",
            "data_inicio",
            "data_fim",
            "cor",
        ]
        widgets = {
            "data_inicio": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"},
            ),
            "data_fim": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"},
            ),
            "cor": forms.TextInput(
                attrs={"type": "color", "class": "form-control form-control-color"},
            ),
        }
