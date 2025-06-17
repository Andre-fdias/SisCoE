# core/templatetags/messages_tag.py
from django import template
from django.contrib import messages

register = template.Library()

@register.inclusion_tag('messages_container.html', takes_context=True)
def military_messages(context):
    request = context['request']
    
    # Obtenha as mensagens da requisição. 
    # get_messages() consome as mensagens da storage, então elas não reaparecerão em recargas.
    storage = messages.get_messages(request)
    
    message_list = []
    for message in storage:
        message_list.append({
            'text': message.message, # O conteúdo da mensagem
            'tags': message.tags,    # As tags CSS (e.g., 'success', 'error')
            'level': message.level   # O nível numérico da mensagem (e.g., messages.SUCCESS)
        })
    
    # Adicionando um debug print para ver se as mensagens estão sendo coletadas
    # print(f"Mensagens coletadas pelo template tag: {message_list}")
    
    return {
        'messages': message_list,
        'request': request # Mantém o request no contexto, útil para outras coisas se precisar
    }