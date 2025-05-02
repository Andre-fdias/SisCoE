from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from datetime import datetime, date, timedelta

from .models import Cadastro_adicional, HistoricoCadastro, LP, HistoricoLP
from backend.efetivo.models import Cadastro, DetalhesSituacao, Promocao, Imagem

@login_required
def cadastrar_lp(request):
    """
    View para cadastrar Adicional e LP para um militar.
    """
    if request.method == 'GET':
        return render(request, 'cadastrar_lp.html')

    elif request.method == 'POST':
        # Obtenção dos dados do formulário
        n_bloco_adicional = request.POST.get('n_bloco_adicional')
        n_bloco_lp = request.POST.get('n_bloco_lp')
        cadastro_id = request.POST.get('cadastro_id')
        data_ultimo_adicional_str = request.POST.get('data_ultimo_adicional')
        data_ultimo_lp_str = request.POST.get('data_ultimo_lp')
        situacao_adicional = request.POST.get('situacao_adicional')
        situacao_lp = request.POST.get('situacao_lp')
        dias_desconto_adicional = int(request.POST.get('dias_desconto_adicional', 0) or 0)
        dias_desconto_lp = int(request.POST.get('dias_desconto_lp', 0) or 0)
        sexta_parte = request.POST.get('sexta_parte_hidden', 'False') == 'True'  # Campo oculto
        user = request.user

        # Validações básicas
        if not cadastro_id:
            messages.error(request, 'Cadastro do militar não localizado.')
            return redirect('adicional:cadastrar_lp')

        cadastro = get_object_or_404(Cadastro, id=cadastro_id)

        if not data_ultimo_adicional_str:
            messages.error(request, 'Favor inserir a data de concessão do último Adicional')
            return redirect('adicional:cadastrar_lp')

        if not data_ultimo_lp_str:
            messages.error(request, 'Favor inserir a data de concessão da última LP')
            return redirect('adicional:cadastrar_lp')

        try:
            # Conversão de datas
            data_ultimo_adicional = datetime.strptime(data_ultimo_adicional_str, '%Y-%m-%d').date()
            data_ultimo_lp = datetime.strptime(data_ultimo_lp_str, '%Y-%m-%d').date()

            # Validação dos números de bloco
            if not n_bloco_adicional or not n_bloco_adicional.isdigit():
                messages.error(request, 'Número do Bloco Adicional inválido.')
                return redirect('adicional:cadastrar_lp')
            if not n_bloco_lp or not n_bloco_lp.isdigit():
                messages.error(request, 'Número do Bloco LP inválido.')
                return redirect('adicional:cadastrar_lp')

            numero_adicional = int(n_bloco_adicional)
            numero_prox_adicional = numero_adicional + 1
            proximo_adicional = data_ultimo_adicional + timezone.timedelta(days=365 * 5) - timezone.timedelta(days=dias_desconto_adicional)
            mes_proximo_adicional = proximo_adicional.month
            ano_proximo_adicional = proximo_adicional.year

            numero_lp = int(n_bloco_lp)
            numero_prox_lp = numero_lp + 1
            proximo_lp = data_ultimo_lp + timezone.timedelta(days=365 * 5) - timezone.timedelta(days=dias_desconto_lp)
            mes_proximo_lp = proximo_lp.month
            ano_proximo_lp = proximo_lp.year

            with transaction.atomic():
                # Criação do Adicional
                adicional = Cadastro_adicional.objects.create(
                    cadastro=cadastro,
                    user_created=user,
                    numero_adicional=numero_adicional,
                    data_ultimo_adicional=data_ultimo_adicional,
                    numero_prox_adicional=numero_prox_adicional,
                    proximo_adicional=proximo_adicional,
                    mes_proximo_adicional=mes_proximo_adicional,
                    ano_proximo_adicional=ano_proximo_adicional,
                    dias_desconto_adicional=dias_desconto_adicional,
                    situacao_adicional=situacao_adicional,
                    sexta_parte=sexta_parte
                )

                # Criação da LP
                lp = LP.objects.create(
                    cadastro=cadastro,
                    user_created=user,
                    numero_lp=numero_lp,
                    data_ultimo_lp=data_ultimo_lp,
                    numero_prox_lp=numero_prox_lp,
                    proximo_lp=proximo_lp,
                    mes_proximo_lp=mes_proximo_lp,
                    ano_proximo_lp=ano_proximo_lp,
                    dias_desconto_lp=dias_desconto_lp,
                    situacao_lp=situacao_lp
                )

                # Registrar no histórico do Adicional
                HistoricoCadastro.objects.create(
                    cadastro_adicional=adicional,
                    situacao_adicional=situacao_adicional,
                    usuario_alteracao=user,
                    numero_prox_adicional=numero_prox_adicional,
                    proximo_adicional=proximo_adicional,
                    mes_proximo_adicional=mes_proximo_adicional,
                    ano_proximo_adicional=ano_proximo_adicional,
                    dias_desconto_adicional=dias_desconto_adicional
                )

                # Registrar no histórico da LP
                HistoricoLP.objects.create(
                    lp=lp,
                    situacao_lp=situacao_lp,
                    usuario_alteracao=user,
                    numero_prox_lp=numero_prox_lp,
                    proximo_lp=proximo_lp,
                    mes_proximo_lp=mes_proximo_lp,
                    ano_proximo_lp=ano_proximo_lp,
                    dias_desconto_lp=dias_desconto_lp
                )

            messages.success(request, 'Adicional e LP cadastrados com sucesso!')
            return redirect('adicional:listar_lp')

        except ValueError as e:
            messages.error(request, f'Formato de data inválido. Use o formato AAAA-MM-DD. Erro: {str(e)}')
            return redirect('adicional:cadastrar_lp')
        except Exception as e:
            messages.error(request, f'Ocorreu um erro ao cadastrar: {str(e)}')
            return redirect('adicional:cadastrar_lp')

    return render(request, 'cadastrar_lp.html')


@login_required
def buscar_militar_adicional(request):
    """
    View para buscar um militar pelo RE e exibir seus dados para cadastro de adicional e LP.
    """
    if request.method == "POST":
        re = request.POST.get('re')
        try:
            cadastro = Cadastro.objects.get(re=re)
            detalhes = DetalhesSituacao.objects.filter(cadastro=cadastro).order_by('-id').first()
            imagem = Imagem.objects.filter(cadastro=cadastro).order_by('-id').first()
            promocao = Promocao.objects.filter(cadastro=cadastro).order_by('-id').first()

            if not detalhes:
                messages.error(request, 'Detalhamento não encontrado')
                return redirect('adicional:cadastrar_lp')
            if not promocao:
                messages.error(request, 'Dados de Posto e graduação não localizados')
                return redirect('adicional:cadastrar_lp')

            context = {
                'cadastro': cadastro,
                'detalhes': detalhes,
                'imagem': imagem,
                'promocao': promocao,
            }
            return render(request, 'cadastrar_lp.html', context)
        except Cadastro.DoesNotExist:
            messages.error(request, 'Militar não cadastrado no sistema')
            return redirect('adicional:cadastrar_lp')

    return render(request, 'buscar_adicional.html')

@login_required
def listar_lp(request):
    """
    View para listar todos os Adicionais e LPs cadastrados.
    """
    registros_adicional = Cadastro_adicional.objects.all() # Alterado para pegar todos os registros
    registros_lp = LP.objects.all()

    current_year = datetime.now().year
    anos = list(range(2018, current_year + 2))  # Inclui o próximo ano

    context = {
        'registros_adicional': registros_adicional,
        'registros_lp': registros_lp,
        'anos': anos,
    }

    return render(request, 'listar_lp.html', context)


# Exibe os detalhes de um registro específico LP

def ver_lp(request, id):
    """
    View para exibir os detalhes de um registro de Adicional e LP.
    """
    # Obtém o cadastro de adicional
    cadastro_adicional = get_object_or_404(Cadastro_adicional, id=id)

    # Tenta obter o registro de LP associado ao mesmo cadastro
    try:
        cadastro_lp = LP.objects.get(cadastro=cadastro_adicional.cadastro)
    except LP.DoesNotExist:
        cadastro_lp = None

    # Obter todos os registros deste militar ordenados por data
    historico_adicional = Cadastro_adicional.objects.filter(
        cadastro=cadastro_adicional.cadastro
    ).order_by('-data_ultimo_adicional')

    historico_lp = LP.objects.filter(
        cadastro=cadastro_adicional.cadastro
    ).order_by('-data_ultimo_lp')

    context = {
        'cadastro_adicional': cadastro_adicional,
        'cadastro_lp': cadastro_lp,
        'historico_adicional': historico_adicional,
        'historico_lp': historico_lp,
    }
    return render(request, 'ver_lp.html', context)


@login_required
def editar_lp(request, id):
    """
    View para editar um registro de LP existente
    """
    lp = get_object_or_404(LP, id=id)

    if request.method == 'POST':
        try:
            data_ultimo_lp_str = request.POST.get('data_ultimo_lp')

            if not data_ultimo_lp_str:
                messages.error(request, 'Data da última LP é obrigatória')
                return redirect(reverse('adicional:editar_lp', args=[id]))

            data_ultimo_lp = datetime.strptime(data_ultimo_lp_str, '%Y-%m-%d').date()

            # Atualiza os campos
            lp.numero_lp = int(request.POST.get('numero_lp'))
            lp.data_ultimo_lp = data_ultimo_lp
            lp.dias_desconto_lp = int(request.POST.get('dias_desconto_lp', 0))
            lp.situacao_lp = request.POST.get('situacao_lp')
            lp.save()

            messages.success(request, 'LP atualizada com sucesso')
            return redirect(reverse('adicional:ver_lp', args=[id]))

        except ValueError as e:
            messages.error(request, f'Erro ao processar os dados: {str(e)}')
            return redirect(reverse('adicional:editar_lp', args=[id]))

    context = {
        'lp': lp,
    }
    return render(request, 'adicional/editar_lp.html', context)

@login_required
def excluir_lp(request, id):
    """
    View para excluir um registro de LP
    """
    lp = get_object_or_404(LP, id=id)

    if request.method == 'POST':
        try:
            password = request.POST.get('password')
            user = authenticate(request, username=request.user.username, password=password)

            if not user or user != request.user:
                messages.error(request, 'Autenticação falhou - senha incorreta')
                return redirect(reverse('adicional:ver_lp', args=[id]))

            lp.delete()
            messages.success(request, 'LP excluída com sucesso')
            return redirect('adicional:listar_lp')

        except Exception as e:
            messages.error(request, f'Erro ao excluir: {str(e)}')
            return redirect(reverse('adicional:ver_lp', args=[id]))

    return redirect(reverse('adicional:ver_lp', args=[id]))


from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .models import Cadastro_adicional, HistoricoCadastro

def gravar_historico(instance, usuario_alteracao):
    """
    Grava um snapshot completo do Cadastro_adicional no histórico
    """
    HistoricoCadastro.objects.create(
        cadastro_adicional=instance,
        usuario_alteracao=usuario_alteracao,
        
        # Copia todos os campos relevantes
        cadastro=instance.cadastro,
        user_created=instance.user_created,
        user_updated=instance.user_updated,
        usuario_conclusao=instance.usuario_conclusao,
        created_at=instance.created_at,
        updated_at=instance.updated_at,
        data_conclusao=instance.data_conclusao,
        numero_adicional=instance.numero_adicional,
        data_ultimo_adicional=instance.data_ultimo_adicional,
        numero_prox_adicional=instance.numero_prox_adicional,
        proximo_adicional=instance.proximo_adicional,
        mes_proximo_adicional=instance.mes_proximo_adicional,
        ano_proximo_adicional=instance.ano_proximo_adicional,
        dias_desconto_adicional=instance.dias_desconto_adicional,
        situacao_adicional=instance.situacao_adicional,
        sexta_parte=instance.sexta_parte,
        confirmacao_6parte=instance.confirmacao_6parte,
        data_concessao_adicional=instance.data_concessao_adicional,
        bol_g_pm_adicional=instance.bol_g_pm_adicional,
        data_publicacao_adicional=instance.data_publicacao_adicional,
        status_adicional=instance.status_adicional
    )

@login_required
@require_http_methods(["GET"])
def historico_adicional(request, id):
    """
    View para exibir o histórico completo de um adicional
    """
    adicional = get_object_or_404(
        Cadastro_adicional.objects.select_related('cadastro'),
        id=id
    )
    
    historicos = HistoricoCadastro.objects.filter(
        cadastro_adicional=adicional
    ).select_related(
        'usuario_alteracao'
    ).order_by('-data_alteracao')

    context = {
        'adicional': adicional,
        'historicos': historicos,
        'campos_historicos': [
            ('data_alteracao', 'Data Alteração'),
            ('usuario_alteracao', 'Responsável'),
            ('numero_adicional', 'Bloco'),
            ('situacao_adicional', 'Situação'),
            ('status_adicional', 'Status'),
            ('data_publicacao_adicional', 'Data Publicação'),
            ('bol_g_pm_adicional', 'BOL GPm')
        ]
    }
    
    return render(request, 'adicional/historico_adicional.html', context)

@login_required
def historico_lp(request, id):
    """
    View para exibir o histórico de uma LP
    """
    lp = get_object_or_404(LP, id=id)
    historicos = HistoricoLP.objects.filter(lp=lp).order_by('-data_alteracao')

    context = {
        'lp': lp,
        'historicos': historicos,
    }
    return render(request, 'historico_lp.html', context)

@login_required
def concluir_lp(request, id):
    """
    Processa a conclusão de uma licença prêmio com todas as validações
    """
    cadastro = get_object_or_404(Cadastro_adicional, id=id)

    if request.method == 'POST':
        try:
            # Validações básicas
            password = request.POST.get('password')
            data_concessao_str = request.POST.get('data_concessao')

            if not data_concessao_str:
                raise ValidationError("A data de concessão é obrigatória")

            data_concessao = date.fromisoformat(data_concessao_str)

            if data_concessao > date.today():
                raise ValidationError("A data de concessão não pode ser no futuro")

            # Validação do usuário
            user = authenticate(request, username=request.user.username, password=password)
            if not user or user != request.user:
                raise ValidationError("Autenticação falhou - senha incorreta")

            # Atualização do registro atual
            cadastro.situacao_lp = "Concluído"
            cadastro.data_concessao_lp = data_concessao
            cadastro.data_conclusao_lp = timezone.now()
            cadastro.usuario_conclusao_lp = request.user
            cadastro.save()

            # Criação do novo registro
            novo_lp = Cadastro_adicional.objects.create(
                cadastro=cadastro.cadastro,
                numero_adicional=cadastro.numero_adicional,
                data_ultimo_adicional=cadastro.data_ultimo_adicional,
                numero_lp=cadastro.numero_prox_lp,
                data_ultimo_lp=data_concessao,  # Usa a data informada no modal
                user_created=request.user,
                situacao_adicional=cadastro.situacao_adicional,
                situacao_lp="Aguardando",
                dias_desconto_adicional=0,
                dias_desconto_lp=0
            )

            # Registro no histórico
            HistoricoCadastro.objects.create(
                    cadastro_adicional=novo_lp,
                    situacao_adicional=novo_lp.situacao_adicional,
                    situacao_lp="Aguardando",
                    usuario_alteracao=request.user,
                    numero_prox_adicional=novo_lp.numero_prox_adicional,
                    proximo_adicional=novo_lp.proximo_adicional,
                    mes_proximo_adicional=novo_lp.mes_proximo_adicional,
                    ano_proximo_adicional=novo_lp.ano_proximo_adicional,
                    dias_desconto_adicional=0,
                )

            messages.success(request, 'Licença Prêmio concluída com sucesso!')
            return redirect(reverse('adicional:ver_lp', args=[novo_lp.id]))

        except ValidationError as e:
            messages.error(request, str(e), extra_tags='concluir_lp')
        except Exception as e:
            messages.error(request, f'Erro: {str(e)}', extra_tags='concluir_lp')

        return redirect(reverse('adicional:ver_lp', args=[id]))



@login_required
@permission_required('adicional.can_concluir_adicional', raise_exception=True)
def concluir_adicional(request, id):
    """
    Processa a conclusão de um adicional com todas as validações
    """
    adicional = get_object_or_404(Cadastro_adicional, id=id)

    if not request.method == 'POST':
        return redirect(reverse('adicional:ver_adicional', args=[id]))

    try:
        # Validações iniciais
        if adicional.situacao_adicional == "Concluído":
            raise ValidationError("Este adicional já foi concluído")

        # Validação de senha
        password = request.POST.get('password')
        user = authenticate(request, username=request.user.username, password=password)
        if not user or user != request.user:
            raise ValidationError("Autenticação falhou - senha incorreta")

        # Validação de dados
        data_concessao_str = request.POST.get('data_concessao')
        if not data_concessao_str:
            raise ValidationError("A data de concessão é obrigatória")

        data_concessao = date.fromisoformat(data_concessao_str)
        if data_concessao > date.today():
            raise ValidationError("A data de concessão não pode ser no futuro")

        # Validação específica para 6ª Parte
        if adicional.numero_prox_adicional == 4:
            sexta_parte = request.POST.get('sexta_parte') == 'on'
            if not sexta_parte:
                raise ValidationError("Confirmação da 6ª Parte é obrigatória")
            adicional.confirmacao_6parte = True

        # Atualização do registro atual
        adicional.situacao_adicional = "Concluído"
        adicional.status_adicional = "encerrado"
        adicional.data_concessao_adicional = data_concessao
        adicional.usuario_conclusao = request.user
        adicional.data_conclusao = timezone.now()

        if adicional.numero_prox_adicional == 4:
            adicional.sexta_parte = True

        # Criação do novo registro antes de salvar o atual
        novo_adicional = Cadastro_adicional(
            cadastro=adicional.cadastro,
            numero_adicional=adicional.numero_prox_adicional,
            data_ultimo_adicional=data_concessao,
            user_created=request.user,
            situacao_adicional="Aguardando",
            status_adicional="aguardando_requisitos",
            dias_desconto_adicional=0
        )

        # Salva ambos os registros em transação
        with transaction.atomic():
            adicional.save()
            novo_adicional.save()

            # Atualiza o próximo adicional com base no último salvo
            novo_adicional.numero_prox_adicional = novo_adicional.numero_adicional + 1
            novo_adicional.proximo_adicional = novo_adicional.data_ultimo_adicional + timedelta(days=1825)
            novo_adicional.save()

        messages.success(request, 'Adicional concluído com sucesso! Foi criado um novo registro para o próximo período.')
        return redirect(reverse('adicional:ver_adicional', args=[novo_adicional.id]))

    except ValidationError as e:
        messages.error(request, str(e), extra_tags='concluir_adicional')
    except Exception as e:
        messages.error(request, f'Erro inesperado: {str(e)}', extra_tags='concluir_adicional')

    return redirect(reverse('adicional:ver_adicional', args=[id]))


# Exibe os detalhes de um registro específico ADICIONAL
from datetime import datetime
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Cadastro_adicional, HistoricoCadastro

@login_required
def ver_adicional(request, id):
    """
    View para exibir os detalhes de um registro de Adicional
    """
    adicional = get_object_or_404(
        Cadastro_adicional.objects.select_related('cadastro', 'user_created', 'user_updated'),
        id=id
    )
    
    # Histórico de alterações do adicional específico
    historico_alteracoes = HistoricoCadastro.objects.filter(
        cadastro_adicional=adicional
    ).order_by('-data_alteracao')
    
    # Histórico de todos adicionais encerrados do militar
    historico_encerrados = Cadastro_adicional.objects.filter(
        cadastro=adicional.cadastro,
        status_adicional=Cadastro_adicional.StatusAdicional.ENCERRADO
    ).exclude(id=id).order_by('-data_ultimo_adicional')

    context = {
        'cadastro_adicional': adicional,  # Nome corrigido para bater com o template
        'historico_alteracoes': historico_alteracoes,
        'historico_encerrados': historico_encerrados,
        'current_year': datetime.now().year,
    }
    return render(request, 'detalhar_adicional.html', context)

@login_required
def editar_adicional(request, id):
    """
    View para editar um registro de Adicional existente
    """
    adicional = get_object_or_404(Cadastro_adicional, id=id)

    if request.method == 'POST':
        try:
            data_ultimo_adicional_str = request.POST.get('data_ultimo_adicional')

            if not data_ultimo_adicional_str:
                messages.error(request, 'Data do último adicional é obrigatória')
                return redirect(reverse('adicional:editar_adicional', args=[id]))

            data_ultimo_adicional = datetime.strptime(data_ultimo_adicional_str, '%Y-%m-%d').date()

            # Atualiza os campos
            adicional.numero_adicional = int(request.POST.get('numero_adicional'))
            adicional.data_ultimo_adicional = data_ultimo_adicional
            adicional.dias_desconto_adicional = int(request.POST.get('dias_desconto_adicional', 0))
            adicional.situacao_adicional = request.POST.get('situacao_adicional')

            if 'sexta_parte' in request.POST:
                adicional.sexta_parte = True
            else:
                adicional.sexta_parte = False

            adicional.save()

            messages.success(request, 'Adicional atualizado com sucesso')
            return redirect(reverse('adicional:ver_adicional', args=[id]))

        except ValueError as e:
            messages.error(request, f'Erro ao processar os dados: {str(e)}')
            return redirect(reverse('adicional:editar_adicional', args=[id]))

    context = {
        'adicional': adicional,
    }
    return render(request, 'editar_adicional.html', context)

@login_required
def excluir_adicional(request, id):
    """
    View para excluir um registro de Adicional
    """
    adicional = get_object_or_404(Cadastro_adicional, id=id)

    if request.method == 'POST':
        try:
            password = request.POST.get('password')
            user = authenticate(request, username=request.user.username, password=password)

            if not user or user != request.user:
                messages.error(request, 'Autenticação falhou - senha incorreta')
                return redirect(reverse('adicional:ver_adicional', args=[id]))

            adicional.delete()
            messages.success(request, 'Adicional excluído com sucesso')
            return redirect('adicional:listar_lp')

        except Exception as e:
            messages.error(request, f'Erro ao excluir: {str(e)}')
            return redirect(reverse('adicional:ver_adicional', args=[id]))

    return redirect(reverse('adicional:ver_adicional', args=[id]))


# Views para LP
@login_required
def ver_lp(request, id):
    """
    View para exibir os detalhes de um registro de LP
    """
    lp = get_object_or_404(LP, id=id)
    historico_lp = HistoricoLP.objects.filter(lp=lp).order_by('-data_alteracao')

    context = {
        'lp': lp,
        'historico_lp': historico_lp,
        'current_year': datetime.now().year,
    }
    return render(request, 'detalhar_lp.html', context)

    # views.py
# views.py
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404

# views.py
def editar_dias_desconto(request, pk):
    if request.method == 'POST':
        adicional = get_object_or_404(Cadastro_adicional, pk=pk)
        try:
            dias_desconto = int(request.POST.get('dias_desconto', 0))
            if dias_desconto < 0:
                raise ValueError("Dias de desconto não podem ser negativos")

            adicional.dias_desconto_adicional = dias_desconto
            adicional.save()
            messages.success(request, "Dias de desconto atualizados com sucesso!")
        except ValueError as e:
            messages.error(request, str(e), extra_tags='dias_desconto')

        # Redireciona para a página de visualização do adicional
        return redirect('adicional:ver_adicional', id=pk)

    # Fallback para requisições GET
    return redirect('adicional:ver_adicional', id=pk)


@login_required
def editar_concessao(request, pk):
    adicional = get_object_or_404(Cadastro_adicional, id=pk)

    if request.method == 'POST':
        try:
            # Verificar se o usuário está autenticado
            if not request.user.is_authenticated:
                messages.error(request, 'Usuário não autenticado', extra_tags='concessao')
                return redirect('adicional:ver_adicional', id=pk)
            
            # Atualizar data de concessão
            data_concessao = request.POST.get('data_concessao')
            if data_concessao:
                adicional.data_concessao_adicional = data_concessao
                # Atualiza status para Publicado quando salvar os detalhes
                adicional.status_adicional = Cadastro_adicional.StatusAdicional.PUBLICADO

            # Atualizar BOL G Pm
            adicional.bol_g_pm_adicional = request.POST.get('bol_g_pm', '')

            # Atualizar data de publicação
            data_publicacao = request.POST.get('data_publicacao')
            if data_publicacao:
                adicional.data_publicacao_adicional = data_publicacao

            adicional.user_updated = request.user
            adicional.save()
            
            # Registrar no histórico
            HistoricoCadastro.objects.create(
                cadastro_adicional=adicional,
                situacao_adicional=adicional.situacao_adicional,
                usuario_alteracao=request.user,
                numero_prox_adicional=adicional.numero_prox_adicional,
                proximo_adicional=adicional.proximo_adicional,
                mes_proximo_adicional=adicional.mes_proximo_adicional,
                ano_proximo_adicional=adicional.ano_proximo_adicional,
                dias_desconto_adicional=adicional.dias_desconto_adicional
            )
            
            messages.success(request, "Detalhes atualizados!")
            return redirect('adicional:ver_adicional', id=adicional.id)  # Corrigido
            
        except ValueError as e:
            messages.error(request, f"Erro: {str(e)}")
            return redirect('adicional:ver_adicional', id=adicional.id)  # Corrigido
            
        except Exception as e:
            messages.error(request, f"Erro: {str(e)}")
            return redirect('adicional:ver_adicional', id=adicional.id)  # Corrigido

    return redirect('adicional:ver_adicional', id=adicional.id)  # Corrigido


@require_POST
@csrf_exempt  # Temporário para testes, remova em produção
def confirmar_6parte(request, pk):
    try:
        adicional = Cadastro_adicional.objects.get(pk=pk)
        adicional.confirmacao_6parte = True
        adicional.save()
        return JsonResponse({'success': True})
    except Cadastro_adicional.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Adicional não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)



@login_required
def confirmar_sipa(request, pk):
    adicional = get_object_or_404(Cadastro_adicional, pk=pk)
    
    if request.method == 'POST':
        try:
            # Verificar se o usuário está autenticado
            if not request.user.is_authenticated:
                messages.error(request, 'Usuário não autenticado')
                return redirect('adicional:ver_adicional', id=pk)
            
            # Verificar senha
            password = request.POST.get('password')
            if not password:
                messages.error(request, 'Senha não fornecida')
                return redirect('adicional:ver_adicional', id=pk)
            
            # Verificar credenciais
            user = authenticate(request, username=request.user.get_username(), password=password)
            if not user or user != request.user:
                messages.error(request, 'Senha incorreta')
                return redirect('adicional:ver_adicional', id=pk)
            
            # Atualizar campos
            adicional.status_adicional = Cadastro_adicional.StatusAdicional.LANCADO_SIPA
            adicional.numero_prox_adicional = int(request.POST.get('numero_prox_adicional', 1))
            
            proximo_adicional = request.POST.get('proximo_adicional')
            if proximo_adicional:
                adicional.proximo_adicional = datetime.strptime(proximo_adicional, '%Y-%m-%d').date()
            else:
                adicional.proximo_adicional = None
            
            # Verificar e atualizar 6ª parte se necessário
            if adicional.numero_prox_adicional == 4:
                adicional.sexta_parte = request.POST.get('sexta_parte') == 'on'
            else:
                adicional.sexta_parte = False
                
            adicional.user_updated = request.user
            adicional.save()
            
            # Registrar no histórico
            HistoricoCadastro.objects.create(
                cadastro_adicional=adicional,
                situacao_adicional=adicional.situacao_adicional,
                usuario_alteracao=request.user,
                numero_prox_adicional=adicional.numero_prox_adicional,
                proximo_adicional=adicional.proximo_adicional,
                mes_proximo_adicional=adicional.mes_proximo_adicional,
                ano_proximo_adicional=adicional.ano_proximo_adicional,
                dias_desconto_adicional=adicional.dias_desconto_adicional
            )
            
            messages.success(request, 'Lançamento no SIPA confirmado com sucesso!')
            return redirect('adicional:ver_adicional', id=pk)
            
        except ValueError as e:
            messages.error(request, f'Erro nos dados fornecidos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Erro inesperado: {str(e)}')
    
    # Redireciona para a página de visualização em caso de erro ou método GET
    return redirect('adicional:ver_adicional', id=pk)


@login_required
def carregar_dados_sipa(request, pk):
    adicional = get_object_or_404(Cadastro_adicional, pk=pk)

    data = {
        'numero_prox_adicional': adicional.numero_prox_adicional,
        'proximo_adicional': adicional.proximo_adicional.strftime('%Y-%m-%d') if adicional.proximo_adicional else '',
        'dias_desconto_adicional': adicional.dias_desconto_adicional,
        'sexta_parte': adicional.sexta_parte,
        'n_choices': [{'value': c[0], 'label': c[1]} for c in Cadastro_adicional.StatusAdicional.choices]
    }

    return JsonResponse(data)



from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from .models import Cadastro_adicional

@login_required
def concluir_processo_ats(request, pk):
    adicional = get_object_or_404(Cadastro_adicional, pk=pk)
    
    if request.method == 'POST':
        password = request.POST.get('password')
        response_data = {'success': False, 'message': ''}

        try:
            # Verifica senha e permissão
            if not request.user.check_password(password):
                raise ValueError("Senha incorreta")
                
            if not request.user.has_perm('adicional.can_concluir_adicional'):
                raise PermissionError("Permissão insuficiente")

            # Atualiza o adicional
            adicional.status_adicional = Cadastro_adicional.StatusAdicional.ENCERRADO
            adicional.situacao_adicional = "Concluído"
            adicional.data_conclusao = timezone.now()
            adicional.usuario_conclusao = request.user
            adicional.save()

            response_data['success'] = True
            return JsonResponse(response_data)

        except Exception as e:
            response_data['message'] = str(e)
            return JsonResponse(response_data, status=400)

    return redirect('adicional:detalhar_adicional', pk=pk)

# backend/adicional/views.py
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods
# Supondo que o modelo Cadastro está neste local

@require_http_methods(["GET", "POST"])
def novo_adicional(request):
    if request.method == 'POST':
        try:
            # Coletar dados básicos
            cadastro_id = request.POST.get('cadastro_id')
            n_bloco = request.POST.get('n_bloco_adicional')
            data_ultimo = request.POST.get('data_ultimo_adicional')
            
            # Validação básica
            if not all([cadastro_id, n_bloco, data_ultimo]):
                raise ValidationError('Todos os campos obrigatórios devem ser preenchidos')
            
            # Conversão de tipos
            cadastro = get_object_or_404(Cadastro, id=cadastro_id)
            n_bloco_int = int(n_bloco)
            data_ultimo_date = timezone.datetime.strptime(data_ultimo, '%Y-%m-%d').date()
            
            # Validação de negócio
            if n_bloco_int < 1 or n_bloco_int > 8:
                raise ValidationError('Número do bloco deve estar entre 1 e 8')
                
            # Criação do adicional
            adicional = Cadastro_adicional.objects.create(
                cadastro=cadastro,
                numero_adicional=n_bloco_int,
                data_ultimo_adicional=data_ultimo_date,
                user_created=request.user
            )
            
            # Mensagem de sucesso personalizada
            messages.success(
                request,
                f'Adicional {n_bloco_int}° registrado com sucesso para '
                f'{cadastro.nome_completo()}. '
                f'Próxima concessão prevista para {adicional.proximo_adicional.strftime("%d/%m/%Y")}'
            )
            
            return redirect('adicional:ver_adicional', id=adicional.id)
            
        except ValidationError as e:
            messages.error(request, f'Erro de validação: {e}')
            return render(request, 'adicional/novo_adicional.html', {
                'cadastro': cadastro,
                'form_data': request.POST
            })
            
        except Exception as e:
            messages.error(request, f'Erro inesperado: {str(e)}')
            return redirect('efetivo:detalhes_militar', militar_id=cadastro_id)

    # Método GET
    militar_id = request.GET.get('militar_id')
    if not militar_id:
        messages.warning(request, 'Nenhum militar selecionado')
        return redirect('efetivo:lista_militares')
    
    cadastro = get_object_or_404(Cadastro, id=militar_id)
    return render(request, 'adicional/novo_adicional.html', {
        'cadastro': cadastro,
        'default_data': {
            'n_bloco_adicional': 1,
            'data_ultimo_adicional': timezone.now().strftime('%Y-%m-%d')
        }
    })