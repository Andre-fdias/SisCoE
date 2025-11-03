from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.db.models import Count, Q
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from collections import defaultdict
from .forms import ChamadoForm, ComentarioForm, UpdateStatusForm, AssignTecnicoForm
from .models import Chamado, Anexo, Categoria, Comentario
from backend.accounts.models import User
from backend.efetivo.models import Cadastro, DetalhesSituacao, Promocao, Imagem

@csrf_exempt
def buscar_dados_cpf(request):
    """API para buscar dados do militar por CPF"""
    logger.info("=== INÍCIO buscar_dados_cpf ===")
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cpf = data.get('cpf', '')
            logger.info(f"CPF recebido: {cpf}")
            
            if not cpf or len(cpf) != 14:
                logger.error(f"CPF inválido: {cpf}")
                return JsonResponse({'error': 'CPF inválido ou fora do formato XXX.XXX.XXX-XX'}, status=400)
            
            # Limpa o CPF
            cpf_limpo = cpf.replace('.', '').replace('-', '')
            logger.info(f"CPF limpo para busca: {cpf_limpo}")
            
            # Busca o cadastro pelo CPF - TENTA COM E SEM FORMATAÇÃO
            try:
                # Primeiro tenta com formatação
                cadastro = Cadastro.objects.get(cpf=cpf)
                logger.info(f"Cadastro encontrado COM formatação: {cadastro.nome}")
            except Cadastro.DoesNotExist:
                # Tenta sem formatação
                cadastro = Cadastro.objects.get(cpf=cpf_limpo)
                logger.info(f"Cadastro encontrado SEM formatação: {cadastro.nome}")
            
            # Resto do código permanece igual...
            # Busca os dados mais recentes da situação
            situacao = DetalhesSituacao.objects.filter(cadastro=cadastro).order_by('-data_alteracao').first()
            logger.info(f"Situação encontrada: {situacao}")
            
            # Busca a promoção mais recente
            promocao = Promocao.objects.filter(cadastro=cadastro).order_by('-data_alteracao').first()
            logger.info(f"Promoção encontrada: {promocao}")
            
            # Busca a foto mais recente
            foto = Imagem.objects.filter(cadastro=cadastro).order_by('-create_at').first()
            logger.info(f"Foto encontrada: {foto}")
            
            response_data = {
                'nome': cadastro.nome,
                'nome_guerra': cadastro.nome_de_guerra,
                'email': cadastro.email,
                'telefone': cadastro.telefone,
                're': f"{cadastro.re}-{cadastro.dig}",
                'posto_grad': promocao.posto_grad if promocao else '',
                'sgb': situacao.sgb if situacao else '',
                'posto_secao': situacao.posto_secao if situacao else '',
                'foto_url': foto.image.url if foto else '',
            }
            
            logger.info(f"Dados retornados: {response_data}")
            return JsonResponse(response_data)
            
        except Cadastro.DoesNotExist:
            logger.error(f"Cadastro não encontrado para CPF (com e sem formatação): {cpf}")
            return JsonResponse({'error': 'Militar não encontrado'}, status=404)
        except Exception as e:
            logger.error(f"Erro em buscar_dados_cpf: {str(e)}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método não permitido'}, status=405)

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.db.models import Count, Q
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from collections import defaultdict

logger = logging.getLogger(__name__)

def abrir_chamado(request):
    logger.info("=== INÍCIO abrir_chamado ===")
    logger.info(f"Método: {request.method}")
    
    if request.method == 'POST':
        logger.info("Processando POST request")
        form = ChamadoForm(request.POST, request.FILES)
        
        if form.is_valid():
            logger.info("Formulário é VÁLIDO")
            cpf = form.cleaned_data.get('solicitante_cpf')
            logger.info(f"CPF do formulário: {cpf}")
            user = None
            
            try:
                # Limpa CPF para busca
                cpf_limpo = cpf.replace('.', '').replace('-', '')
                logger.info(f"CPF limpo para busca: {cpf_limpo}")
                
                # Busca dados do militar - TENTA COM E SEM FORMATAÇÃO
                logger.info("Buscando cadastro do militar...")
                try:
                    # Primeiro tenta com a formatação original (como está no banco)
                    cadastro = Cadastro.objects.get(cpf=cpf)
                    logger.info(f"Cadastro encontrado COM formatação: {cadastro.nome}")
                except Cadastro.DoesNotExist:
                    # Se não encontrar, tenta sem formatação
                    cadastro = Cadastro.objects.get(cpf=cpf_limpo)
                    logger.info(f"Cadastro encontrado SEM formatação: {cadastro.nome}")
                
                logger.info(f"Cadastro encontrado: {cadastro.nome} (RE: {cadastro.re})")
                
                # Resto do código permanece igual...
                # Tenta encontrar usuário vinculado
                try:
                    user = User.objects.get(email=cadastro.email)
                    logger.info(f"Usuário encontrado: {user.email}")
                except User.DoesNotExist:
                    logger.info("Usuário não encontrado pelo email, verificando user_account...")
                    if hasattr(cadastro, 'user_account') and cadastro.user_account:
                        user = cadastro.user_account
                        logger.info(f"Usuário vinculado via user_account: {user.email}")
                    else:
                        logger.info("Nenhum usuário vinculado encontrado")
                
                # Cria objeto chamado sem salvar
                chamado = form.save(commit=False)
                logger.info("Chamado object created (not saved)")
                
                # Define a categoria do clean() do form
                chamado.categoria = form.cleaned_data['categoria']
                logger.info(f"Categoria definida: {chamado.categoria}")

                # PREENCHE AUTOMATICAMENTE OS DADOS DO SOLICITANTE
                chamado.solicitante_nome = cadastro.nome
                chamado.solicitante_email = cadastro.email
                chamado.solicitante_telefone = cadastro.telefone
                chamado.re = f"{cadastro.re}-{cadastro.dig}"
                logger.info("Dados básicos do solicitante preenchidos")

                # Busca dados adicionais
                situacao = DetalhesSituacao.objects.filter(cadastro=cadastro).order_by('-data_alteracao').first()
                promocao = Promocao.objects.filter(cadastro=cadastro).order_by('-data_alteracao').first()
                foto = Imagem.objects.filter(cadastro=cadastro).order_by('-create_at').first()

                chamado.posto_grad = promocao.posto_grad if promocao else ''
                chamado.sgb = situacao.sgb if situacao else ''
                chamado.posto_secao = situacao.posto_secao if situacao else ''
                
                logger.info(f"Posto/Grad: {chamado.posto_grad}")
                logger.info(f"SGB: {chamado.sgb}")
                logger.info(f"Posto/Seção: {chamado.posto_secao}")

                if user:
                    chamado.usuario = user
                    logger.info(f"Usuário atribuído ao chamado: {user.email}")
                
                if foto:
                    chamado.foto_militar = foto.image
                    logger.info("Foto do militar atribuída")
                
                # SALVA O CHAMADO
                logger.info("Salvando chamado no banco...")
                chamado.save()
                logger.info(f"Chamado salvo com protocolo: {chamado.protocolo}")

                # Processa anexos
                anexos_files = request.FILES.getlist('anexos')
                logger.info(f"Processando {len(anexos_files)} anexos...")
                
                for f in anexos_files:
                    Anexo.objects.create(chamado=chamado, arquivo=f, autor=user)
                    logger.info(f"Anexo criado: {f.name}")
                
                logger.info("=== SUCESSO - Redirecionando para página de sucesso ===")
                messages.success(request, f'Seu chamado foi aberto com sucesso! Protocolo: {chamado.protocolo}')
                return redirect('tickets:chamado_sucesso', protocolo=chamado.protocolo)
                
            except Cadastro.DoesNotExist:
                error_msg = f'Militar não encontrado com CPF: {cpf} (tentou com e sem formatação)'
                logger.error(error_msg)
                messages.error(request, 'Militar não encontrado com este CPF.')
                
            except Exception as e:
                error_msg = f'Erro inesperado ao processar chamado: {str(e)}'
                logger.error(error_msg, exc_info=True)
                messages.error(request, 'Erro interno ao processar seu chamado. Tente novamente.')
        else:
            logger.error("Formulário INVÁLIDO")
            logger.error(f"Erros do formulário: {form.errors}")
            messages.error(request, 'Por favor, corrija os erros no formulário.')
    
    else:
        logger.info("Renderizando formulário vazio (GET request)")
        form = ChamadoForm()

    # Cria o mapa de categorias para o JavaScript
    categoria_map = defaultdict(list)
    for cat in Categoria.objects.all():
        categoria_map[cat.categoria].append({
            'value': cat.subcategoria,
            'display': cat.get_subcategoria_display()
        })

    context = {
        'form': form,
        'categoria_map': json.dumps(categoria_map)
    }
    
    logger.info("Renderizando template abrir_chamado.html")
    return render(request, 'tickets/abrir_chamado.html', context)



def chamado_sucesso(request, protocolo):
    # Determinar a origem baseado no usuário autenticado
    origem = 'dashboard' if request.user.is_authenticated else 'landing'
    
    context = {
        'protocolo': protocolo,
        'origem': origem
    }
    return render(request, 'tickets/chamado_sucesso.html', context)


@login_required
def meus_chamados(request):
    chamados = Chamado.objects.filter(usuario=request.user).order_by('-criado_em')
    return render(request, 'tickets/meus_chamados.html', {'chamados': chamados})

@staff_member_required
def dashboard(request):
    chamados_qs = Chamado.objects.all()
    
    status_filter = request.GET.get('status')
    categoria_filter = request.GET.get('categoria')
    tecnico_filter = request.GET.get('tecnico')

    if status_filter:
        chamados_qs = chamados_qs.filter(status=status_filter)
    if categoria_filter:
        chamados_qs = chamados_qs.filter(categoria__id=categoria_filter)
    if tecnico_filter:
        chamados_qs = chamados_qs.filter(tecnico_responsavel__id=tecnico_filter)

    total_chamados = Chamado.objects.count()
    hoje = timezone.now().date()
    chamados_abertos_hoje = Chamado.objects.filter(criado_em__date=hoje).count()
    
    chamados_por_status = Chamado.objects.values('status').annotate(total=Count('status')).order_by('status')
    status_dict = dict(Chamado.STATUS_CHOICES)
    chart_data = {
        'labels': [status_dict.get(item['status'], item['status']) for item in chamados_por_status],
        'data': [item['total'] for item in chamados_por_status],
    }

    context = {
        'chamados': chamados_qs,
        'categorias': Categoria.objects.all(),
        'tecnicos': User.objects.filter(Q(is_admin=True) | Q(is_superuser=True)),
        'status_choices': Chamado.STATUS_CHOICES,
        'current_filters': {
            'status': status_filter,
            'categoria': categoria_filter,
            'tecnico': tecnico_filter,
        },
        'stats': {
            'total_chamados': total_chamados,
            'chamados_abertos_hoje': chamados_abertos_hoje,
        },
        'chart_data': chart_data,
    }
    return render(request, 'tickets/dashboard.html', context)


from django.http import JsonResponse
from django.template.loader import render_to_string

@login_required
def meus_chamados_api(request):
    """API para retornar os chamados do usuário em formato JSON"""
    chamados = Chamado.objects.filter(usuario=request.user).order_by('-criado_em')[:5]  # Últimos 5
    
    chamados_data = []
    for chamado in chamados:
        chamados_data.append({
            'id': chamado.id,
            'protocolo': chamado.protocolo,
            'assunto': chamado.assunto,
            'status': chamado.get_status_display(),
            'status_cor': get_status_color(chamado.status),
            'criado_em': chamado.criado_em.strftime('%d/%m/%Y %H:%M'),
            'categoria': str(chamado.categoria),
            'descricao': chamado.descricao[:100] + '...' if len(chamado.descricao) > 100 else chamado.descricao,
        })
    
    return JsonResponse({
        'chamados': chamados_data,
        'total': len(chamados_data)
    })

def get_status_color(status):
    """Retorna a cor do status baseado no estado"""
    colors = {
        'aberto': 'bg-green-100 text-green-800',
        'em_atendimento': 'bg-blue-100 text-blue-800',
        'aguardando_usuario': 'bg-yellow-100 text-yellow-800',
        'resolvido': 'bg-purple-100 text-purple-800',
        'fechado': 'bg-gray-100 text-gray-800',
    }
    return colors.get(status, 'bg-gray-100 text-gray-800')



def chamado_detail(request, chamado_id):
    """
    View para detalhes do chamado
    Admin: mostra detalhes de um chamado específico com funcionalidades completas
    Usuário comum: mostra detalhes do seu próprio chamado (apenas leitura)
    """
    print(f"Usuário: {request.user}")
    print(f"É admin: {request.user.is_admin}")
    print(f"Chamado ID: {chamado_id}")
    
    # Busca o chamado
    chamado = get_object_or_404(Chamado, pk=chamado_id)
    
    # Verifica permissões
    if not request.user.is_admin and chamado.usuario != request.user:
        return HttpResponseForbidden("Você não tem permissão para acessar este chamado.")
    
    # Prepara o contexto base
    context = {
        'chamado': chamado,
        'comentarios': chamado.comentarios.all().order_by('criado_em'),
        'anexos': chamado.anexos.all().order_by('-enviado_em'),
    }
    
    # Lógica para admin
    if request.user.is_admin:
        template_name = 'tickets/chamado_detail_admin.html'
        
        # Adiciona forms para admin
        context.update({
            'comentario_form': ComentarioForm(),
            'status_form': UpdateStatusForm(instance=chamado),
            'assign_form': AssignTecnicoForm(instance=chamado),
        })
        
        # Lógica de POST (para admin)
        if request.method == 'POST':
            action = request.POST.get('action')
            
            if action == 'add_comment':
                comentario_form = ComentarioForm(request.POST)
                if comentario_form.is_valid():
                    comentario = comentario_form.save(commit=False)
                    comentario.chamado = chamado
                    comentario.autor = request.user
                    comentario.save()
                    messages.success(request, 'Comentário adicionado com sucesso!')
                    return redirect('tickets:chamado_detail', chamado_id=chamado.id)
            
            elif action == 'update_status':
                status_form = UpdateStatusForm(request.POST, instance=chamado)
                if status_form.is_valid():
                    status_form.save()
                    messages.success(request, 'Status atualizado com sucesso!')
                    return redirect('tickets:chamado_detail', chamado_id=chamado.id)
            
            elif action == 'assign_tecnico':
                assign_form = AssignTecnicoForm(request.POST, instance=chamado)
                if assign_form.is_valid():
                    assign_form.save()
                    messages.success(request, 'Técnico atribuído com sucesso!')
                    return redirect('tickets:chamado_detail', chamado_id=chamado.id)
    
    else:
        # Template para usuário comum
        template_name = 'tickets/chamado_detail_user.html'
    
    # RETORNA SEMPRE um HttpResponse
    return render(request, template_name, context)

@login_required
def meus_chamados_lista(request):
    """View específica para lista de chamados do usuário comum"""
    chamados = Chamado.objects.filter(usuario=request.user).order_by('-criado_em')
    return render(request, 'tickets/meus_chamados.html', {'chamados': chamados})