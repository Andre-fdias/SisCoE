# backend/efetivo/templatetags/count_filters.py
from django import template

register = template.Library()

@register.filter
def dict_get(dictionary, key):
    """
    Retorna o valor de uma chave em um dicionário.
    Uso: {{ my_dictionary|dict_get:key }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def sum_values(data_list, key_to_sum='militar_count'):
    """
    Soma os valores de uma chave específica em uma lista de dicionários.
    Uso: {{ my_list_of_dicts|sum_values:'my_key' }}
    """
    total = 0
    if isinstance(data_list, list):
        for item in data_list:
            if isinstance(item, dict) and key_to_sum in item:
                try:
                    total += int(item[key_to_sum])
                except (ValueError, TypeError):
                    # Ignora itens que não podem ser convertidos para int
                    pass
            # Se for um item direto (não um dicionário), tenta somar se for numérico
            elif isinstance(item, (int, float)):
                total += item
    return total