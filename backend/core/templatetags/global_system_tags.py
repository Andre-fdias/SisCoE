# /home/andre/Repositorio/SisCoE/backend/core/templatetags/global_system_tags.py

from django import template
from django.conf import settings

register = template.Library()


@register.inclusion_tag("includes/global_system_scripts.html", takes_context=True)
def global_system_scripts(context):
    """
    Template tag para incluir os scripts do sistema global automaticamente
    """
    enabled = getattr(settings, "GLOBAL_SYSTEM_CONFIG", {}).get("ENABLED", True)

    return {
        "global_system_enabled": enabled,
        "user_authenticated": context.get("user_authenticated", False),
        "SESSION_IDLE_TIMEOUT": context.get("SESSION_IDLE_TIMEOUT", 1800),
        "SESSION_WARNING_TIME": context.get("SESSION_WARNING_TIME", 300),
    }


@register.simple_tag(takes_context=True)
def global_system_meta(context):
    """
    Template tag para incluir meta tags do sistema global
    """
    user = context.get("user")
    return f"""
    <meta name="user-authenticated" content="{user.is_authenticated if user else 'false'}">
    <meta name="session-timeout" content="{context.get('SESSION_IDLE_TIMEOUT', 1800)}">
    <meta name="session-warning-time" content="{context.get('SESSION_WARNING_TIME', 300)}">
    """
