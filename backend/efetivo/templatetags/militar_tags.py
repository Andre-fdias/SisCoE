from django import template

register = template.Library()

@register.simple_tag
def get_border_color(posto_grad):
    oficiais = ["Cel PM", "Ten Cel PM", "Maj PM", "CAP PM", 
               "1º Ten PM", "1º Ten QAPM", "2º Ten PM", 
               "2º Ten QAPM", "Asp OF PM"]
    suboficiais = ["Subten PM", "1º Sgt PM", "2º Sgt PM", "3º Sgt PM"]
    
    if posto_grad in oficiais:
        return "border-blue-500"
    elif posto_grad in suboficiais:
        return "border-red-500"
    return "border-gray-900"