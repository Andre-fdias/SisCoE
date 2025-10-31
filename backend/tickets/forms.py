from django import forms
from .models import Chamado, Anexo, Categoria, Comentario
from backend.accounts.models import User

class ChamadoForm(forms.ModelForm):
    anexos = forms.FileField(required=False, label='Anexos')

    class Meta:
        model = Chamado
        fields = [
            'solicitante_nome', 'solicitante_email', 'solicitante_cpf', 'solicitante_telefone',
            'categoria', 'assunto', 'descricao', 'anexos'
        ]
        widgets = {
            'solicitante_nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Seu nome completo'}),
            'solicitante_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'seu@email.com'}),
            'solicitante_cpf': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apenas números'}),
            'solicitante_telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(XX) XXXXX-XXXX'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'assunto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Um breve resumo do problema'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Descreva o problema em detalhes'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].queryset = Categoria.objects.all()
        self.fields['categoria'].empty_label = "Selecione uma categoria"

class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ['texto', 'privado']
        widgets = {
            'texto': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Adicione seu comentário...'}),
            'privado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'texto': 'Novo Comentário',
            'privado': 'Marcar como comentário privado (visível apenas para a equipe)'
        }

class UpdateStatusForm(forms.ModelForm):
    class Meta:
        model = Chamado
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'})
        }

class AssignTecnicoForm(forms.ModelForm):
    class Meta:
        model = Chamado
        fields = ['tecnico_responsavel']
        widgets = {
            'tecnico_responsavel': forms.Select(attrs={'class': 'form-select'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tecnico_responsavel'].queryset = User.objects.filter(is_staff=True)
        self.fields['tecnico_responsavel'].label = "Atribuir Técnico"
