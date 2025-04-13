# backend/faisca/views.py
import os
import json
import locale
from datetime import datetime
import pytz
from markdown import markdown
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from langchain_groq import ChatGroq
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

from .models import Conversation, Chat, DocumentoInterno

locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

# Configuração comum
os.environ['GROQ_API_KEY'] = settings.GROQ_API_KEY

##############################################################################
#                               FAISCA AI (Chatbot Geral)                     #
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
    """View principal do Faisca AI (Geral)"""
    current_conversation = Conversation.objects.filter(user=request.user, tipo='geral').last()

    if request.method == 'POST':
        if not current_conversation:
            current_conversation = Conversation.objects.create(user=request.user, tipo='geral')

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
    return render(request, 'chatbot.html', {'chats': chats, 'active_agent': 'faisca_ia'})


@login_required
def faisca_ai_history(request):
    """Histórico de conversas do Faisca AI (Geral)"""
    conversations = Conversation.objects.filter(user=request.user, tipo='geral').order_by('-created_at')
    history = [{
        'id': conv.id,
        'first_message': conv.chats.first().message if conv.chats.exists() else 'Nova conversa',
        'created_at': conv.created_at.astimezone(pytz.timezone('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M')
    } for conv in conversations]

    return JsonResponse({'history': history})

@login_required
def reset_faisca_ai_chat(request):
    """Reseta conversa do Faisca AI (Geral)"""
    Conversation.objects.create(user=request.user, tipo='geral')
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

##############################################################################
#                               FAISCA IN AI (Agente Interno)                 #
##############################################################################

class FaiscaInAiAgent:
    def __init__(self, user):
        self.user = user
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index_path = os.path.join(settings.BASE_DIR, 'backend', 'faisca', 'indices', f'indice_interno_{user.id}.bin')
        self.index_to_id_map_path = os.path.join(settings.BASE_DIR, 'backend', 'faisca', 'indices', f'indice_interno_map_{user.id}.json')
        self.groq_llm = ChatGroq(model='llama-3.2-90b-vision-preview')
        self._carregar_indice()

    def _extrair_texto_pdf(self, arquivo_path):
        """Extrai texto de um arquivo PDF."""
        texto = ""
        try:
            with open(arquivo_path, 'rb') as pdf_file:
                reader = PdfReader(pdf_file)
                for page in reader.pages:
                    texto += page.extract_text() + "\n"
        except Exception as e:
            print(f"Erro ao extrair texto de {arquivo_path}: {e}")
        return texto

    def _criar_indice(self, chunk_size=500, chunk_overlap=100, nlist=100): # nlist: número de clusters
        """Cria o índice vetorial otimizado com IndexIVFFlat."""

        documentos = DocumentoInterno.objects.filter(user=self.user)
        textos = []  # Linha 270 (corretamente indentada)
        doc_ids = []
        all_chunks = [] # Para mapear o índice para o chunk original

        for doc in documentos:
            texto_completo = self._extrair_texto_pdf(doc.arquivo.path)
            if texto_completo:
                chunks = self._chunk_texto(texto_completo, chunk_size, chunk_overlap) # Use sua função de chunking
                textos.extend(chunks)
                doc_ids.extend([doc.id] * len(chunks))
                all_chunks.extend(chunks)

        if not textos:
            self.index = None
            self.index_to_id_map = {}
            self.chunks_armazenados = []
            return

        embeddings = self.embedding_model.encode(textos)
        dimension = embeddings.shape[1]
        quantizer = faiss.IndexFlatL2(dimension)  # Quantizador para o índice IVFFlat
        self.index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
        self.index.train(embeddings)  # Treina o índice
        self.index.add(embeddings)
        self.index_to_id_map = {i: i for i in range(len(textos))} # Mapeia o índice FAISS para o índice da lista de chunks
        self.chunks_armazenados = all_chunks # Armazena os chunks para recuperação eficiente

        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        faiss.write_index(self.index, self.index_path)
        with open(self.index_to_id_map_path, 'w') as f:
            json.dump(self.index_to_id_map, f)
        with open(os.path.join(settings.BASE_DIR, 'backend', 'faisca', 'indices', f'chunks_interno_{self.user.id}.json'), 'w') as f:
            json.dump(self.chunks_armazenados, f)



    def _carregar_indice(self):
        """Carrega o índice vetorial existente do usuário."""
        if os.path.exists(self.index_path) and os.path.exists(self.index_to_id_map_path) and os.path.exists(os.path.join(settings.BASE_DIR, 'backend', 'faisca', 'indices', f'chunks_interno_{self.user.id}.json')):
            self.index = faiss.read_index(self.index_path)
            with open(self.index_to_id_map_path, 'r') as f:
                self.index_to_id_map = json.load(f)
            with open(os.path.join(settings.BASE_DIR, 'backend', 'faisca', 'indices', f'chunks_interno_{self.user.id}.json'), 'r') as f:
                self.chunks_armazenados = json.load(f)
        else:
            self.index = None
            self.index_to_id_map = {}
            self.chunks_armazenados = []

    def _buscar_documentos_relevantes(self, query, k=3):
        """Busca os documentos internos mais relevantes para a query."""
        if self.index is None:
            return []

        query_embedding = self.embedding_model.encode(query)
        D, I = self.index.search(np.array([query_embedding]), k)
        relevant_doc_ids = [self.index_to_id_map.get(i) for i in I[0] if self.index_to_id_map.get(i) is not None]
        return DocumentoInterno.objects.filter(id__in=relevant_doc_ids, user=self.user)

    def perguntar(self, query, top_k=3, nprobe=5):
        """Realiza a busca nos chunks relevantes com IndexIVFFlat."""
        if self.index is None:
            return "Nenhum documento interno indexado."

        self.index.nprobe = nprobe  # Define o número de clusters a serem pesquisados
        query_embedding = self.embedding_model.encode(query)
        D, I = self.index.search(np.array([query_embedding]), top_k)

        context = ""
        for index in I[0]:
            if index < len(self.chunks_armazenados):
                context += self.chunks_armazenados[index] + "\n\n"

        prompt = f"""Você é o Faisca IN AI, um assistente virtual especializado em responder perguntas com base nos documentos internos da PMESP fornecidos.
        Use o seguinte contexto para responder à pergunta:
        {context}
        Pergunta: {query}
        Resposta:"""

        response = self.groq_llm.invoke([("human", prompt)])
        return markdown(response.content, output_format='html')

    def _chunk_texto(self, texto, chunk_size=500, chunk_overlap=100):
        """Implemente sua lógica de chunking aqui (por tamanho fixo com overlap como exemplo)."""
        chunks = []
        for i in range(0, len(texto), chunk_size - chunk_overlap):
            chunk = texto[i:i + chunk_size].strip()
            if chunk:
                chunks.append(chunk)
        return chunks

@csrf_exempt
@login_required
def faisca_in_ai_chat(request):
    """View principal do Faisca IN AI (Agente Interno)"""
    current_conversation = Conversation.objects.filter(user=request.user, tipo='interno').last()

    if request.method == 'POST':
        if not current_conversation:
            current_conversation = Conversation.objects.create(user=request.user, tipo='interno')

        message = request.POST.get('message')
        if not message:
            return JsonResponse({'error': 'Mensagem vazia'}, status=400)

        faisca_in_ai_agent = FaiscaInAiAgent(request.user)
        response = faisca_in_ai_agent.perguntar(message)

        Chat.objects.create(
            conversation=current_conversation,
            message=message,
            response=response,
            created_at=get_local_time()
        )

        return JsonResponse({'message': message, 'response': response})

    chats = current_conversation.chats.all() if current_conversation else []
    return render(request, 'chatbot.html', {'chats': chats, 'active_agent': 'faisca_in_ai'})

@login_required
def faisca_in_ai_history(request):
    """Histórico de conversas do Faisca IN AI (Agente Interno)"""
    conversations = Conversation.objects.filter(user=request.user, tipo='interno').order_by('-created_at')
    history = [{
        'id': conv.id,
        'first_message': conv.chats.first().message if conv.chats.exists() else 'Nova conversa',
        'created_at': conv.created_at.astimezone(pytz.timezone('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M')
    } for conv in conversations]

    return JsonResponse({'history': history})

@login_required
def reset_faisca_in_ai_chat(request):
    """Reseta conversa do Faisca IN AI (Agente Interno)"""
    Conversation.objects.create(user=request.user, tipo='interno')
    return JsonResponse({'status': 'success'})

@login_required
def upload_documento_interno(request):
    """View para permitir o upload de documentos internos."""
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        arquivo = request.FILES.get('arquivo')
        if titulo and arquivo:
            DocumentoInterno.objects.create(user=request.user, titulo=titulo, arquivo=arquivo)
            faisca_in_ai_agent = FaiscaInAiAgent(request.user)
            faisca_in_ai_agent._criar_indice() # Recria o índice após o upload
            return JsonResponse({'success': True, 'message': 'Documento enviado e índice atualizado.'})
        else:
            return JsonResponse({'error': 'Por favor, forneça título e arquivo.'}, status=400)
    return JsonResponse({'error': 'Método não permitido'}, status=405)