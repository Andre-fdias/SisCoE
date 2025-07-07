from django import forms
from .models import Documento

class DocumentoForm(forms.ModelForm):
    data_publicacao = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    data_documento = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'})) # Adicione esta linha
    class Meta:
        model = Documento
        fields = ['data_publicacao', 'data_documento', 'assunto', 'numero_documento', 'tipo', 'descricao', 'assinada_por'] # Adicione 'data_documento' aqui