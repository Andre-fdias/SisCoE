from django.shortcuts import render, redirect, get_object_or_404
from .models import Cadastro, DetalhesSituacao, Promocao, Imagem, HistoricoDetalhesSituacao, HistoricoPromocao
from django.contrib import messages
from django.contrib.messages import constants
from django.contrib.auth.decorators import login_required
from django.db.models import OuterRef, Subquery
from django.utils import timezone
from django.db import IntegrityError
from django.db import transaction
from backend.rpt.models import Cadastro_rpt
from django.http import HttpResponseForbidden
from django.db.models import F, Window
from django.db.models.functions import RowNumber
# backend/efetivo/views.py
from backend.municipios.models import Posto  # Supondo que Posto está no app 'municipios'

@login_required
def cadastrar_militar(request):
    if request.method == "GET":
        context = {
            'posto_grad': Promocao.posto_grad_choices,
            'quadro': Promocao.quadro_choices,
            'grupo': Promocao.grupo_choices,
            'sgb': DetalhesSituacao.sgb_choices,
            'posto_secao': DetalhesSituacao.posto_secao_choices,
            'esta_adido': DetalhesSituacao.esta_adido_choices,
            'funcao': DetalhesSituacao.funcao_choices,
            'op_adm': DetalhesSituacao.op_adm_choices,
            'prontidao': DetalhesSituacao.prontidao_choices,
            'genero': Cadastro.genero_choices,
            'situacao': DetalhesSituacao.situacao_choices,
            'cad_efetivo': DetalhesSituacao.cat_efetivo_choices,
            'alteracao': Cadastro.alteracao_choices,
         
        }
        return render(request, 'cadastrar_militar.html', context)

    elif request.method == "POST":
        print("Dados recebidos no POST:")
        print(request.POST)

        cpf = request.POST.get('cpf')
        if Cadastro.objects.filter(cpf=cpf).exists():
            messages.add_message(request, constants.ERROR, 'Erro: CPF já cadastrado.', extra_tags='bg-red-500 text-white p-4 rounded')
            return redirect('/efetivo/cadastrar_militar')

        try:
            cadastro = Cadastro(
                re=request.POST.get('re'),
                dig=request.POST.get('dig'),
                nome=request.POST.get('nome'),
                nome_de_guerra=request.POST.get('nome_de_guerra'),
                genero=request.POST.get('genero'),
                nasc=request.POST.get('nasc'),
                matricula=request.POST.get('matricula'),
                admissao=request.POST.get('admissao'),
                previsao_de_inatividade=request.POST.get('previsao_de_inatividade'),
                cpf=cpf,
                rg=request.POST.get('rg'),
                tempo_para_averbar_inss=request.POST.get('tempo_para_averbar_inss'),
                tempo_para_averbar_militar=request.POST.get('tempo_para_averbar_militar'),
                email=request.POST.get('email_funcional'),
                telefone=request.POST.get('telefone'),
                alteracao=request.POST.get('alteracao'),
                user=request.user,
       )
            cadastro.save()
            print("Cadastro salvo com sucesso")

            if request.FILES.get('image'):
                imagem = Imagem(
                    cadastro=cadastro,
                    image=request.FILES.get('image'),
                    user=request.user
                )
                imagem.save()
                print("Imagem salva com sucesso")

            try:
                detalhes = DetalhesSituacao(
                    cadastro=cadastro,
                    situacao=request.POST.get('situacao'),
                    sgb=request.POST.get('sgb'),
                    posto_secao=request.POST.get('posto_secao'),
                    esta_adido=request.POST.get('esta_adido'),
                    funcao=request.POST.get('funcao'),
                    op_adm=request.POST.get('op_adm'),
                    prontidao= request.POST.get('prontidao'),
                    apresentacao_na_unidade=request.POST.get('apresentacao_na_unidade'),
                    saida_da_unidade=request.POST.get('saida_da_unidade'),
                    usuario_alteracao=request.user
                )
                detalhes.save()
                print("Detalhes da situação salvos com sucesso")
            except Exception as e:
                print(f"Erro ao salvar detalhes da situação: {e}")
                messages.add_message(request, constants.ERROR, 'Erro ao salvar detalhes da situação.', extra_tags='bg-red-500 text-white p-4 rounded')


            try:
                promocao = Promocao(
                    cadastro=cadastro,
                    posto_grad=request.POST.get('posto_grad'),
                    quadro=request.POST.get('quadro'),
                    grupo=request.POST.get('grupo'),
                    ultima_promocao=request.POST.get('ultima_promocao'),
                    usuario_alteracao=request.user
                )
                promocao.save()
                print("Promoção salva com sucesso")
            except Exception as e:
                print(f"Erro ao salvar promoção: {e}")
                messages.add_message(request, constants.ERROR, 'Erro ao salvar promoção.', extra_tags='bg-red-500 text-white p-4 rounded')

            

            messages.add_message(request, constants.SUCCESS, 'Militar cadastrado com sucesso', extra_tags='bg-green-500 text-white p-4 rounded')
            return redirect('/efetivo/cadastrar_militar')


        except IntegrityError as e:
            if 'unique constraint' in str(e).lower():
                messages.add_message(request, constants.ERROR, 'Erro: CPF já cadastrado.')
            else:
                messages.add_message(request, constants.ERROR, 'Erro ao cadastrar militar. Por favor, tente novamente.', extra_tags='bg-red-500 text-white p-4 rounded')
            return redirect('/efetivo/cadastrar_militar')

        except Exception as e:
            print(f"Erro ao salvar os dados: {e}")
            messages.add_message(request, constants.ERROR, 'Erro ao cadastrar militar. Por favor, tente novamente.', extra_tags='bg-red-500 text-white p-4 rounded')
            return redirect('/efetivo/cadastrar_militar')




        
@login_required        
def listar_militar(request):
    if request.method == "GET":
        # Subconsulta para obter o último posto_grad de cada Cadastro
        latest_promocao = Promocao.objects.filter(cadastro=OuterRef('pk')).order_by('-ultima_promocao')
        cadastros = Cadastro.objects.annotate(
            latest_posto_grad=Subquery(latest_promocao.values('posto_grad')[:1])
        ).order_by('latest_posto_grad')
        
        # Adicione um print para verificar os dados
        for cadastro in cadastros:
            print(f"Cadastro: {cadastro}, Último Posto/Grad: {cadastro.latest_posto_grad}")
        
        return render(request, 'listar_militar.html', {
            'cadastros': cadastros
        })

    


# responsável pelo detalhamento de cada ID de militares
@login_required
def ver_militar(request, id):
    if id is None:
        messages.add_message(request, constants.ERROR, 'ID inválido', extra_tags='bg-red-500 text-white p-4 rounded')
        return redirect('/efetivo/listar_militar')


    try:
        cadastro = Cadastro.objects.get(id=id)
    except Cadastro.DoesNotExist:
        messages.add_message(request, constants.ERROR, 'Militar não encontrado', extra_tags='bg-red-500 text-white p-4 rounded')
        return redirect('/efetivo/listar_militar')

    if request.method == "GET":
        detalhes = DetalhesSituacao.objects.filter(cadastro=cadastro).last()
        promocao = Promocao.objects.filter(cadastro=cadastro).last()
         # Obter o RPT com rank global
        cadastro_rpt = Cadastro_rpt.objects.filter(cadastro=cadastro).annotate(
            global_rank=Window(
                expression=RowNumber(),
                order_by=[F('data_pedido').asc(), F('id').asc()]
            )
        ).last()

        # Contar inscritos na mesma seção
        count_in_section = 0
        if cadastro_rpt:
            count_in_section = Cadastro_rpt.objects.filter(
                posto_secao_destino=cadastro_rpt.posto_secao_destino
            ).count()
        

        return render(request, 'ver_militar.html', {
            'cadastro': cadastro,
            'detalhes': detalhes,
            'promocao': promocao,
            'cadastro_rpt': cadastro_rpt,
            'situacao': DetalhesSituacao.situacao_choices,
            'sgb': DetalhesSituacao.sgb_choices,
            'posto_secao': DetalhesSituacao.posto_secao_choices,
            'esta_adido': DetalhesSituacao.esta_adido_choices,
            'funcao': DetalhesSituacao.funcao_choices,
            'op_adm': DetalhesSituacao.op_adm_choices,
            'prontidao': DetalhesSituacao.prontidao_choices,
            'posto_grad': Promocao.posto_grad_choices,
            'quadro': Promocao.quadro_choices,
            'grupo': Promocao.grupo_choices,
            'genero': Cadastro.genero_choices,
            'cat_efetivo': DetalhesSituacao.cat_efetivo_choices,
            'alteracao': Cadastro.alteracao_choices,
            'global_rank': cadastro_rpt.global_rank if cadastro_rpt else None,
            'count_in_section': count_in_section,
        })

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password

@login_required
def excluir_militar(request, id):
    if request.method == 'POST':
        try:
            # Obter objetos relevantes
            cadastro = Cadastro.objects.get(id=id)
            current_user = request.user
            
            # Verificar senha
            password = request.POST.get('password', '')
            if not check_password(password, current_user.password):
                messages.add_message(request, constants.ERROR, 'Senha incorreta! Operação cancelada.', 
                                  extra_tags='bg-red-500 text-white p-4 rounded delete_error')  # Adicione 'delete_error'
                return redirect('efetivo:ver_militar', id=id)
            
            # Realizar exclusão
            cadastro.delete()
            messages.add_message(request, constants.SUCCESS, 'Cadastro excluído com sucesso.', 
                              extra_tags='bg-green-500 text-white p-4 rounded')
            return redirect('efetivo:listar_militar')
            
        except Cadastro.DoesNotExist:
            messages.add_message(request, constants.ERROR, 'Militar não encontrado!.', 
                              extra_tags='bg-red-500 text-white p-4 rounded')
            return redirect('efetivo:listar_militar')
        except Exception as e:
            messages.add_message(request, constants.ERROR, f'Erro ao excluir: {str(e)}', 
                              extra_tags='bg-red-500 text-white p-4 rounded delete_error')  # Adicione 'delete_error'
            return redirect('efetivo:ver_militar', id=id)
    
    return redirect('efetivo:listar_militar')


# responsável pela edição da model promoções
@login_required
def editar_posto_graduacao(request, id):
    cadastro = get_object_or_404(Cadastro, id=id)
    promocao_atual = cadastro.promocoes.last()

    if request.method == "GET":
        return render(request, 'editar_posto_graduacao.html', {
            'cadastro': cadastro,
            'promocao': promocao_atual,
            'posto_grad': Promocao.posto_grad_choices,
            'quadro': Promocao.quadro_choices,
            'grupo': Promocao.grupo_choices,
        })

    elif request.method == "POST":
        ultima_promocao = request.POST.get('ultima_promocao')
        posto_grad = request.POST.get('posto_grad')
        quadro = request.POST.get('quadro')
        grupo = request.POST.get('grupo')

        if not ultima_promocao:
         return redirect('editar_posto_graduacao', id=cadastro.id)

        if promocao_atual:
            HistoricoPromocao.objects.create(
                cadastro=cadastro,
                posto_grad=promocao_atual.posto_grad,
                quadro=promocao_atual.quadro,
                grupo=promocao_atual.grupo,
                ultima_promocao=promocao_atual.ultima_promocao,
                usuario_alteracao=request.user,
                data_alteracao=timezone.now()
            )

        nova_promocao = Promocao(
        cadastro=cadastro,
        posto_grad=posto_grad,
        quadro=quadro,
        grupo=grupo,
        ultima_promocao=ultima_promocao,
        usuario_alteracao=request.user
    )
    nova_promocao.save()
    messages.add_message(request, constants.SUCCESS, 'Dados de Posto e Graduação atualizados com sucesso.', extra_tags='bg-green-500 text-white p-4 rounded')
    return redirect('efetivo:ver_militar', id=cadastro.id)
        

from django.http import JsonResponse

@login_required
def editar_situacao_atual(request, id):
    if request.method == 'POST':
        cadastro = get_object_or_404(Cadastro, id=id)
        
        try:
            # Log dos dados recebidos
            print("Dados recebidos no POST:", request.POST)
            
            # Atualizar apenas os campos necessários
            detalhes = cadastro.detalhes_situacao.last()
            if detalhes:
                detalhes.situacao = request.POST['situacao_atual']
                detalhes.cat_efetivo = request.POST['cat_efetivo']
                detalhes.prontidao = request.POST['prontidao']
                detalhes.saida_da_unidade = request.POST.get('saida_da_unidade', None)
                detalhes.save()
            
            return JsonResponse({'success': True})

        except Exception as e:
            print(f"Erro ao salvar a situação atual: {e}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método de requisição inválido.'})


@login_required
def cadastrar_nova_situacao(request, id):
    if request.method == 'POST':
        cadastro = get_object_or_404(Cadastro, id=id)
        
        try:
            # Log dos dados recebidos
            print("Dados recebidos no POST:", request.POST)
            
            # Criar Nova Situação
            nova_situacao = DetalhesSituacao(
                cadastro=cadastro,
                situacao=request.POST['situacao'],
                sgb=request.POST['sgb'],
                posto_secao=request.POST['posto_secao'],
                esta_adido=request.POST['esta_adido'],
                funcao=request.POST['funcao'],
                op_adm=request.POST['op_adm'],
                prontidao= request.POST.get('prontidao'),
                apresentacao_na_unidade=request.POST['apresentacao_na_unidade'],
                saida_da_unidade=request.POST.get('saida_da_unidade', None),
                usuario_alteracao=request.user,
                cat_efetivo=request.POST['cat_efetivo'],
            )
            nova_situacao.save()
            
            # Atualizar o Histórico de Detalhes da Situação
            HistoricoDetalhesSituacao.objects.create(
                cadastro=cadastro,
                situacao=nova_situacao.situacao,
                sgb=nova_situacao.sgb,
                posto_secao=nova_situacao.posto_secao,
                esta_adido=nova_situacao.esta_adido,
                funcao=nova_situacao.funcao,
                op_adm=nova_situacao.op_adm,
                prontidao= nova_situacao.prontidao,
                apresentacao_na_unidade=nova_situacao.apresentacao_na_unidade,
                saida_da_unidade=nova_situacao.saida_da_unidade,
                data_alteracao=nova_situacao.data_alteracao,
                usuario_alteracao=request.user,
                cat_efetivo=nova_situacao.cat_efetivo,
            )
         
            messages.add_message(request, constants.SUCCESS, 'Criada Nova Situação Funcional com sucesso.', 
            extra_tags='bg-green-500 text-white p-4 rounded')
            return redirect('efetivo:ver_militar', id=cadastro.id)

        except Exception as e:
            print(f"Erro ao cadastrar a nova situação: {e}")
            messages.add_message(request, constants.ERROR, 'Erro ao cadastrar nova situação.', 
                              extra_tags='bg-red-500 text-white p-4 rounded')  # SEM 'delete_error'
            return redirect('efetivo:ver_militar', id=cadastro.id)
    
    messages.add_message(request, constants.ERROR, 'Método de Requisição errado.', 
                      extra_tags='bg-red-500 text-white p-4 rounded')  # SEM 'delete_error'
    return redirect('efetivo:ver_militar', id=id)



# responsável pela edição da model cadastro
@login_required
def editar_dados_pessoais_contatos(request, id):
    cadastro = get_object_or_404(Cadastro, id=id)
    historico_promocoes = HistoricoPromocao.objects.filter(cadastro=cadastro).order_by('-data_alteracao')
    historico_detalhes_situacao = HistoricoDetalhesSituacao.objects.filter(cadastro=cadastro).order_by('-data_alteracao')

    if request.method == "GET":
        return render(request, 'editar_dados_pessoais_contatos.html', {
            'cadastro': cadastro,
            'genero': Cadastro.genero_choices,
            'historico_promocoes': historico_promocoes,
            'historico_detalhes_situacao': historico_detalhes_situacao,
        })

    elif request.method == "POST":
        cadastro.re = request.POST.get('re')
        cadastro.dig = request.POST.get('dig')
        cadastro.nome = request.POST.get('nome')
        cadastro.nome_de_guerra = request.POST.get('nome_de_guerra')
        cadastro.genero = request.POST.get('genero')
        cadastro.nasc = request.POST.get('nasc')
        cadastro.matricula = request.POST.get('matricula')
        cadastro.admissao = request.POST.get('admissao')
        cadastro.previsao_de_inatividade = request.POST.get('previsao_de_inatividade')
        cadastro.cpf = request.POST.get('cpf')
        cadastro.rg = request.POST.get('rg')
        cadastro.tempo_para_averbar_inss = request.POST.get('tempo_para_averbar_inss')
        cadastro.tempo_para_averbar_militar = request.POST.get('tempo_para_averbar_militar')
        cadastro.email = request.POST.get('email')
        cadastro.telefone = request.POST.get('telefone')
      
        cadastro.save()
        messages.add_message(request, constants.SUCCESS, 'Dados Pessoais e Contatos atualizados com sucesso', extra_tags='bg-green-500 text-white p-4 rounded')
        return redirect('efetivo:ver_militar', id=cadastro.id)


@login_required
def editar_imagem(request, id):
    
    cadastro = get_object_or_404(Cadastro, id=id)

    if request.method == "POST":
        if request.FILES.get('image'):
            nova_imagem = Imagem(
                cadastro=cadastro,
                image=request.FILES.get('image'),
                user=request.user
            )
            nova_imagem.save()
            messages.add_message(request, constants.SUCCESS, 'Imagem atualizada com sucesso', extra_tags='bg-green-500 text-white p-4 rounded')
        else:
            messages.add_message(request, constants.ERROR, 'Por favor, envie uma imagem válida.', extra_tags='bg-red-500 text-white p-4 rounded')

        return redirect('efetivo:ver_militar', id=cadastro.id)

    return render(request, 'editar_imagem.html', {
        'cadastro': cadastro,
        'imagem': cadastro.imagens.last()
    })


# responsável por armazenar os dados de movimentação
@login_required
def historico_movimentacoes(request, id):
    cadastro = get_object_or_404(Cadastro, id=id)
    promocoes = Promocao.objects.filter(cadastro=cadastro).order_by('-data_alteracao')
    historico_detalhes_situacao = HistoricoDetalhesSituacao.objects.filter(cadastro=cadastro).order_by('-data_alteracao')

    return render(request, 'historico_movimentacoes.html', {
        'cadastro': cadastro,
        'promocoes': promocoes,
        'historico_detalhes_situacao': historico_detalhes_situacao,
    })


# responsável pela edição da model De
@login_required
def editar_situacao_funcional(request, id):
    cadastro = get_object_or_404(Cadastro, id=id)
    
    if request.method == 'POST':
        try:
            # Atualizar a Situação Atual
            cadastro.situacao = request.POST['situacao_atual']
            cadastro.save()
            
            # Criar Nova Situação
            nova_situacao = DetalhesSituacao(
                cadastro=cadastro,
                situacao=request.POST['situacao'],
                sgb=request.POST['sgb'],
                posto_secao=request.POST['posto_secao'],
                esta_adido=request.POST['esta_adido'],
                funcao=request.POST['funcao'],
                op_adm=request.POST['op_adm'],
                apresentacao_na_unidade=request.POST['apresentacao_na_unidade'],
                saida_da_unidade=request.POST.get('saida_da_unidade', None),
                cat_efetivo=request.POST('cat_efetivo'),
            )
            nova_situacao.save()
            
            # Atualizar o Histórico de Detalhes da Situação
            HistoricoDetalhesSituacao.objects.create(
                cadastro=cadastro,
                situacao=nova_situacao.situacao,
                sgb=nova_situacao.sgb,
                posto_secao=nova_situacao.posto_secao,
                esta_adido=nova_situacao.esta_adido,
                funcao=nova_situacao.funcao,
                op_adm=nova_situacao.op_adm,
                apresentacao_na_unidade=nova_situacao.apresentacao_na_unidade,
                saida_da_unidade=nova_situacao.saida_da_unidade,
                data_alteracao=nova_situacao.data_alteracao,
                usuario_alteracao=request.user,
                cat_efetivo=nova_situacao.cat_efetivo,
            )
            messages.add_message(request, constants.SUCCESS, 'Situação funcional atualizada com sucesso!', extra_tags='bg-green-500 text-white p-4 rounded')

        except Exception as e:
            messages.add_message(request, constants.SUCCESS, 'Dados de Posto e Graduação atualizados com sucesso.', extra_tags='bg-green-500 text-white p-4 rounded')
            messages.error(request, f'Ocorreu um erro ao atualizar a situação funcional: {e}', extra_tags='bg-red-500 text-white p-4 rounded')

          # Permanecer na mesma URL após salvar
        return redirect('editar_situacao_funcional', id=id)
        
    # Renderizar o formulário de edição com os dados atuais
    return render(request, 'editar_situacao_funcional.html', {
        'cadastro': cadastro,
        'situacao': DetalhesSituacao.objects.all(),
        'sgb_choices': DetalhesSituacao._meta.get_field('sgb').choices,
        'posto_secao_choices': DetalhesSituacao._meta.get_field('posto_secao').choices,
        'esta_adido_choices': DetalhesSituacao._meta.get_field('esta_adido').choices,
        'funcao_choices': DetalhesSituacao._meta.get_field('funcao').choices,
        'op_adm_choices': DetalhesSituacao._meta.get_field('op_adm').choices,
        'cat_efetivo': DetalhesSituacao._meta.get_field('cat_efetivo').choices,
        'detalhes': cadastro.detalhes_situacao.last()
    })


from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from backend.rpt.models import Cadastro_rpt
from backend.efetivo.models import Cadastro

@login_required
def check_rpt(request, id):
    cadastro = get_object_or_404(Cadastro, id=id)
    exists = Cadastro_rpt.objects.filter(cadastro=cadastro).exists()
    return JsonResponse({'exists': exists})

# backend/efetivo/views.py
# backend/efetivo/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Q
from .models import Cadastro, Imagem, Promocao, DetalhesSituacao
from backend.municipios.models import Posto
from datetime import datetime

@login_required
def detalhar_efetivo(request, posto_id):
    posto = get_object_or_404(Posto, pk=posto_id)
    
    # Ordem hierárquica dos postos/grads
    ORDEM_POSTOS = [
        "Cel PM", "Ten Cel PM", "Maj PM", "CAP PM",
        "1º Ten PM", "1º Ten QAPM", "2º Ten PM", "2º Ten QAPM", "Asp OF PM",
        "Subten PM", "1º Sgt PM", "2º Sgt PM", "3º Sgt PM",
        "Cb PM", "Sd PM", "Sd PM 2ºCL"
    ]
    
    # Obtém o prefixo do posto_secao (7 primeiros dígitos)
    posto_secao_prefixo = posto.posto_secao[:7]
    
    # Otimizando as consultas
    militares_queryset = Cadastro.objects.filter(
        Q(detalhes_situacao__posto_secao=posto.posto_secao) |
        Q(detalhes_situacao__funcao="CMT_PB", detalhes_situacao__posto_secao__startswith=posto_secao_prefixo)
    ).select_related(
        'user'
    ).prefetch_related(
        Prefetch('imagens', queryset=Imagem.objects.all().order_by('-create_at')),
        Prefetch('promocoes', queryset=Promocao.objects.all().order_by('-ultima_promocao')),
        Prefetch('detalhes_situacao', queryset=DetalhesSituacao.objects.all().order_by('-data_alteracao'))
    ).distinct()
    
    # Converter QuerySet para lista para poder ordenar
    militares = list(militares_queryset)
    
    # Função para ordenação
    def get_ordenacao(militar):
        ultima_promocao = militar.promocoes.first()  # Já está ordenado por '-ultima_promocao' no prefetch
        if ultima_promocao:
            posto_grad = ultima_promocao.posto_grad
            try:
                ordem_posto = ORDEM_POSTOS.index(posto_grad)
            except ValueError:
                ordem_posto = len(ORDEM_POSTOS)  # Coloca no final se não estiver na lista
            data_promocao = ultima_promocao.ultima_promocao or datetime.min.date()
        else:
            ordem_posto = len(ORDEM_POSTOS)
            data_promocao = datetime.min.date()
        
        return (ordem_posto, -data_promocao.toordinal())  # Negativo para ordenar decrescente
    
    # Ordenar os militares
    militares.sort(key=get_ordenacao)
    
    # Obtém o comandante separadamente para facilitar no template
    comandante = next(
        (m for m in militares if any(
            d.funcao == "CMT_PB" and d.posto_secao.startswith(posto_secao_prefixo)
            for d in m.detalhes_situacao.all()
        )),
        None
    )
    
    # Remover o comandante da lista de militares (se existir)
    if comandante:
        militares = [m for m in militares if m.id != comandante.id]
    
    context = {
        'posto': posto,
        'militares': militares,
        'comandante': comandante,
        'unidade_nome': posto.posto_secao,
        'posto_secao_prefixo': posto_secao_prefixo
    }
    return render(request, 'detalhes_efetivo.html', context)
    posto = get_object_or_404(Posto, pk=posto_id)
    
    # Ordem hierárquica dos postos/grads
    ORDEM_POSTOS = [
        "Cel PM", "Ten Cel PM", "Maj PM", "CAP PM",
        "1º Ten PM", "1º Ten QAPM", "2º Ten PM", "2º Ten QAPM", "Asp OF PM",
        "Subten PM", "1º Sgt PM", "2º Sgt PM", "3º Sgt PM",
        "Cb PM", "Sd PM", "Sd PM 2ºCL"
    ]
    
    # Obtém o prefixo do posto_secao (7 primeiros dígitos)
    posto_secao_prefixo = posto.posto_secao[:7]
    
    # Otimizando as consultas
    militares_queryset = Cadastro.objects.filter(
        Q(detalhes_situacao__posto_secao=posto.posto_secao) |
        Q(detalhes_situacao__funcao="CMT_PB", detalhes_situacao__posto_secao__startswith=posto_secao_prefixo)
    ).select_related(
        'user'
    ).prefetch_related(
        Prefetch('imagens', queryset=Imagem.objects.all().order_by('-create_at')),
        Prefetch('promocoes', queryset=Promocao.objects.all().order_by('-data_')),
        Prefetch('detalhes_situacao', queryset=DetalhesSituacao.objects.all().order_by('-data_alteracao'))
    ).distinct()
    
    # Converter QuerySet para lista para poder ordenar
    militares = list(militares_queryset)
    
    # Função para ordenação
    def get_ordenacao(militar):
        ultima_promocao = militar.promocoes.first()  # Já está ordenado por '-data' no prefetch
        if ultima_promocao:
            posto_grad = ultima_promocao.posto_grad
            try:
                ordem_posto = ORDEM_POSTOS.index(posto_grad)
            except ValueError:
                ordem_posto = len(ORDEM_POSTOS)  # Coloca no final se não estiver na lista
            data_promocao = ultima_promocao.data or datetime.min.date()
        else:
            ordem_posto = len(ORDEM_POSTOS)
            data_promocao = datetime.min.date()
        
        return (ordem_posto, -data_promocao.toordinal())  # Negativo para ordenar decrescente
    
    # Ordenar os militares
    militares.sort(key=get_ordenacao)
    
    # Obtém o comandante separadamente para facilitar no template
    comandante = next(
        (m for m in militares if any(
            d.funcao == "CMT_PB" and d.posto_secao.startswith(posto_secao_prefixo)
            for d in m.detalhes_situacao.all()
        )),
        None
    )
    
    # Remover o comandante da lista de militares (se existir)
    if comandante:
        militares = [m for m in militares if m.id != comandante.id]
    
    context = {
        'posto': posto,
        'militares': militares,
        'comandante': comandante,
        'unidade_nome': posto.posto_secao,
        'posto_secao_prefixo': posto_secao_prefixo
    }
    return render(request, 'detalhes_efetivo.html', context)