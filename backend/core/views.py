from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .models import User
from .models import Profile
from backend.documentos.models import Documento
from django.shortcuts import render
from backend.efetivo.models import Cadastro, Promocao, Imagem, DetalhesSituacao
from datetime import datetime, date
from django.db.models import Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from backend.agenda.models import Lembrete, Tarefa  # Importe os modelos Lembrete e Tarefa


def capa(request):
    template_name = 'landing.html'
    return render(request, template_name)


@login_required
def index(request):
    hoje = datetime.now()
    mes_atual = hoje.month
    ano_atual = hoje.year

    aniversariantes_list = Cadastro.objects.filter(nasc__month=mes_atual).order_by('nasc__day').prefetch_related('imagens', 'promocoes', 'detalhes_situacao')

    for funcionario in aniversariantes_list:
        try:
            funcionario.posto_grad_recente = funcionario.promocoes.latest('ultima_promocao').posto_grad
        except Promocao.DoesNotExist:
            funcionario.posto_grad_recente = None

    paginator_aniversariantes = Paginator(aniversariantes_list, 10)
    page_number = request.GET.get('page')

    documentos_list = Documento.objects.all().order_by('-data_criacao')
    paginator_documentos = Paginator(documentos_list, 10)
    documentos_page_number = request.GET.get('documentos_page')

    try:
        page_obj = paginator_aniversariantes.get_page(page_number)
        documentos_page_obj = paginator_documentos.get_page(documentos_page_number)
    except PageNotAnInteger:
        page_obj = paginator_aniversariantes.get_page(1)
        documentos_page_obj = paginator_documentos.get_page(1)
    except EmptyPage:
        page_obj = paginator_aniversariantes.get_page(paginator_aniversariantes.num_pages)
        documentos_page_obj = paginator_documentos.get_page(paginator_documentos.num_pages)

    # Adicionando os lembretes e tarefas ao contexto
    lembretes = Lembrete.objects.filter(user=request.user, data__year=hoje.year, data__month=hoje.month).order_by('data')
    tarefas = Tarefa.objects.filter(user=request.user, data_inicio__year=hoje.year, data_inicio__month=hoje.month).order_by('data_inicio')

    context = {
        'page_obj': page_obj,
        'documentos_page_obj': documentos_page_obj,
        'mes_atual': mes_atual,
        'meses': [
            (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'),
            (4, 'Abril'), (5, 'Maio'), (6, 'Junho'),
            (7, 'Julho'), (8, 'Agosto'), (9, 'Setembro'),
            (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
        ],
        'hoje': hoje,
        'lembretes': lembretes,  # Adicionado
        'tarefas': tarefas,      # Adicionado
    }
    return render(request, 'index.html', context)

@login_required
def dashboard(request):
    template_name = 'dashboard.html'
    return render(request, template_name)


@login_required
def profile(request):
    profile = request.user.profile
    return render(request, 'profiles/profile.html', {'profile': profile})



@login_required
def profile_list(request):
    profiles = Profile.objects.all()
    return render(request, 'accounts/user_list.html', {'profiles': profiles})



@login_required
def profile_detail(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    return render(request, 'accounts/accounts/user_detail.html', {'profile': profile})



@login_required
def profile_create(request):
    if request.method == 'POST':
        user = request.POST.get('user')
        cadastro = request.POST.get('cadastro')
        re = request.POST.get('re')
        dig = request.POST.get('dig')
        posto_grad = request.POST.get('posto_grad')
        image = request.FILES.get('image')
        cpf = request.POST.get('cpf')
        tipo = request.POST.get('tipo')
        
        profile = Profile(user=user, cadastro=cadastro, re=re, dig=dig, posto_grad=posto_grad, image=image, cpf=cpf, tipo=tipo)
        profile.save()
        return redirect('core:profile_list')
    return render(request, 'profiles/profile_form.html')

@login_required
def profile_update(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    posto_grad_choices = Profile.posto_grad_choices
    tipo_choices = Profile.tipo_choices

    if request.method == 'POST':
        profile.cpf = request.POST.get('cpf')
        profile.posto_grad = request.POST.get('posto_grad')
        profile.re = request.POST.get('re')
        profile.dig = request.POST.get('dig')
        profile.tipo = request.POST.get('tipo')
        if 'image' in request.FILES:
            profile.image = request.FILES['image']
        
        profile.save()
        return redirect('core:profile_detail', pk=pk)
    
    context = {
        'profile': profile,
        'posto_grad_choices': posto_grad_choices,
        'tipo_choices': tipo_choices,
    }
    return render(request, 'profiles/profile_form.html', context)

@login_required
def profile_delete(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    if request.method == 'POST':
        profile.delete()
        return redirect('core:profile_list')
    return render(request, 'profiles/profile_confirm_delete.html', {'profile': profile})
