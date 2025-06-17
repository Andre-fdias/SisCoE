# core/middleware.py
import json
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin

class JSONMessagesMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        # Se for uma resposta JSON e houver mensagens
        if (response.headers.get('Content-Type') == 'application/json' and 
            hasattr(request, '_messages') and 
            request._messages):
            
            try:
                content = json.loads(response.content)
            except json.JSONDecodeError:
                return response
                
            # Adicionar mensagens à resposta JSON
            message_list = []
            for message in messages.get_messages(request):
                message_list.append({
                    'text': message.message,
                    'level': message.level,
                    'tags': message.tags
                })
            
            if 'messages' not in content:
                content['messages'] = []
            content['messages'].extend(message_list)
            
            response.content = json.dumps(content)
            
        return response