# backend/efetivo/templatetags/cpftags.py
from django import template
from backend.efetivo.models import Cadastro

register = template.Library()

@register.filter
def get_cadastros_by_cpf(cpf):
    """Retorna todos os cadastros com o CPF especificado"""
    return Cadastro.objects.filter(cpf=cpf)

@register.filter
def format_cpf(cpf):
    """Formata um CPF no formato XXX.XXX.XXX-XX"""
    if not cpf:
        return ""
    
    cpf_str = str(cpf).zfill(11)  # Garante que tenha 11 dígitos
    
    if len(cpf_str) == 11:
        return f"{cpf_str[:3]}.{cpf_str[3:6]}.{cpf_str[6:9]}-{cpf_str[9:]}"
    else:
        return cpf  # Retorna o original se não tiver 11 dígitos