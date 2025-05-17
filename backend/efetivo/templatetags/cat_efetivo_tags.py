from django import template
from ..models import CatEfetivo

register = template.Library()

@register.simple_tag
def get_restricao_fields():
    """Returns all fields that start with 'restricao_'"""
    return [field for field in CatEfetivo._meta.get_fields() 
           if field.name.startswith('restricao_')]
