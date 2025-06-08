# C:\Users\30991492846\Documents\GitHub\SisCoE-main\backend\efetivo\templatetags\cat_efetivo_tags.py

from django import template
from ..models import CatEfetivo # Importe o modelo CatEfetivo

register = template.Library()

@register.simple_tag
def get_restricao_fields():
    """Returns all fields that start with 'restricao_'"""
    return [field for field in CatEfetivo._meta.get_fields() 
            if field.name.startswith('restricao_')]

@register.simple_tag
def get_cat_efetivo_tipo_choices():
    """Returns the choices for CatEfetivo type field."""
    return CatEfetivo.TIPO_CHOICES