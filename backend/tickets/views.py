from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.db.models import Count
from django.http import HttpResponseForbidden
from .forms import ChamadoForm, ComentarioForm, UpdateStatusForm, AssignTecnicoForm
from .models import Chamado, Anexo, Categoria, Comentario
from backend.accounts.models import User
from backend.efetivo.models import Cadastro

def abrir_chamado(request):
    if request.method == 'POST':
        form = ChamadoForm(request.POST, request.FILES)
        if form.is_valid():
            user = None
            cpf = form.cleaned_data.get('solicitante_cpf')
            if cpf:
                try:
                    cadastro = Cadastro.objects.get(cpf=cpf.replace('.', '').replace('-', ''))
                    if hasattr(cadastro, 'user_account'):
                        user = cadastro.user_account
                except Cadastro.DoesNotExist:
                    try:
                        user = User.objects.get(email=form.cleaned_data.get('solicitante_email'))
                    except User.DoesNotExist:
                        pass

            chamado = form.save(commit=False)
            if user:
                chamado.usuario = user
            
            chamado.save()

            for f in request.FILES.getlist('anexos'):
                Anexo.objects.create(chamado=chamado, arquivo=f, autor=user)
            
            messages.success(request, f'Seu chamado foi aberto com sucesso! Protocolo: {chamado.protocolo}')
            return redirect('tickets:chamado_sucesso', protocolo=chamado.protocolo)
        else:
            messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        form = ChamadoForm()

    return render(request, 'tickets/abrir_chamado.html', {'form': form})

def chamado_sucesso(request, protocolo):
    return render(request, 'tickets/chamado_sucesso.html', {'protocolo': protocolo})

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
        'tecnicos': User.objects.filter(is_staff=True),
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
    chamado = get_object_or_404(Chamado, id=chamado_id)
    
    if not request.user.is_staff and chamado.usuario != request.user:
        return HttpResponseForbidden("Você não tem permissão para ver este chamado.")

    anexos = chamado.anexos.all()
    comentarios = chamado.comentarios.all()
    
    if request.method == 'POST' and request.user.is_staff:
        action = request.POST.get('action')
        if action == 'add_comment':
            comentario_form = ComentarioForm(request.POST)
            if comentario_form.is_valid():
                novo_comentario = comentario_form.save(commit=False)
                novo_comentario.chamado = chamado
                novo_comentario.autor = request.user
                novo_comentario.save()
                messages.success(request, 'Comentário adicionado com sucesso.')
                return redirect('tickets:chamado_detail', chamado_id=chamado.id)
        
        elif action == 'update_status':
            status_form = UpdateStatusForm(request.POST, instance=chamado)
            if status_form.is_valid():
                status_form.save()
                messages.success(request, 'Status do chamado atualizado.')
                return redirect('tickets:chamado_detail', chamado_id=chamado.id)

        elif action == 'assign_tecnico':
            assign_form = AssignTecnicoForm(request.POST, instance=chamado)
            if assign_form.is_valid():
                assign_form.save()
                messages.success(request, 'Técnico atribuído com sucesso.')
                return redirect('tickets:chamado_detail', chamado_id=chamado.id)

    comentario_form = ComentarioForm()
    status_form = UpdateStatusForm(instance=chamado)
    assign_form = AssignTecnicoForm(instance=chamado)

    context = {
        'chamado': chamado,
        'anexos': anexos,
        'comentarios': comentarios,
        'comentario_form': comentario_form,
        'status_form': status_form,
        'assign_form': assign_form,
    }
    return render(request, 'tickets/chamado_detail.html', context)