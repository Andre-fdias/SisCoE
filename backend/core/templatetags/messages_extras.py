# core/templatetags/messages_extras.py
from django import template

register = template.Library()


@register.inclusion_tag("messages_container.html")
def military_messages():
    return {}
