from django import forms
from .models import CalculoMilitar


class CalculoMilitarForm(forms.ModelForm):
    class Meta:
        model = CalculoMilitar
        fields = [
            "data_admissao",
            "tempo_ffaa_pm_cbm",
            "tempo_inss_outros",
            "afastamentos",
        ]
        widgets = {
            "data_admissao": forms.DateInput(attrs={"type": "date"}),
        }
