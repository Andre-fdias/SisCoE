# views.py
from django.shortcuts import get_object_or_404
import os
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from langchain_groq import ChatGroq
from markdown import markdown
from backend.faisca.models import Chat, Conversation
from datetime import datetime
import pytz

os.environ['GROQ_API_KEY'] = settings.GROQ_API_KEY

def get_chat_history(chats):
    """Obtém o histórico apenas da conversa atual"""
    return [('human' if i % 2 == 0 else 'ai', chat.message if i % 2 == 0 else chat.response)
            for i, chat in enumerate(chats)]

def ask_ai(context, message):
    """Função de consulta à IA com histórico controlado"""
    model = ChatGroq(model='llama-3.2-90b-vision-preview')
    
    messages = [
        ('system', 
         'Você é Faisca AI, um assistente virtual especializado em responder dúvidas sobre Normas e Regras da PMESP e CB. '
         'Forneça informações precisas em markdown. Mantenha o contexto da conversa atual. '
         'Sempre trate o usuário como "Senhor" de forma educada e profissional.'
         )
    ]
    
    # Adiciona apenas o histórico da conversa atual
    messages.extend(context)
    
    # Adiciona a nova mensagem do usuário
    messages.append(('human', message))
    
    response = model.invoke(messages)
    return markdown(response.content, output_format='html')

@login_required
def chatbot(request):
    """View principal do chatbot com gestão de contexto"""
    current_conversation = Conversation.objects.filter(user=request.user).last()
    
    if request.method == 'POST':
        # Cria nova conversa se não existir
        if not current_conversation:
            current_conversation = Conversation.objects.create(user=request.user)
        
        message = request.POST.get('message')
        context = get_chat_history(current_conversation.chats.all())
        response = ask_ai(context=context, message=message)
        
        # Salva apenas na conversa atual
        Chat.objects.create(
            conversation=current_conversation,
            message=message,
            response=response,
            created_at=get_local_time()
        )

        return JsonResponse({'message': message, 'response': response})
    
    # Carrega histórico apenas da conversa atual
    chats = current_conversation.chats.all() if current_conversation else []
    return render(request, 'chatbot.html', {'chats': chats})

def get_local_time():
    """Obtém horário local formatado"""
    return datetime.now(pytz.timezone('America/Sao_Paulo'))

@login_required
def chat_history(request):
    """Histórico de conversas anteriores (sem misturar com atual)"""
    conversations = Conversation.objects.filter(user=request.user).order_by('-created_at')
    history = [{
        'id': conv.id,
        'first_message': conv.chats.first().message if conv.chats.exists() else 'Nova conversa',
        'created_at': conv.created_at.astimezone(pytz.timezone('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M')
    } for conv in conversations]
    
    return JsonResponse({'history': history})

@login_required
def reset_chat(request):
    """Cria nova conversa vazia sem apagar o histórico"""
    Conversation.objects.create(user=request.user)
    return JsonResponse({'status': 'success', 'new_conversation': True})


@login_required
def system_agent(request):
    """Endpoint para o agente de sistema síncrono"""
    if request.method == 'POST':
        if not request.user.has_perm('faisca.use_system_agent'):
            return JsonResponse({'error': 'Permissão negada'}, status=403)
            
        comando = request.POST.get('comando')
        agent = SistemaAgent(request.user)
        resposta = agent.executar_comando(comando)
        
        return JsonResponse({
            'comando': comando,
            'resposta': resposta,
            'timestamp': get_local_time().isoformat()
        })
    
    return JsonResponse({'error': 'Método não permitido'}, status=405)


# backend/faisca/views.py
@login_required
def faisca_agent_chat(request):
    """View principal do Faisca Agent"""
    current_conversation = FaiscaAgentConversation.objects.filter(user=request.user, active=True).first()
    
    if request.method == 'POST':
        if not current_conversation:
            current_conversation = FaiscaAgentConversation.objects.create(user=request.user)
        
        message = request.POST.get('message')
        response = execute_faisca_agent_command(message)
        
        FaiscaAgentChat.objects.create(
            conversation=current_conversation,
            message=message,
            response=response
        )

        return JsonResponse({'message': message, 'response': response})
    
    return JsonResponse({'error': 'Método não permitido'}, status=405)

def execute_faisca_agent_command(command):
    """Executa comandos no Faisca Agent"""
    agent = ChatGroq(model='llama-3.2-90b-vision-preview')
    
    prompt = f"""
    [SYSTEM]
    Você é o Faisca Agent, especialista em análise de dados e operações do sistema.
    Forneça respostas técnicas e estruturadas usando markdown.
    Mantenha o foco em dados do sistema e operações.
    
    [COMANDO]
    {command}
    """
    
    response = agent.invoke(prompt)
    return markdown(response.content, output_format='html')

@login_required
def reset_faisca_agent_chat(request):
    """Reseta a conversa do Faisca Agent"""
    FaiscaAgentConversation.objects.filter(user=request.user, active=True).update(active=False)
    return JsonResponse({'status': 'success'})