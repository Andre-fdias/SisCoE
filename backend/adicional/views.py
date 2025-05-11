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
from django.contrib.messages import constants
from .models import Cadastro_adicional, HistoricoCadastro, LP, HistoricoLP
from backend.efetivo.models import Cadastro, DetalhesSituacao, Promocao, Imagem
from datetime import timedelta
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
            messages.add_message(request, constants.ERROR, 'Cadastro do militar não localizado.', extra_tags='bg-red-500 text-white p-4 rounded')
            return redirect('adicional:cadastrar_lp')

        cadastro = get_object_or_404(Cadastro, id=cadastro_id)

        if not data_ultimo_adicional_str:
            messages.add_message(request, constants.ERROR, 'Favor inserir a data de concessão do último Adicional', extra_tags='bg-red-500 text-white p-4 rounded')
            return redirect('adicional:cadastrar_lp')

        if not data_ultimo_lp_str:
            messages.add_message(request, constants.ERROR, 'Favor inserir a data de concessão da última LP', extra_tags='bg-red-500 text-white p-4 rounded')
            return redirect('adicional:cadastrar_lp')

        try:
            # Conversão de datas
            data_ultimo_adicional = datetime.strptime(data_ultimo_adicional_str, '%Y-%m-%d').date()
            data_ultimo_lp = datetime.strptime(data_ultimo_lp_str, '%Y-%m-%d').date()

            # Validação dos números de bloco
            if not n_bloco_adicional or not n_bloco_adicional.isdigit():
                messages.add_message(request, constants.ERROR, 'Número do Bloco Adicional inválido.', extra_tags='bg-red-500 text-white p-4 rounded')
                return redirect('adicional:cadastrar_lp')
            if not n_bloco_lp or not n_bloco_lp.isdigit():
                messages.add_message(request, constants.ERROR, 'Número do Bloco LP inválido.', extra_tags='bg-red-500 text-white p-4 rounded')
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
                    cadastro=cadastro,  # CAMPO OBRIGATÓRIO ADICIONADO
                    cadastro_adicional=adicional,
                    numero_adicional=adicional.numero_adicional,
                    data_ultimo_adicional=adicional.data_ultimo_adicional,
                    situacao_adicional=situacao_adicional,
                    usuario_alteracao=user,
                    numero_prox_adicional=numero_prox_adicional,
                    proximo_adicional=proximo_adicional,
                    mes_proximo_adicional=mes_proximo_adicional,
                    ano_proximo_adicional=ano_proximo_adicional,
                    dias_desconto_adicional=dias_desconto_adicional,
                    status_adicional=adicional.status_adicional  # ADICIONAR SE NECESSÁRIO
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

            messages.add_message(request, constants.SUCCESS, 'Adicional e LP cadastrados com sucesso!', extra_tags='bg-green-500 text-white p-4 rounded')
            return redirect('adicional:listar_lp')

        except ValueError as e:
            messages.add_message(request, constants.ERROR, f'Formato de data inválido. Use o formato AAAA-MM-DD. Erro: {str(e)}', extra_tags='bg-red-500 text-white p-4 rounded')
            return redirect('adicional:cadastrar_lp')
        except Exception as e:
            messages.add_message(request, constants.ERROR, f'Ocorreu um erro ao cadastrar: {str(e)}', extra_tags='bg-red-500 text-white p-4 rounded')
            return redirect('adicional:cadastrar_lp')


@login_required
def buscar_militar_adicional(request):
    """
    Busca um militar pelo RE (via POST) para pré-preencher o formulário de cadastro de Adicional/LP,
    ou exibe o formulário de busca (via GET).
    """
    # Template principal que contém tanto a busca quanto o formulário
    template_name = 'cadastrar_lp.html'

    if request.method == "POST":
        re = request.POST.get('re', '').strip()
        if not re:
            messages.warning(request, 'Por favor, informe o RE para buscar.', extra_tags='bg-yellow-500 text-white p-4 rounded')
            return render(request, template_name)

        try:
            # Busca o cadastro principal
            cadastro = Cadastro.objects.get(re=re)

            # Busca os dados relacionados
            detalhes = DetalhesSituacao.objects.filter(cadastro=cadastro).order_by('-id').first()
            imagem = Imagem.objects.filter(cadastro=cadastro).order_by('-id').first()
            promocao = Promocao.objects.filter(cadastro=cadastro).order_by('-id').first()

            # Verifica dados obrigatórios
            if not detalhes:
                messages.error(request, 'Detalhamento não encontrado', extra_tags='bg-red-500 text-white p-4 rounded')
                return render(request, template_name)
            if not promocao:
                messages.error(request, 'Dados de Posto e graduação não localizados', extra_tags='bg-red-500 text-white p-4 rounded')
                return render(request, template_name)

            # Prepara o contexto
            context = {
                'cadastro': cadastro,
                'detalhes': detalhes,
                'imagem': imagem,
                'promocao': promocao,
                'found_re': re  # Indica que a busca foi feita
            }
            return render(request, template_name, context)

        except Cadastro.DoesNotExist:
            messages.error(request, f'Militar com RE "{re}" não cadastrado no sistema', extra_tags='bg-red-500 text-white p-4 rounded')
            return render(request, template_name, {'searched_re': re})
        
        except Exception as e:
            messages.error(request, f'Ocorreu um erro ao buscar o militar: {str(e)}', extra_tags='bg-red-500 text-white p-4 rounded')
            return render(request, template_name)

    # Se for GET, mostra o formulário vazio
    return render(request, template_name)


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
        'historicos_encerrados': historicos,
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
            novo_adicional.proximo_adicional = novo_adicional.data_ultimo_adicional + timedelta(days=1825)  # 5 anos em dias
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
    ).exclude(id=id).order_by('numero_adicional') 

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
            
            # Verifica a senha diretamente (sem usar authenticate)
            if not request.user.check_password(password):
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
            adicional.dias_desconto_adicional = int(request.POST.get('dias_desconto', 0))
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

from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
import json
import logging

logger = logging.getLogger(__name__)

@require_http_methods(["POST"])
@login_required
def concluir_adicional(request, pk):
    logger.info(f"Iniciando conclusão para adicional {pk}")
    
    try:
        # Verifica o tipo de conteúdo
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body.decode('utf-8'))
                password = data.get('password')
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao decodificar JSON: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'message': 'Dados JSON inválidos'
                }, status=400)
        else:
            password = request.POST.get('password')
        
        # Validações
        if not password:
            return JsonResponse({
                'success': False,
                'message': 'Senha não fornecida'
            }, status=400)

        if not request.user.check_password(password):
            return JsonResponse({
                'success': False,
                'message': 'Senha incorreta'
            }, status=403)

        if not request.user.has_perm('adicional.can_concluir_adicional'):
            return JsonResponse({
                'success': False,
                'message': 'Permissão negada'
            }, status=403)

        adicional = get_object_or_404(Cadastro_adicional, pk=pk)
        
        with transaction.atomic():
            # Atualiza o adicional
            adicional.status_adicional = Cadastro_adicional.StatusAdicional.ENCERRADO
            adicional.situacao_adicional = "Concluído"
            adicional.data_conclusao = timezone.now()
            adicional.usuario_conclusao = request.user
            adicional.save()

            # Cria histórico com TODOS os campos obrigatórios
            HistoricoCadastro.objects.create(
                cadastro_adicional=adicional,
                cadastro=adicional.cadastro,
                user_created=adicional.user_created,
                user_updated=request.user,
                usuario_alteracao=request.user,
                numero_adicional=adicional.numero_adicional,
                numero_prox_adicional=adicional.numero_prox_adicional,
                data_ultimo_adicional=adicional.data_ultimo_adicional,
                situacao_adicional="Concluído",
                status_adicional=Cadastro_adicional.StatusAdicional.ENCERRADO,
                data_conclusao=timezone.now(),
                # Outros campos conforme necessário
                proximo_adicional=adicional.proximo_adicional,
                mes_proximo_adicional=adicional.mes_proximo_adicional,
                ano_proximo_adicional=adicional.ano_proximo_adicional,
                dias_desconto_adicional=adicional.dias_desconto_adicional
            )

            return JsonResponse({
                'success': True,
                'message': 'Processo concluído com sucesso',
               
            })
        

    except Exception as e:
        logger.error(f"Erro ao concluir adicional: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': 'Erro interno do servidor',
            'error': str(e)
        }, status=500)

from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.http import JsonResponse
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Cadastro_adicional
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def novo_adicional(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Validação dos campos obrigatórios
                required_fields = ['cadastro_id', 'n_bloco_adicional', 'data_ultimo_adicional']
                for field in required_fields:
                    if not request.POST.get(field):
                        raise ValidationError(f"Campo obrigatório faltando: {field}")

                # Coleta de dados
                cadastro_id = int(request.POST['cadastro_id'])
                bloco_atual = int(request.POST['n_bloco_adicional'])
                data_ultimo = request.POST['data_ultimo_adicional']
                situacao = request.POST.get('situacao_adicional', 'Aguardando')

                # Validações
                if not (1 <= bloco_atual <= 8):
                    raise ValidationError("Número do bloco deve estar entre 1 e 8")

                data_ultima = timezone.datetime.strptime(data_ultimo, '%Y-%m-%d').date()
                if data_ultima > timezone.now().date():
                    raise ValidationError("Data do último adicional não pode ser futura")

                # Criação do objeto
                novo_adicional = Cadastro_adicional(
                    cadastro_id=cadastro_id,
                    numero_adicional=bloco_atual,
                    numero_prox_adicional=bloco_atual + 1,
                    data_ultimo_adicional=data_ultima,
                    situacao_adicional=situacao,
                    sexta_parte=request.POST.get('sexta_parte', 'False') == 'True',
                    user_created=request.user
                )

                novo_adicional.full_clean()
                novo_adicional.save()

                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('adicional:listar_lp'),
                    'message': 'Adicional criado com sucesso!'
                })

        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'message': '; '.join(e.messages)
            }, status=400)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro interno: {str(e)}'
            }, status=500)

    return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
# You would then need a URL pattern named 'ver_adicional' or 'detalhes_cadastro'
# in your backend/adicional/urls.py (or wherever your URLs are defined).

import logging
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required

# Configura o logger
logger = logging.getLogger(__name__)

@login_required
def editar_cadastro_adicional(request, id):
    """
    View robusta para edição de Cadastro_adicional com:
    - Tratamento completo de erros
    - Logging adequado
    - Validação de campos
    - Suporte a histórico (opcional)
    """
    adicional = get_object_or_404(Cadastro_adicional, id=id)
    
    # Obter choices para os selects
    try:
        n_choices = Cadastro_adicional._meta.get_field('numero_adicional').choices
        situacao_choices = Cadastro_adicional._meta.get_field('situacao_adicional').choices
        status_choices = Cadastro_adicional._meta.get_field('status_adicional').choices
    except Exception as e:
        logger.error(f"Erro ao obter choices: {str(e)}")
        messages.error(request, "Erro ao carregar opções do formulário")
        return redirect('adicional:ver_adicional', id=id)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 1. Processar campos básicos
                fields_to_update = [
                    'numero_adicional', 'numero_prox_adicional',
                    'situacao_adicional', 'status_adicional',
                    'dias_desconto_adicional', 'bol_g_pm_adicional'
                ]
                
                for field in fields_to_update:
                    if field in request.POST:
                        setattr(adicional, field, request.POST.get(field))

                # 2. Processar campos numéricos especiais
                numeric_fields = {
                    'mes_proximo_adicional': int,
                    'ano_proximo_adicional': int
                }
                
                for field, type_func in numeric_fields.items():
                    if request.POST.get(field):
                        setattr(adicional, field, type_func(request.POST.get(field)))

                # 3. Processar datas
                date_fields = [
                    'data_ultimo_adicional',
                    'proximo_adicional',
                    'data_concessao_adicional',
                    'data_publicacao_adicional'
                ]
                
                for field in date_fields:
                    if request.POST.get(field):
                        setattr(adicional, field, datetime.strptime(request.POST.get(field), '%Y-%m-%d').date())

                # 4. Processar booleanos
                adicional.sexta_parte = 'sexta_parte' in request.POST
                adicional.confirmacao_6parte = 'confirmacao_6parte' in request.POST

                # 5. Atualizar metadados
                adicional.user_updated = request.user
                adicional.updated_at = timezone.now()

                # 6. Validar e salvar
                adicional.full_clean()
                adicional.save()

                # 7. Tentar criar histórico (se existir)
                try:
                    if hasattr(adicional, 'historicos'):
                        HistoricoCadastro.objects.create(
                            cadastro_adicional=adicional,
                            usuario=request.user,
                            acao="EDIÇÃO",
                            detalhes=f"Editado por {request.user.username}"
                        )
                except Exception as hist_error:
                    logger.warning(f"Erro ao criar histórico (pode ser normal): {str(hist_error)}")

                messages.success(request, 'Cadastro atualizado com sucesso!')
                return redirect('adicional:ver_adicional', id=adicional.id)

        except ValueError as e:
            logger.error(f"Erro de valor ao editar adicional {id}: {str(e)}")
            messages.error(request, f'Erro nos valores informados: {str(e)}')
        except ValidationError as e:
            logger.error(f"Erro de validação ao editar adicional {id}: {str(e)}")
            messages.error(request, f'Erro de validação: {", ".join(e.messages)}')
        except Exception as e:
            logger.critical(f"Erro inesperado ao editar adicional {id}: {str(e)}", exc_info=True)
            messages.error(request, 'Ocorreu um erro inesperado. Administrador foi notificado.')

    context = {
        'adicional': adicional,
        'n_choices': n_choices,
        'situacao_choices': situacao_choices,
        'status_choices': status_choices,
    }
    
    return render(request, 'editar_geral.html', context)