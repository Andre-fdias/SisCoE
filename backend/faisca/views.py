import os
import json
import time
from datetime import datetime
from django.conf import settings
from django.apps import apps
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from markdown import markdown
from langchain_groq import ChatGroq
from .models import Chat, Conversation, FaiscaAgentConversation, FaiscaAgentChat, FaiscaAgentQueryLog
import pytz
from django.views.decorators.csrf import csrf_exempt
from .faisca_agent import FaiscaAgent 


# Configuração comum
os.environ['GROQ_API_KEY'] = settings.GROQ_API_KEY

##############################################################################
#                          FAISCA AI (Chatbot Geral)                         #
##############################################################################

FAISCA_AI_PROMPT = """
Você é o Faisca AI, assistente virtual da PMESP. Suas funções são:
1. Responder perguntas gerais sobre normas e procedimentos
2. Auxiliar com informações institucionais
3. Esclarecer dúvidas sobre regulamentos

Regras:
- Sempre trate o usuário como "Senhor" 
- Seja preciso e profissional
- Use markdown para formatação
"""

def get_local_time():
    return datetime.now(pytz.timezone('America/Sao_Paulo'))

def get_ai_chat_history(chats):
    return [('human' if i % 2 == 0 else 'ai', chat.message if i % 2 == 0 else chat.response)
            for i, chat in enumerate(chats)]

def ask_faisca_ai(context, message):
    model = ChatGroq(model='llama-3.2-90b-vision-preview')
    
    messages = [('system', FAISCA_AI_PROMPT)]
    messages.extend(context)
    messages.append(('human', message))
    
    response = model.invoke(messages)
    return markdown(response.content, output_format='html')

@login_required
def faisca_ai_chat(request):
    """View principal do Faisca AI"""
    current_conversation = Conversation.objects.filter(user=request.user).last()
    
    if request.method == 'POST':
        if not current_conversation:
            current_conversation = Conversation.objects.create(user=request.user)
        
        message = request.POST.get('message')
        if not message:
            return JsonResponse({'error': 'Mensagem vazia'}, status=400)
            
        context = get_ai_chat_history(current_conversation.chats.all())
        response = ask_faisca_ai(context, message)
        
        Chat.objects.create(
            conversation=current_conversation,
            message=message,
            response=response,
            created_at=get_local_time()
        )

        return JsonResponse({'message': message, 'response': response})
    
    chats = current_conversation.chats.all() if current_conversation else []
    return render(request, 'chatbot.html', {'chats': chats})


@login_required
def faisca_ai_history(request):
    """Histórico de conversas do Faisca AI"""
    conversations = Conversation.objects.filter(user=request.user).order_by('-created_at')
    history = [{
        'id': conv.id,
        'first_message': conv.chats.first().message if conv.chats.exists() else 'Nova conversa',
        'created_at': conv.created_at.astimezone(pytz.timezone('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M')
    } for conv in conversations]
    
    return JsonResponse({'history': history})

@login_required
def reset_faisca_ai_chat(request):
    """Reseta conversa do Faisca AI"""
    Conversation.objects.create(user=request.user)
    return JsonResponse({'status': 'success'})

##############################################################################
#                          FAISCA AGENT (Dados do Sistema)                   #
##############################################################################

FAISCA_AGENT_PROMPT = """
Você é o Faisca Agent, especialista nos dados do sistema PMESP. 

APLICATIVOS DISPONÍVEIS:
{apps}

REGRAS:
1. Só responda com base nos dados reais do sistema
2. Formate respostas em markdown
3. Se não souber, diga "Não encontrei esses dados no sistema"
""".format(apps=', '.join([app for app in settings.INSTALLED_APPS if app.startswith('backend.')]))

class AgentQueryValidator:
    @staticmethod
    def validate(query):
        if not query or len(query.strip()) < 3:
            raise ValidationError("Por favor, formule melhor sua pergunta")
        
        forbidden = ['receita', 'bolo', 'futebol']
        if any(word in query.lower() for word in forbidden):
            raise ValidationError("Assunto não permitido")

def execute_agent_command(command):
    try:
        AgentQueryValidator.validate(command)
        
        agent = ChatGroq(model='llama-3.2-90b-vision-preview')
        response = agent.invoke([
            ("system", FAISCA_AGENT_PROMPT),
            ("human", command)
        ])
        
        return mark_safe(markdown(response.content))
        
    except ValidationError as e:
        return mark_safe(markdown(f"**Aviso:** {str(e)}"))
    except Exception as e:
        return mark_safe(markdown("**Erro:** Falha ao processar solicitação"))



@csrf_exempt
def faisca_agent_chat(request):
    if request.method == 'POST':
        try:
            # Processa os dados da requisição
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                message = data.get('message', '').strip()
            else:
                message = request.POST.get('message', '').strip()
            
            if not message:
                return JsonResponse({'error': 'Mensagem vazia'}, status=400)
            
            # Processa a mensagem com o FaiscaAgent
            agent = FaiscaAgent(request.user)
            
            if 'relatório' in message.lower() or 'relatorio' in message.lower():
                response_text = agent.generate_report(message)
            else:
                result = agent.search_data(message)
                response_text = result if isinstance(result, str) else result['analysis']
            
            return JsonResponse({
                'success': True,
                'response': response_text,
                'original_message': message
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'error': 'Método não permitido'}, status=405)



@login_required
def faisca_agent_history(request):
    """Histórico do Faisca Agent"""
    conversations = FaiscaAgentConversation.objects.filter(user=request.user).order_by('-created_at')
    history = [{
        'id': conv.id,
        'first_message': conv.chats.first().message if conv.chats.exists() else 'Nova consulta',
        'created_at': conv.created_at.astimezone(pytz.timezone('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M')
    } for conv in conversations]
    
    return JsonResponse({'history': history})

@login_required
def reset_faisca_agent_chat(request):
    """Reseta conversa do Faisca Agent"""
    FaiscaAgentConversation.objects.filter(user=request.user, active=True).update(active=False)
    return JsonResponse({'status': 'success'})

    from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json

@method_decorator(csrf_exempt, name='dispatch')
class FaiscaAgentChatView(View):
    def post(self, request):
        try:
            # Verifica se é AJAX
            if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Requisição inválida'}, status=400)
            
            # Carrega os dados JSON
            try:
                data = json.loads(request.body)
                message = data.get('message', '').strip()
            except:
                message = request.POST.get('message', '').strip()
            
            if not message:
                return JsonResponse({'error': 'Mensagem vazia'}, status=400)
            
            # Aqui você processa a mensagem com o FaiscaAgent
            # Substitua pelo seu código real de processamento
            response_text = f"Você disse: {message}"
            
            return JsonResponse({
                'response': response_text
            }, status=200)
            
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)