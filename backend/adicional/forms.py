from django import forms
from .models import Cadastro_adicional, LP

class AdicionalLPForm(forms.ModelForm):
    """
    Formulário combinado para Adicional e LP.
    """
    n_bloco_adicional = forms.ChoiceField(choices=[(i, f'{i:02d}') for i in range(1, 9)], label="Nº Bloco Adicional")
    data_ultimo_adicional = forms.DateField(label="Data Último Adicional", widget=forms.DateInput(attrs={'type': 'date'}))
    n_bloco_lp = forms.ChoiceField(choices=[(i, f'{i:02d}') for i in range(1, 9)], label="Nº Bloco LP")
    data_ultimo_lp = forms.DateField(label="Data Último LP", widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Cadastro_adicional
        fields = ['n_bloco_adicional', 'data_ultimo_adicional'] #declara os campos do form
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remova os campos que não devem estar no formulário de criação
        del self.fields['numero_adicional']
        del self.fields['proximo_adicional']
        del self.fields['mes_proximo_adicional']
        del self.fields['ano_proximo_adicional']
        del self.fields['numero_prox_adicional']
        del self.fields['situacao_adicional']
        del self.fields['status_adicional']
        del self.fields['dias_desconto_adicional']
        
        del self.fields['data_concessao_adicional']
        del self.fields['bol_g_pm_adicional']
        del self.fields['data_publicacao_adicional']
        del self.fields['sexta_parte']

        # Adicione os campos de LP ao formulário
        self.fields['n_bloco_lp'] = forms.ChoiceField(choices=[(i, f'{i:02d}') for i in range(1, 9)], label="Nº Bloco LP")
        self.fields['data_ultimo_lp'] = forms.DateField(label="Data Último LP", widget=forms.DateInput(attrs={'type': 'date'}))
        
        # Remova os campos de LP que não devem estar no formulário de criação
        