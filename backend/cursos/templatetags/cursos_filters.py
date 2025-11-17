from django import template

register = template.Library()


@register.filter(name="get_item")
def get_item(dictionary, key):
    """
    Permite acessar um item de um dicionário por chave em templates Django.
    Exemplo de uso: {{ my_dict|get_item:my_key }}
    """
    return dictionary.get(key)
