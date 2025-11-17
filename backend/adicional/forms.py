# adicional/forms.py
from django import forms
from .models import Cadastro_adicional


class CadastroAdicionalForm(forms.ModelForm):
    class Meta:
        model = Cadastro_adicional
        fields = "__all__"  # Inclui todos os campos do modelo no formulário
        # Se quiser campos específicos:
        # fields = ['numero_adicional', 'data_ultimo_adicional', ...]
