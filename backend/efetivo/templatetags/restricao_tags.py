from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def badge_rule(regra):
    colors = {
        '5.2.1': 'bg-blue-100 text-blue-800',
        '5.2.2': 'bg-green-100 text-green-800',
        '5.2.3': 'bg-yellow-100 text-yellow-800',
        '5.2.4': 'bg-purple-100 text-purple-800',
        '5.2.5': 'bg-red-100 text-red-800',
        '5.2.6': 'bg-indigo-100 text-indigo-800',
        '5.2.7': 'bg-teal-100 text-teal-800',
        '5.2.8': 'bg-orange-100 text-orange-800',
    }
    titles = {
        '5.2.1': 'Atividades operacionais com condições ou administrativas/apoio',
        '5.2.2': 'Somente atividades administrativas',
        '5.2.3': 'Trabalhar durante o dia em qualquer atividade',
        '5.2.4': 'Policiamento ostensivo ou administrativas/apoio',
        '5.2.5': 'Desarmado e atividades administrativas',
        '5.2.6': 'Atividades administrativas ou de apoio',
        '5.2.7': 'Sandálias pretas, sem atendimento ao público',
        '5.2.8': 'Policiamento ostensivo',
    }
    
    return mark_safe(
        f'<span class="{colors.get(regra, "bg-gray-100 text-gray-800")} px-2 py-1 rounded text-xs mr-1 mb-1" '
        f'title="{titles.get(regra, "")}">{regra}</span>'
    )