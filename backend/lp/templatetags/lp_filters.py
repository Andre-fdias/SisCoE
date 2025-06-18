from django import template
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe
import json

register = template.Library()

@register.filter
def json_message_list(messages):
    """
    Converts a list of Django messages into a JSON string suitable for JavaScript.
    """
    message_list = []
    for message in messages:
        message_list.append({
            'message': message.message,
            'tags': message.tags,
            'level': message.level,
        })
    return mark_safe(json.dumps(message_list))

from django import template
from datetime import date, timedelta

@register.filter
def add_days(value, days):
    try:
        return value + timedelta(days=int(days))
    except (TypeError, ValueError):
        return value
    

@register.filter
def add(value, arg):
    try:
        return int(value) + int(arg)
    except (ValueError, TypeError):
        return value