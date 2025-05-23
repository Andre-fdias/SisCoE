# backend/cursos/forms.py

from django import forms
from .models import MilitarMedalha, Medalha, Cadastro, TipoMedalha
from django.forms import ModelForm, DateInput

class MilitarMedalhaForm(ModelForm):
    class Meta:
        model = MilitarMedalha
        fields = ['cadastro', 'medalha', 'data_concessao', 'observacoes']
        widgets = {
            'data_concessao': DateInput(attrs={'type': 'date'}),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cadastro'].queryset = Cadastro.objects.all().order_by('nome_de_guerra')
        self.fields['medalha'].queryset = Medalha.objects.all().order_by('honraria')
        self.fields['cadastro'].widget.attrs.update({'class': 'w-full pl-4 pr-10 py-3.5 rounded-xl border border-gray-200 bg-white/70 shadow-xs focus:ring-2 focus:ring-indigo-200 focus:border-indigo-500 transition-all duration-200 hover:border-gray-300 text-gray-700 font-medium appearance-none'})
        self.fields['medalha'].widget.attrs.update({'class': 'w-full pl-4 pr-10 py-3.5 rounded-xl border border-gray-200 bg-white/70 shadow-xs focus:ring-2 focus:ring-indigo-200 focus:border-indigo-500 transition-all duration-200 hover:border-gray-300 text-gray-700 font-medium appearance-none medalha-select-dynamic'})


class MedalhaSearchForm(forms.Form):
    nome = forms.CharField(
        label='Nome da Medalha',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Pesquisar medalha...'})
    )
    
    tipo = forms.ChoiceField(
        label='Tipo de Medalha',
        required=False,
        choices=[('', 'Todos')] + list(TipoMedalha.TIPO_CHOICES)
    )
    
    def search(self):
        queryset = Medalha.objects.all()
        nome = self.cleaned_data.get('nome')
        tipo = self.cleaned_data.get('tipo')
        
        if nome:
            queryset = queryset.filter(honraria__icontains=nome)
        if tipo:
            queryset = queryset.filter(tipo__nome=tipo)
        
        return queryset.order_by('honraria')

class MedalhaForm(ModelForm): # Este é o formulário para a Medalha em si
    class Meta:
        model = Medalha
        fields = ['honraria', 'entidade_concedente', 'ordem', 'tipo'] # Removido 'observacoes' aqui
        widgets = {
            'honraria': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Nome da Honraria'}),
            'entidade_concedente': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Entidade Concedente'}),
            'ordem': forms.Select(attrs={'class': 'input-field'}),
            'tipo': forms.Select(attrs={'class': 'input-field'}),
        }