from django.db import models
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden
from .models import Lembrete, Tarefa
from .forms import LembreteForm, TarefaForm

def calendario(request):
    # Filtra eventos do usuário + públicos
    lembretes = Lembrete.objects.filter(
        models.Q(usuario=request.user) | 
        models.Q(visibilidade='publico')
    )
    tarefas = Tarefa.objects.filter(
        models.Q(usuario=request.user) | 
        models.Q(visibilidade='publico')
    )
    
    lembrete_form = LembreteForm()
    tarefa_form = TarefaForm()
    
    return render(request, 'calendario.html', {
        'lembretes': lembretes,
        'tarefas': tarefas,
        'lembrete_form': lembrete_form,
        'tarefa_form': tarefa_form
    })

def lembrete_novo(request):
    if request.method == "POST":
        form = LembreteForm(request.POST)
        if form.is_valid():
            novo_lembrete = form.save(commit=False)
            novo_lembrete.usuario = request.user
            novo_lembrete.save()
            return redirect('agenda:calendario')
    return redirect('agenda:calendario')

def tarefa_nova(request):
    if request.method == "POST":
        form = TarefaForm(request.POST)
        if form.is_valid():
            nova_tarefa = form.save(commit=False)
            nova_tarefa.usuario = request.user
            nova_tarefa.save()
            return redirect('agenda:calendario')
    return redirect('agenda:calendario')

def lembrete_editar(request, pk):
    lembrete = get_object_or_404(Lembrete, pk=pk)
    
    if lembrete.usuario != request.user:
        return HttpResponseForbidden("Ação não permitida")
        
    if request.method == "POST":
        form = LembreteForm(request.POST, instance=lembrete)
        if form.is_valid():
            form.save()
            return redirect('agenda:calendario')
    else:
        form = LembreteForm(instance=lembrete)
    
    return render(request, 'lembrete_form.html', {'form': form})

def lembrete_deletar(request, pk):
    lembrete = get_object_or_404(Lembrete, pk=pk)
    
    if lembrete.usuario != request.user:
        return HttpResponseForbidden("Ação não permitida")
        
    if request.method == "POST":
        lembrete.delete()
        return redirect('agenda:calendario')
        
    return render(request, 'lembrete_confirm_delete.html', {'lembrete': lembrete})

def tarefa_editar(request, pk):
    tarefa = get_object_or_404(Tarefa, pk=pk)
    
    if tarefa.usuario != request.user:
        return HttpResponseForbidden("Ação não permitida")
        
    if request.method == "POST":
        form = TarefaForm(request.POST, instance=tarefa)
        if form.is_valid():
            form.save()
            return redirect('agenda:calendario')
    else:
        form = TarefaForm(instance=tarefa)
    
    return render(request, 'tarefa_form.html', {'form': form})

def tarefa_deletar(request, pk):
    tarefa = get_object_or_404(Tarefa, pk=pk)
    
    if tarefa.usuario != request.user:
        return HttpResponseForbidden("Ação não permitida")
        
    if request.method == "POST":
        tarefa.delete()
        return redirect('agenda:calendario')
        
    return render(request, 'tarefa_confirm_delete.html', {'tarefa': tarefa})