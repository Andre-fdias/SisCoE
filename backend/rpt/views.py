from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.messages import constants
from backend.efetivo.models import Cadastro, DetalhesSituacao, Promocao, Imagem  # Ajuste a importação conforme necessário
from .models import Cadastro_rpt, HistoricoRpt
from django.db.models import Prefetch
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


@login_required
def cadastrar_rpt(request):
    if request.method == 'GET':
        context = {
            'sgb_choices': Cadastro_rpt._meta.get_field('sgb_destino').choices,
            'posto_secao_choices': Cadastro_rpt._meta.get_field('posto_secao_destino').choices,
            'status_choices': Cadastro_rpt._meta.get_field('status').choices,
        }
        return render(request, 'cadastrar_rpt.html', context)

    elif request.method == 'POST':
        cadastro_id = request.POST.get('cadastro_id')
        data_pedido = request.POST.get('data_pedido')
        status = request.POST.get('status')
        sgb_destino = request.POST.get('sgb_destino')
        posto_secao_destino = request.POST.get('posto_secao_destino')
        doc_solicitacao = request.POST.get('doc_solicitacao')
        usuario_alteracao = request.user

        if not cadastro_id:
            messages.add_message(request, constants.ERROR, 'Cadastro não encontrado. Por favor, pesquise um RE válido.', extra_tags='bg-red-500 text-white p-4 rounded')
            return redirect('rpt:cadastrar_rpt')

        cadastro = get_object_or_404(Cadastro, id=cadastro_id)

        # Verificar se já existe um cadastro com status "aguardando" para o RE retornado
        cadastro_existente = Cadastro_rpt.objects.filter(cadastro=cadastro, status='Aguardando').exists()
        if cadastro_existente:
            messages.add_message(request, constants.ERROR, 'Militar ja possui cadasto ativo no Rpt.', extra_tags='bg-red-500 text-white p-4 rounded')
            return redirect('rpt:listar_rpt')

        Cadastro_rpt.objects.create(
            cadastro=cadastro,
            data_pedido=data_pedido,
            status=status,
            sgb_destino=sgb_destino,
            posto_secao_destino=posto_secao_destino,
            doc_solicitacao=doc_solicitacao,
            usuario_alteracao=usuario_alteracao
        )
        messages.add_message(request, constants.SUCCESS, 'Cadastro realizado com Sucesso.', extra_tags='bg-green-500 text-white p-4 rounded')
        return redirect('rpt:listar_rpt')
    return render(request, 'cadastrar_rpt.html')



@login_required
def listar_rpt(request):
    cadastros_rpt = Cadastro_rpt.objects.all().select_related('cadastro').prefetch_related(
        Prefetch('cadastro__promocoes', to_attr='promocoes_list'),
        Prefetch('cadastro__detalhes_situacao', to_attr='detalhes_situacao_list'),
        Prefetch('cadastro__imagens', to_attr='imagens_list')
    )
    
    return render(request, 'listar_rpt.html', {'cadastros_rpt': cadastros_rpt})




from django.db.models import F, Window
from django.db.models.functions import RowNumber

@login_required
def ver_rpt(request, id):
    # Obtém o cadastro RPT com rank global
    cadastro_rpt = get_object_or_404(
        Cadastro_rpt.objects.annotate(
            global_rank=Window(
                expression=RowNumber(),
                order_by=[F('data_pedido').asc(), F('id').asc()]
            )
        ),
        id=id
    )
    
    # Obtém dados relacionados
    cadastro = cadastro_rpt.cadastro
    detalhes_situacao = cadastro.detalhes_situacao.last()
    promocao = cadastro.promocoes.last()

    # Conta quantos estão no mesmo posto_secao_destino
    count_in_section = Cadastro_rpt.objects.filter(
        posto_secao_destino=cadastro_rpt.posto_secao_destino
    ).count()

    context = {
        'cadastro_rpt': cadastro_rpt,
        'cadastro': cadastro,
        'detalhes_situacao': detalhes_situacao,
        'promocao': promocao,
        'global_rank': cadastro_rpt.global_rank,
        'count_in_section': count_in_section,
    }
    return render(request, 'ver_rpt.html', context)



@login_required
def editar_rpt(request, id):
    cadastro_rpt = get_object_or_404(Cadastro_rpt, id=id)

    if request.method == "GET":
        return render(request, 'editar_rpt.html', {
             'cadastro_rpt': cadastro_rpt,
             'status_choices': Cadastro_rpt._meta.get_field('status').choices,
             'posto_secao_choices': Cadastro_rpt._meta.get_field('posto_secao_destino').choices,
             'sgb_choices': Cadastro_rpt._meta.get_field('sgb_destino').choices,
             'alteracao_choices': Cadastro_rpt._meta.get_field('alteracao').choices,
    })
    if request.method == "POST":
        cadastro_rpt.data_pedido = request.POST.get('data_pedido')
        cadastro_rpt.data_movimentacao = request.POST.get('data_movimentacao')
        cadastro_rpt.data_alteracao = request.POST.get('data_alteracao')
        cadastro_rpt.status = request.POST.get('status')
        cadastro_rpt.sgb_destino = request.POST.get('sgb_destino')
        cadastro_rpt.posto_secao_destino = request.POST.get('posto_secao_destino')
        cadastro_rpt.doc_solicitacao = request.POST.get('doc_solicitacao')
        cadastro_rpt.doc_alteracao = request.POST.get('doc_alteracao')
        cadastro_rpt.doc_movimentacao = request.POST.get('doc_movimentacao')
        cadastro_rpt.alteracao = request.POST.get('alteracao')

        cadastro_rpt.save()
        return redirect('rpt:ver_rpt', id=cadastro_rpt.id)
        
  

@login_required
def search_cadastro(request):
    re = request.GET.get('re', None)
    cadastro = Cadastro.objects.filter(re=re).first()
    if cadastro:
        detalhes_situacao = DetalhesSituacao.objects.filter(cadastro=cadastro).first()
        promocao = Promocao.objects.filter(cadastro=cadastro).first()
        imagem = Imagem.objects.filter(cadastro=cadastro).first()
        data = {
            'nome': cadastro.nome,
            'sgb': detalhes_situacao.sgb if detalhes_situacao else '',
            'posto_secao': detalhes_situacao.posto_secao if detalhes_situacao else '',
            'situacao': detalhes_situacao.situacao if detalhes_situacao else '',
            'posto_grad': promocao.posto_grad if promocao else '',
            'grupo': promocao.grupo if promocao else '',
            'imagem_url': imagem.image.url if imagem else '',
            'cadastro_id': cadastro.id
        }
        return JsonResponse(data)
    else:
        messages.error(request, 'Cadastro não encontrado.')
        return JsonResponse({'error': 'Cadastro não encontrado'})



from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

@login_required
def excluir_rpt(request, id):
    if request.method == 'POST':
        try:
            # Obter objetos relevantes
            cadastro = get_object_or_404(Cadastro_rpt, id=id)
            current_user = request.user
            
            # Verificar senha
            password = request.POST.get('password', '')
            if not check_password(password, current_user.password):
                messages.add_message(request, messages.ERROR, 'Senha incorreta! Operação cancelada.', 
                                   extra_tags='bg-red-500 text-white p-4 rounded')
                return redirect('rpt:ver_rpt', id=id)
            
            # Realizar exclusão
            cadastro.delete()
            messages.add_message(request, messages.SUCCESS, 'Cadastro excluído com sucesso.', 
                               extra_tags='bg-green-500 text-white p-4 rounded')
            return redirect('rpt:listar_rpt')
            
        except Exception as e:
            messages.add_message(request, messages.ERROR, f'Erro ao excluir: {str(e)}', 
                               extra_tags='bg-red-500 text-white p-4 rounded')
            return redirect('rpt:ver_rpt', id=id)
    
    return redirect('rpt:listar_rpt')



@login_required
def buscar_militar_rpt(request):
    if request.method == "POST":
        re = request.POST.get('re')
        try:
            cadastro = Cadastro.objects.get(re=re)
            detalhes = DetalhesSituacao.objects.filter(cadastro=cadastro).order_by('-id').first()
            imagem = Imagem.objects.filter(cadastro=cadastro).order_by('-id').first()
            promocao = Promocao.objects.filter(cadastro=cadastro).order_by('-id').first()

            if not detalhes:
                messages.error(request, 'Detalhes da situação não encontrados.')
                return redirect('rpt:cadastrar_rpt')
            if not promocao:
                messages.error(request, 'Promoção não encontrada.')
                return redirect('rpt:cadastrar_rpt')

            context = {
                'cadastro': cadastro,
                'detalhes': detalhes,
                'imagem': imagem,
                'promocao': promocao,
                'sgb_choices': Cadastro_rpt._meta.get_field('sgb_destino').choices,
                'posto_secao_choices': Cadastro_rpt._meta.get_field('posto_secao_destino').choices,
                'status_choices': Cadastro_rpt._meta.get_field('status').choices,
            }
            return render(request, 'cadastrar_rpt.html', context)
        except Cadastro.DoesNotExist:
            messages.add_message(request, constants.ERROR,'Cadastro nao encontrado.', extra_tags='bg-red-500 text-white p-4 rounded')
            return redirect('rpt:cadastrar_rpt')
    return render(request, 'buscar_rpt.html')


@login_required
def historico_rpt(request, id):
    cadastro_rpt = get_object_or_404(Cadastro_rpt, id=id)
    historico_rpt_list = HistoricoRpt.objects.filter(cadastro=cadastro_rpt).order_by('-data_alteracao')

    return render(request, 'historico_rpt.html', {
        'cadastro_rpt': cadastro_rpt,
        'historicoRpt': historico_rpt_list,
    })