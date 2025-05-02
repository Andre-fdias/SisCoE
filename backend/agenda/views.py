
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Lembrete, Tarefa
from .forms import LembreteForm, TarefaForm
from django.http import JsonResponse
from django.db.models import Q

@login_required
def calendario(request):
    user = request.user

    # Filtra os lembretes e tarefas do usuário logado
    lembretes = Lembrete.objects.filter(user=user)
    tarefas = Tarefa.objects.filter(user=user)

    lembrete_form = LembreteForm()
    tarefa_form = TarefaForm()

    return render(request, 'calendario.html', {
        'lembretes': lembretes,
        'tarefas': tarefas,
        'lembrete_form': lembrete_form,
        'tarefa_form': tarefa_form
    })

@login_required
def lembrete_novo(request):
    if request.method == "POST":
        form = LembreteForm(request.POST)
        if form.is_valid():
            lembrete = form.save(commit=False)
            lembrete.user = request.user
            lembrete.save()
            return JsonResponse({'success': True, 'message': 'Lembrete criado com sucesso!'})
        else:
            errors = {field: error[0] for field, error in form.errors.items()}
            return JsonResponse({'success': False, 'message': 'Erro ao criar lembrete.', 'errors': errors})
    return JsonResponse({'success': False, 'message': 'Método inválido.'})

@login_required
def tarefa_nova(request):
    if request.method == "POST":
        form = TarefaForm(request.POST)
        if form.is_valid():
            tarefa = form.save(commit=False)
            tarefa.user = request.user
            tarefa.save()
            return JsonResponse({'success': True, 'message': 'Tarefa criada com sucesso!'})
        else:
            errors = {field: error[0] for field, error in form.errors.items()}
            return JsonResponse({'success': False, 'message': 'Erro ao criar tarefa.', 'errors': errors})
    return JsonResponse({'success': False, 'message': 'Método inválido.'})

@login_required
def lembrete_editar(request, pk):
    lembrete = get_object_or_404(Lembrete, pk=pk)
    if lembrete.user != request.user:
        messages.error(request, 'Você não tem permissão para editar este lembrete.')
        return redirect('agenda:calendario')

    if request.method == "POST":
        form = LembreteForm(request.POST, instance=lembrete)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lembrete atualizado com sucesso!')
            return redirect('agenda:calendario')
    else:
        form = LembreteForm(instance=lembrete)
    return render(request, 'lembrete_form.html', {'form': form})

@login_required
def lembrete_deletar(request, pk):
    lembrete = get_object_or_404(Lembrete, pk=pk)
    if lembrete.user != request.user:
        messages.error(request, 'Você não tem permissão para excluir este lembrete.')
        return redirect('agenda:calendario')

    if request.method == "POST":
        lembrete.delete()
        messages.success(request, 'Lembrete excluído com sucesso!')
        return redirect('agenda:calendario')
    return render(request, 'eventos/lembrete_confirm_delete.html', {'lembrete': lembrete})

@login_required
def tarefa_editar(request, pk):
    tarefa = get_object_or_404(Tarefa, pk=pk)
    if tarefa.user != request.user:
        messages.error(request, 'Você não tem permissão para editar esta tarefa.')
        return redirect('agenda:calendario')

    if request.method == "POST":
        form = TarefaForm(request.POST, instance=tarefa)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tarefa atualizada com sucesso!')
            return redirect('agenda:calendario')
    else:
        form = TarefaForm(instance=tarefa)
    return render(request, 'eventos/tarefa_form.html', {'form': form})

@login_required
def tarefa_deletar(request, pk):
    tarefa = get_object_or_404(Tarefa, pk=pk)
    if tarefa.user != request.user:
        messages.error(request, 'Você não tem permissão para excluir esta tarefa.')
        return redirect('agenda:calendario')

    if request.method == "POST":
        tarefa.delete()
        messages.success(request, 'Tarefa excluída com sucesso!')
        return redirect('agenda:calendario')
    return render(request, 'eventos/tarefa_confirm_delete.html', {'tarefa': tarefa})

from django.http import JsonResponse
from django.views.decorators.http import require_POST

@require_POST
def excluir_lembrete(request, pk):
    try:
        lembrete = Lembrete.objects.get(pk=pk, user=request.user)
        lembrete.delete()
        return JsonResponse({'success': True, 'message': 'Lembrete excluído com sucesso!'})
    except Lembrete.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Lembrete não encontrado.'})

@require_POST
def excluir_tarefa(request, pk):
    try:
        tarefa = Tarefa.objects.get(pk=pk, user=request.user)
        tarefa.delete()
        return JsonResponse({'success': True, 'message': 'Tarefa excluída com sucesso!'})
    except Tarefa.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Tarefa não encontrada.'})


from django.utils import timezone
from datetime import timedelta

@login_required
def eventos_proximos(request):
    user = request.user
    agora = timezone.now()
    limite = agora + timedelta(days=2)  # Notificar eventos que vencem em até 1 dia

    # Filtra lembretes e tarefas que estão dentro do intervalo
    lembretes_proximos = Lembrete.objects.filter(user=user, data__range=(agora, limite))
    tarefas_proximas = Tarefa.objects.filter(user=user, data_fim__range=(agora, limite))

    # Combina os resultados
    eventos_proximos = list(lembretes_proximos) + list(tarefas_proximas)

    # Retorna os eventos no formato JSON
    return JsonResponse({
        'eventos': [
            {
                'titulo': evento.titulo,
                'data': evento.data.strftime('%Y-%m-%d %H:%M:%S') if hasattr(evento, 'data') else evento.data_fim.strftime('%Y-%m-%d %H:%M:%S'),
                'tipo': 'Lembrete' if hasattr(evento, 'data') else 'Tarefa'
            }
            for evento in eventos_proximos
        ]
    })
