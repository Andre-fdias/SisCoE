import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.db.models import Count, Q
from django.http import HttpResponseForbidden, JsonResponse
import json
from collections import defaultdict

from .forms import ChamadoForm, ComentarioForm, UpdateStatusForm, AssignTecnicoForm
from .models import Chamado, Anexo, Categoria, Comentario
from backend.accounts.models import User
from backend.efetivo.models import Cadastro, DetalhesSituacao, Promocao, Imagem
from .email_service import enviar_email_chamado_aberto, enviar_email_mudanca_status, enviar_email_comentario_adicionado
from .api_views import buscar_dados_cpf

logger = logging.getLogger(__name__)

def abrir_chamado(request):
    """
    View para abertura de chamados com sistema de email
    """
    logger.info("=== INÍCIO abrir_chamado ===")
    
    if request.method == 'POST':
        form = ChamadoForm(request.POST, request.FILES)
        
        if form.is_valid():
            cpf = form.cleaned_data.get('solicitante_cpf')
            
            try:
                # Limpa CPF para busca
                cpf_limpo = cpf.replace('.', '').replace('-', '')
                
                # Busca dados do militar
                try:
                    cadastro = Cadastro.objects.get(cpf=cpf)
                except Cadastro.DoesNotExist:
                    cadastro = Cadastro.objects.get(cpf=cpf_limpo)
                
                # Busca usuário vinculado
                user = None
                try:
                    user = User.objects.get(email=cadastro.email)
                except User.DoesNotExist:
                    if hasattr(cadastro, 'user_account') and cadastro.user_account:
                        user = cadastro.user_account
                
                # Cria objeto chamado
                chamado = form.save(commit=False)
                chamado.categoria = form.cleaned_data['categoria']

                # PREENCHE AUTOMATICAMENTE OS DADOS DO SOLICITANTE
                chamado.solicitante_nome = cadastro.nome
                chamado.solicitante_email = cadastro.email
                chamado.solicitante_telefone = cadastro.telefone
                chamado.re = f"{cadastro.re}-{cadastro.dig}"

                # Busca dados adicionais
                situacao = DetalhesSituacao.objects.filter(cadastro=cadastro).order_by('-data_alteracao').first()
                promocao = Promocao.objects.filter(cadastro=cadastro).order_by('-data_alteracao').first()
                foto = Imagem.objects.filter(cadastro=cadastro).order_by('-create_at').first()

                chamado.posto_grad = promocao.posto_grad if promocao else ''
                chamado.sgb = situacao.sgb if situacao else ''
                chamado.posto_secao = situacao.posto_secao if situacao else ''

                if user:
                    chamado.usuario = user
                
                if foto:
                    chamado.foto_militar = foto.image
                
                # SALVA O CHAMADO
                chamado.save()

                # ENVIA EMAIL DE CONFIRMAÇÃO
                email_enviado = enviar_email_chamado_aberto(chamado)

                # Processa anexos
                anexos_files = request.FILES.getlist('anexos')
                for f in anexos_files:
                    Anexo.objects.create(chamado=chamado, arquivo=f, autor=user)
                
                messages.success(request, f'Seu chamado foi aberto com sucesso! Protocolo: {chamado.protocolo}')
                if not email_enviado:
                    messages.warning(request, 'Chamado criado, mas não foi possível enviar o email de confirmação.')
                
                return redirect('tickets:chamado_sucesso', protocolo=chamado.protocolo)
                
            except Cadastro.DoesNotExist:
                messages.error(request, 'Militar não encontrado com este CPF.')
            except Exception as e:
                logger.error(f'Erro ao processar chamado: {str(e)}', exc_info=True)
                messages.error(request, 'Erro interno ao processar seu chamado. Tente novamente.')
        else:
            messages.error(request, 'Por favor, corrija os erros no formulário.')
    
    else:
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
    
    return render(request, 'tickets/abrir_chamado.html', context)

def chamado_sucesso(request, protocolo):
    """Página de sucesso após abertura de chamado"""
    origem = 'dashboard' if request.user.is_authenticated else 'landing'
    
    context = {
        'protocolo': protocolo,
        'origem': origem
    }
    return render(request, 'tickets/chamado_sucesso.html', context)

@login_required
def meus_chamados(request):
    """View para lista de chamados do usuário comum"""
    chamados = Chamado.objects.filter(usuario=request.user).order_by('-criado_em')
    return render(request, 'tickets/meus_chamados.html', {'chamados': chamados})

@login_required
def meus_chamados_api(request):
    """API para retornar os chamados do usuário em formato JSON"""
    chamados = Chamado.objects.filter(usuario=request.user).order_by('-criado_em')[:5]
    
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

@staff_member_required
def dashboard(request):
    """Dashboard para administradores"""
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

@login_required
def chamado_detail(request, chamado_id):
    """
    View para detalhes do chamado com sistema de email para mudanças de status
    """
    chamado = get_object_or_404(Chamado, pk=chamado_id)
    
    # Verifica permissões
    if not request.user.is_admin and chamado.usuario != request.user:
        return HttpResponseForbidden("Você não tem permissão para acessar este chamado.")
    
    context = {
        'chamado': chamado,
        'comentarios': chamado.comentarios.all().order_by('criado_em'),
        'anexos': chamado.anexos.all().order_by('-enviado_em'),
    }
    
    # Lógica para admin
    if request.user.is_admin:
        template_name = 'tickets/chamado_detail_admin.html'
        
        context.update({
            'comentario_form': ComentarioForm(),
            'status_form': UpdateStatusForm(instance=chamado),
            'assign_form': AssignTecnicoForm(instance=chamado),
        })
        
        if request.method == 'POST':
            action = request.POST.get('action')
            
            if action == 'add_comment':
                comentario_form = ComentarioForm(request.POST)
                if comentario_form.is_valid():
                    comentario = comentario_form.save(commit=False)
                    comentario.chamado = chamado
                    comentario.autor = request.user
                    comentario.save()
                    
                    # Envia email de comentário (apenas se não for privado)
                    if not comentario.privado:
                        enviar_email_comentario_adicionado(chamado, comentario)
                    
                    messages.success(request, 'Comentário adicionado com sucesso!')
                    return redirect('tickets:chamado_detail', chamado_id=chamado.id)
            
            elif action == 'update_status':
                status_form = UpdateStatusForm(request.POST, instance=chamado)
                if status_form.is_valid():
                    old_status = chamado.status
                    status_form.save()
                    
                    # Verifica se o status mudou e envia email
                    if hasattr(chamado, '_status_changed') and chamado._status_changed:
                        enviar_email_mudanca_status(chamado, old_status, chamado.status)
                    
                    messages.success(request, 'Status atualizado com sucesso!')
                    return redirect('tickets:chamado_detail', chamado_id=chamado.id)
            
            elif action == 'assign_tecnico':
                assign_form = AssignTecnicoForm(request.POST, instance=chamado)
                if assign_form.is_valid():
                    assign_form.save()
                    messages.success(request, 'Técnico atribuído com sucesso!')
                    return redirect('tickets:chamado_detail', chamado_id=chamado.id)
    
    else:
        template_name = 'tickets/chamado_detail_user.html'
    
    return render(request, template_name, context)