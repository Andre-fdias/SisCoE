# core/templatetags/cpftags.py
from django import template
from backend.efetivo.models import Cadastro

register = template.Library()

# Alterado para register.filter (em vez de simple_tag)
@register.filter
def get_cadastros_by_cpf(cpf):
    """Retorna todos os cadastros com o CPF especificado"""
    return Cadastro.objects.filter(cpf=cpf)