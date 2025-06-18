# backend/lp/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import authenticate 
from django.core.exceptions import ValidationError
from django.http import JsonResponse, HttpResponseBadRequest 
from django.views.decorators.http import require_POST, require_http_methods
from django.db import transaction 
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from django.contrib.messages import constants
from .models import LP, HistoricoLP, N_CHOICES, situacao_choices 
from backend.efetivo.models import Cadastro, Promocao, DetalhesSituacao, Imagem # Importe os modelos necessários
from django.template.loader import render_to_string
import logging
import json # Importar json para serializar as escolhas de status

logger = logging.getLogger(__name__)

def alert_response(type, title, message, status=200, reload_page=False, redirect_url=None, errors=None):
    """
    Helper function to return a JSON response with alert data for AJAX requests.
    The 'modal_alerts.html' JavaScript listens for this structure.
    """
    response_data = {
        'alert': {
            'type': type,
            'title': title,
            'message': message
        }
    }
    if reload_page:
        response_data['reload_page'] = True
    if redirect_url:
        response_data['redirect_url'] = redirect_url
    if errors:
        response_data['errors'] = errors
    return JsonResponse(response_data, status=status)

def create_historico_lp(lp_instance, user, observacoes_historico=""):
    HistoricoLP.objects.create(
        lp=lp_instance,
        usuario_alteracao=user,
        situacao_lp=lp_instance.situacao_lp,
        status_lp=lp_instance.status_lp,
        numero_lp=lp_instance.numero_lp,
        data_ultimo_lp=lp_instance.data_ultimo_lp,
        
        numero_prox_lp=lp_instance.numero_prox_lp,
        proximo_lp=lp_instance.proximo_lp,
        mes_proximo_lp=lp_instance.mes_proximo_lp,
        ano_proximo_lp=lp_instance.ano_proximo_lp,
        dias_desconto_lp=lp_instance.dias_desconto_lp,
        bol_g_pm_lp=lp_instance.bol_g_pm_lp,
        data_publicacao_lp=lp_instance.data_publicacao_lp,
        data_concessao_lp=lp_instance.data_concessao_lp,
        lancamento_sipa=lp_instance.lancamento_sipa, 
        observacoes_historico=observacoes_historico
    )

def calcular_dias_efeito_interruptivo_ou_suspensivo(cadastro, start_date, end_date):
    """
    Calcula os dias de afastamento que afetam a contagem da LP entre duas datas.
    Isso é um PLACEHOLDER. Você precisa preencher com a lógica real
    consultando os modelos de LTS, Agregações, Punições Disciplinares, etc.
    """
    total_dias_interrupcao = 0
    total_dias_suspensao = 0
    
    # ... (Sua lógica de interrupção/suspensão aqui) ...

    return total_dias_interrupcao, total_dias_suspensao 


def calcular_proxima_lp_data(cadastro_id):
    """
    Calcula a data prevista para o próximo bloco de LP,
    considerando o histórico de LPs e interrupções/suspensões.
    """
    cadastro = get_object_or_404(Cadastro, id=cadastro_id)
    ultima_lp = LP.objects.filter(cadastro=cadastro).order_by('-numero_lp').first()

    if ultima_lp:
        data_inicio_aquisitivo_atual = ultima_lp.data_ultimo_lp + timedelta(days=1)
        proximo_numero_lp = ultima_lp.numero_lp + 1
    else:
        if not cadastro.data_ingresso:
            raise ValidationError("Data de ingresso do militar não definida no cadastro.")
        data_inicio_aquisitivo_atual = cadastro.data_ingresso
        proximo_numero_lp = 1

    data_fechamento_bloco_base = data_inicio_aquisitivo_atual + relativedelta(years=5) - timedelta(days=1)
    
    data_ultimo_lp_calculado = data_fechamento_bloco_base 

    proximo_lp_data_previsao = data_ultimo_lp_calculado + timedelta(days=1)
    
    return {
        'proximo_lp_numero': proximo_numero_lp,
        'data_ultimo_lp_calculado': data_ultimo_lp_calculado, 
        'proximo_lp_data_previsao': proximo_lp_data_previsao,
        'mes_proximo_lp': proximo_lp_data_previsao.month,
        'ano_proximo_lp': proximo_lp_data_previsao.year,
        'data_inicio_periodo_aquisitivo': data_inicio_aquisitivo_atual
    }

@login_required
@require_http_methods(["GET", "POST"])
def cadastrar_lp(request):
    """
    View para cadastrar Licença Prêmio para um militar.
    """
    template_name = 'lp/cadastrar_lp.html'
    
    if request.method == 'GET':
        # Renderiza o formulário inicial de busca
        return render(request, template_name, {'n_choices': N_CHOICES})

    elif request.method == 'POST':
        # Obtenção dos dados do formulário
        cadastro_id = request.POST.get('cadastro_id')
        numero_lp = request.POST.get('numero_lp')
        data_ultimo_lp_str = request.POST.get('data_ultimo_lp')
      
        dias_desconto_lp = int(request.POST.get('dias_desconto_lp', 0) or 0)
        user = request.user

        # Determinar se é uma requisição AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        # Validações básicas
        if not cadastro_id:
            error_msg = 'Cadastro do militar não localizado.'
            if is_ajax:
                return alert_response(type='error', title='Erro!', message=error_msg, status=400)
            messages.error(request, error_msg)
            return redirect('lp:cadastrar_lp')

        cadastro = get_object_or_404(Cadastro, id=cadastro_id)

        if not data_ultimo_lp_str:
            error_msg = 'A data de fechamento do bloco aquisitivo é obrigatória.'
            if is_ajax:
                return alert_response(type='error', title='Erro!', message=error_msg, status=400)
            messages.error(request, error_msg)
            return redirect('lp:cadastrar_lp')
            


        try:
            # Conversão de datas
            data_ultimo_lp = datetime.strptime(data_ultimo_lp_str, '%Y-%m-%d').date()
         

            # Validação do número da LP
            if not numero_lp or not numero_lp.isdigit():
                error_msg = 'Número da Licença Prêmio inválido.'
                if is_ajax:
                    return alert_response(type='error', title='Erro!', message=error_msg, status=400)
                messages.error(request, error_msg)
                return redirect('lp:cadastrar_lp')

            numero_lp_int = int(numero_lp)
            
            # Verificar se LP já existe para este militar
            if LP.objects.filter(cadastro=cadastro, numero_lp=numero_lp_int).exists():
                error_msg = f'Já existe uma LP de número {numero_lp_int} cadastrada para este militar.'
                if is_ajax:
                    return alert_response(type='error', title='Erro!', message=error_msg, status=400)
                messages.error(request, error_msg)
                return redirect('lp:cadastrar_lp')

            # Calcular dados da próxima LP
            data_base_proximo_periodo = data_ultimo_lp + timedelta(days=1)
            proximo_lp = data_base_proximo_periodo + relativedelta(years=5) - timedelta(days=1)
            mes_proximo_lp = proximo_lp.month
            ano_proximo_lp = proximo_lp.year
            numero_prox_lp = numero_lp_int + 1

            with transaction.atomic():
                # Criação da LP
                lp = LP.objects.create(
                    cadastro=cadastro,
                    user_created=user,
                    user_updated=user,
                    numero_lp=numero_lp_int,
                    data_ultimo_lp=data_ultimo_lp,
                    
                    numero_prox_lp=numero_prox_lp,
                    proximo_lp=proximo_lp,
                    mes_proximo_lp=mes_proximo_lp,
                    ano_proximo_lp=ano_proximo_lp,
                    dias_desconto_lp=dias_desconto_lp,
                    situacao_lp="Aguardando",
                    status_lp=LP.StatusLP.AGUARDANDO_REQUISITOS
                )

                # Registrar no histórico da LP
                create_historico_lp(lp, user, "LP cadastrada inicialmente.")

            success_msg = f'LP {lp.numero_lp} cadastrada com sucesso para {cadastro.nome_de_guerra}!'
            if is_ajax:
                redirect_url = reverse('lp:ver_lp', kwargs={'pk': lp.id})
                return alert_response(
                    type='success',
                    title='Sucesso!',
                    message=success_msg,
                    redirect_url=redirect_url
                )
            messages.success(request, success_msg)
            return redirect('lp:ver_lp', pk=lp.id)

        except ValueError as e:
            error_msg = f'Formato de data inválido. Use o formato AAAA-MM-DD. Erro: {str(e)}'
            if is_ajax:
                return alert_response(type='error', title='Erro!', message=error_msg, status=400)
            messages.error(request, error_msg)
            return redirect('lp:cadastrar_lp')
            
        except ValidationError as e:
            error_msg = f'Erro de validação: {", ".join(e.messages)}'
            if is_ajax:
                errors = {}
                if hasattr(e, 'error_dict'):
                    for field, err_list in e.error_dict.items():
                        errors[field] = ' '.join([str(err) for err in err_list])
                return alert_response(
                    type='error',
                    title='Erro de Validação!',
                    message=error_msg,
                    errors=errors,
                    status=400
                )
            messages.error(request, error_msg)
            return redirect('lp:cadastrar_lp')
            
        except Exception as e:
            error_msg = f'Ocorreu um erro inesperado ao cadastrar: {str(e)}'
            logger.exception(f"Erro em cadastrar_lp: {str(e)}")
            if is_ajax:
                return alert_response(type='error', title='Erro!', message=error_msg, status=500)
            messages.error(request, error_msg)
            return redirect('lp:cadastrar_lp')


@login_required
@require_POST
def buscar_militar_lp(request):
    """
    Busca um militar pelo RE e retorna os dados em JSON.
    Esta função só deve ser chamada via requisição POST do formulário de busca.
    """
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    re_militar = request.POST.get('re', '').strip()
    
    if not re_militar:
        return JsonResponse({
            'success': False,
            'alert': {'type': 'error', 'title': 'Erro!', 'message': 'O RE do militar é obrigatório.'}
        }, status=400)

    try:
        cadastro = Cadastro.objects.get(re=re_militar)
        promocao = Promocao.objects.filter(cadastro=cadastro).order_by('-ultima_promocao').first() 
        detalhes = DetalhesSituacao.objects.filter(cadastro=cadastro).first()
        imagem = Imagem.objects.filter(cadastro=cadastro).first()

        # Verificar dados obrigatórios
        if not detalhes:
            return JsonResponse({
                'success': False,
                'alert': {'type': 'error', 'title': 'Erro!', 'message': 'Detalhamento da situação não encontrado para este militar.'}
            }, status=400)
        
        if not promocao:
            return JsonResponse({
                'success': False,
                'alert': {'type': 'error', 'title': 'Erro!', 'message': 'Dados de Posto/Graduação não encontrados para este militar.'}
            }, status=400)

        # Preparar dados para retorno JSON
        militar_data = {
            'id': cadastro.id,
            're': cadastro.re,
            'nome': cadastro.nome,
            'posto_grad': promocao.posto_grad,
            'sgb': detalhes.sgb,
            'posto_secao': detalhes.posto_secao,
            'image_url': imagem.image.url if imagem and imagem.image else '',
            'alert': {
                'type': 'success',
                'title': 'Militar Encontrado!',
                'message': f'Dados do militar {cadastro.nome_de_guerra} carregados.'
            }
        }
        
        # Você pode calcular os dados iniciais da LP aqui se preferir no backend,
        # ou deixar o JS do frontend calcular (o que é o caso atual com calcularCampos)
        # initial_lp_data = calcular_proxima_lp_data(cadastro.id) # Se esta função existir
        # militar_data['initial_lp_data'] = initial_lp_data 

        return JsonResponse({'success': True, 'militar_data': militar_data})

    except Cadastro.DoesNotExist:
        return JsonResponse({
            'success': False,
            'alert': {'type': 'error', 'title': 'Erro!', 'message': f'Militar com RE "{re_militar}" não cadastrado no sistema.'}
        }, status=404)
    
    except Exception as e:
        logger.exception(f'Erro em buscar_militar_lp para RE {re_militar}: {str(e)}')
        return JsonResponse({
            'success': False,
            'alert': {'type': 'error', 'title': 'Erro Interno!', 'message': f'Ocorreu um erro inesperado ao buscar o militar: {str(e)}'}
        }, status=500)



@login_required
def ver_lp(request, pk):
    lp = get_object_or_404(LP, pk=pk)
    
    # Histórico da LP específica (alterações nesta LP)
    historico_lp = HistoricoLP.objects.filter(lp=lp).order_by('-data_alteracao')
    
    # Histórico de cadastros de LP para o mesmo militar (apenas LPs concluídas)
    lps_do_cadastro = LP.objects.filter(cadastro=lp.cadastro)
    historico_cadastro = HistoricoLP.objects.filter(
        lp__in=lps_do_cadastro,
        status_lp='concluido'  # Filtro para status concluído
    ).order_by('-data_alteracao')
    
    status_lp_choices_json = json.dumps(list(LP.StatusLP.choices))

    # 1. VERIFICAÇÃO AUTOMÁTICA DE STATUS
    hoje = timezone.localdate()
    
    if lp.status_lp == LP.StatusLP.AGUARDANDO_REQUISITOS:
        data_fim_periodo_lp_calculated = None
        if lp.data_ultimo_lp:
            data_inicio_periodo_lp_calculated = lp.data_ultimo_lp + timedelta(days=1)
            data_fim_periodo_lp_calculated = data_inicio_periodo_lp_calculated + relativedelta(years=5) - timedelta(days=1)

        if data_fim_periodo_lp_calculated and data_fim_periodo_lp_calculated <= hoje:
            lp.status_lp = LP.StatusLP.APTA_CONCESSAO
            lp.save()
    
    # 2. CÁLCULO DO PERÍODO AQUISITIVO
    progresso_periodo_aquisitivo_percentual = 0
    dias_restantes_periodo_lp = 0
    dias_decorridos_periodo_lp = 0
    total_dias_periodo_lp = 0
    data_inicio_periodo_lp = None
    data_fim_periodo_lp = None

    if lp.data_ultimo_lp:
        data_inicio_periodo_lp = lp.data_ultimo_lp + timedelta(days=1)
        data_fim_periodo_lp = data_inicio_periodo_lp + relativedelta(years=5) - timedelta(days=1)
        
        if hoje > data_fim_periodo_lp:
            dias_decorridos_periodo_lp = (data_fim_periodo_lp - data_inicio_periodo_lp).days
            dias_restantes_periodo_lp = 0
            progresso_periodo_aquisitivo_percentual = 100
        
        elif hoje >= data_inicio_periodo_lp:
            dias_decorridos_periodo_lp = (hoje - data_inicio_periodo_lp).days
            dias_restantes_periodo_lp = (data_fim_periodo_lp - hoje).days
            total_dias_periodo_lp = (data_fim_periodo_lp - data_inicio_periodo_lp).days
            
            if total_dias_periodo_lp > 0:
                progresso_periodo_aquisitivo_percentual = (dias_decorridos_periodo_lp / total_dias_periodo_lp) * 100

    lp_count = LP.objects.filter(cadastro=lp.cadastro).count()

    context = {
        'lp': lp,
        'historico_lp': historico_lp,
        'historico_cadastro': historico_cadastro,
        'N_CHOICES': N_CHOICES,
        'current_year': timezone.now().year,
        'progresso_periodo_aquisitivo_percentual': round(progresso_periodo_aquisitivo_percentual, 2),
        'dias_decorridos_periodo_lp': dias_decorridos_periodo_lp,
        'dias_restantes_periodo_lp': dias_restantes_periodo_lp,
        'total_dias_periodo_lp': total_dias_periodo_lp,
        'data_inicio_periodo_lp': data_inicio_periodo_lp,
        'data_fim_periodo_lp': data_fim_periodo_lp,
        'StatusLP_choices': LP.StatusLP.choices,
        'StatusLP_choices_json': status_lp_choices_json,
        'lp_count': lp_count,
    }
    return render(request, 'lp/detalhar_lp.html', context)


@login_required
@require_POST
def editar_concessao_lp(request, pk):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    lp = get_object_or_404(LP, pk=pk)

    try:
        data = request.POST
        data_concessao_lp_str = data.get('data_concessao_lp')
        bol_g_pm_lp = data.get('bol_g_pm_lp')
        data_publicacao_lp_str = data.get('data_publicacao_lp')

        # Conversão de datas
        data_concessao_lp = date.fromisoformat(data_concessao_lp_str) if data_concessao_lp_str else None
        data_publicacao_lp = date.fromisoformat(data_publicacao_lp_str) if data_publicacao_lp_str else None

        # Validações básicas aprimoradas
        errors = {}
        if not data_concessao_lp:
            errors['data_concessao_lp'] = 'A data de concessão é obrigatória.'
        # O campo 'BOL GPm LP' não é 'required' no HTML, então a validação aqui deve ser opcional ou removida
        # Se for obrigatório, adicione 'required' no input HTML e mantenha a validação aqui.
        # if not bol_g_pm_lp:
        #     errors['bol_g_pm_lp'] = 'O BOL GPm é obrigatório.'
        # A data de publicação também não é 'required' no HTML, então a validação deve ser opcional
        # Se for obrigatória, adicione 'required' no input HTML e mantenha a validação aqui.
        # if not data_publicacao_lp:
        #     errors['data_publicacao_lp'] = 'A data de publicação é obrigatória.'
        
        if errors:
            if is_ajax:
                # Retorna os erros de validação específicos para cada campo, se existirem
                return alert_response('error', 'Erro de Validação!', 'Por favor, preencha os campos obrigatórios.', 400, errors=errors)
            messages.error(request, 'Por favor, preencha todos os campos obrigatórios.')
            return redirect('lp:ver_lp', pk=pk)

        with transaction.atomic():
            lp.data_concessao_lp = data_concessao_lp
            lp.bol_g_pm_lp = bol_g_pm_lp
            lp.data_publicacao_lp = data_publicacao_lp
            lp.user_updated = request.user
            lp.data_atualizacao = timezone.now()

            # Lógica de status: se já tem data de concessão e publicação, status vira 'publicado'
            if lp.data_concessao_lp and lp.data_publicacao_lp:
                lp.status_lp = LP.StatusLP.PUBLICADO
            
            lp.full_clean() # Validação do modelo
            lp.save()

            # Registrar histórico
            HistoricoLP.objects.create(
                lp=lp,
                situacao_lp=lp.situacao_lp,
                status_lp=lp.status_lp,
                usuario_alteracao=request.user,
                numero_lp=lp.numero_lp,
                data_ultimo_lp=lp.data_ultimo_lp,
                numero_prox_lp=lp.numero_prox_lp,
                proximo_lp=lp.proximo_lp,
                mes_proximo_lp=lp.mes_proximo_lp,
                ano_proximo_lp=lp.ano_proximo_lp,
                dias_desconto_lp=lp.dias_desconto_lp,
                # Correção: usar request.user.email ou request.user.get_full_name()
                observacoes_historico=f"Dados de concessão/publicação atualizados por {request.user.get_full_name() or request.user.email}" 
            )

        if is_ajax:
            return alert_response('success', 'Sucesso!', 'Concessão da LP atualizada com sucesso!', reload_page=True)
        messages.success(request, 'Concessão da LP atualizada com sucesso!')
        return redirect('lp:ver_lp', pk=pk)

    except ValidationError as e:
        if is_ajax:
            # Envia os detalhes dos erros para o frontend para exibição específica
            return alert_response('error', 'Erro de Validação', 'Por favor, corrija os erros no formulário.', 400, errors=e.message_dict)
        messages.error(request, f'Erro de validação: {", ".join(e.messages)}')
    except Exception as e:
        logger.exception(f"Erro ao editar concessão da LP {pk}: {e}")
        if is_ajax:
            return alert_response('error', 'Erro Interno', 'Ocorreu um erro inesperado ao editar a concessão da LP.', 500)
        messages.error(request, 'Ocorreu um erro inesperado ao editar a concessão da LP. O administrador foi notificado.')
    
    return redirect('lp:ver_lp', pk=pk)


@login_required
@require_POST
def editar_dias_desconto_lp(request, pk):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    lp = get_object_or_404(LP, pk=pk)

    try:
        dias_desconto_lp = int(request.POST.get('dias_desconto_lp', 0))
        
        if dias_desconto_lp < 0:
            if is_ajax:
                return alert_response('error', 'Erro de Validação!', 'Os dias de desconto não podem ser negativos.', 400)
            messages.error(request, 'Os dias de desconto não podem ser negativos.')
            return redirect('lp:ver_lp', pk=pk)

        with transaction.atomic():
            lp.dias_desconto_lp = dias_desconto_lp
            # Recalcular proximo_lp e mes_proximo_lp/ano_proximo_lp se houver data_ultimo_lp
            if lp.data_ultimo_lp:
                # O 'proximo_lp' é a data de fechamento do bloco + 1 dia + os dias de desconto
                proximo_lp_calculado = lp.data_ultimo_lp + timedelta(days=1) + timedelta(days=lp.dias_desconto_lp)
                lp.proximo_lp = proximo_lp_calculado
                lp.mes_proximo_lp = proximo_lp_calculado.month
                lp.ano_proximo_lp = proximo_lp_calculado.year
            
            lp.user_updated = request.user
            lp.data_atualizacao = timezone.now()
            lp.full_clean()
            lp.save()

            # Registrar histórico
            HistoricoLP.objects.create(
                lp=lp,
                situacao_lp=lp.situacao_lp,
                status_lp=lp.status_lp,
                usuario_alteracao=request.user,
                numero_lp=lp.numero_lp,
                data_ultimo_lp=lp.data_ultimo_lp,
                numero_prox_lp=lp.numero_prox_lp,
                proximo_lp=lp.proximo_lp,
                mes_proximo_lp=lp.mes_proximo_lp,
                ano_proximo_lp=lp.ano_proximo_lp,
                dias_desconto_lp=lp.dias_desconto_lp,
                observacoes_historico=f"Dias de desconto alterados para {dias_desconto_lp} por {request.user.username}"
            )

        if is_ajax:
            return alert_response('success', 'Sucesso!', 'Dias de desconto da LP atualizados com sucesso!', reload_page=True)
        messages.success(request, 'Dias de desconto da LP atualizados com sucesso!')
        return redirect('lp:ver_lp', pk=pk)

    except ValueError as e:
        error_msg = f'Erro nos dados numéricos: {str(e)}'
        if is_ajax:
            return alert_response('error', 'Erro!', error_msg, 400)
        messages.error(request, error_msg)
    except ValidationError as e:
        error_msg = f'Erro de validação: {str(e)}'
        if is_ajax:
            return alert_response('error', 'Erro!', error_msg, 400)
        messages.error(request, error_msg)
    except Exception as e:
        error_msg = f'Erro inesperado: {str(e)}'
        if is_ajax:
            return alert_response('error', 'Erro!', error_msg, 500)
        messages.error(request, error_msg)
    
    return redirect('lp:ver_lp', pk=pk)


@login_required
@require_POST
def excluir_lp(request, pk):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    lp = get_object_or_404(LP, pk=pk)

    try:
        password = request.POST.get('password')

        if not password:
            if is_ajax:
                return alert_response('error', 'Erro de Validação!', 'A senha é obrigatória para excluir.', 400, errors={'password': 'A senha é obrigatória.'})
            messages.error(request, 'A senha é obrigatória para excluir.')
            return redirect('lp:ver_lp', pk=lp.pk)

        user = authenticate(request, username=request.user.username, password=password)

        if user is None or user != request.user:
            if is_ajax:
                return alert_response('error', 'Erro de Autenticação!', 'Senha incorreta.', 403, errors={'password': 'Senha incorreta.'})
            messages.error(request, 'Senha incorreta.')
            return redirect('lp:ver_lp', pk=lp.pk)
        
        with transaction.atomic():
            lp_cadastro_id = lp.cadastro.id # Captura o ID do cadastro antes de excluir
            lp.delete()

            HistoricoLP.objects.create(
                lp=None, # Define lp como None ou usa um campo que permita null para exclusão
                observacoes_historico=f"LP (ID {pk}) excluída por {request.user.username}. Militar ID: {lp_cadastro_id}"
            )

        if is_ajax:
            return alert_response('success', 'Sucesso!', 'LP excluída com sucesso!', redirect_url=reverse('lp:listar_lp'))
        messages.success(request, 'LP excluída com sucesso!')
        return redirect('lp:listar_lp')

    except Exception as e:
        logger.exception(f"Erro ao excluir LP {pk}: {e}")
        if is_ajax:
            return alert_response('error', 'Erro Interno', 'Ocorreu um erro inesperado ao excluir a LP.', 500)
        messages.error(request, 'Ocorreu um erro inesperado ao excluir a LP. O administrador foi notificado.')
    
    return redirect('lp:ver_lp', pk=pk)



@login_required
def listar_lp(request): 
    lps = LP.objects.all().order_by('cadastro__nome_de_guerra', 'numero_lp')
    context = {
        'lps': lps,
        'N_CHOICES': N_CHOICES 
    }
    return render(request, 'lp/listar_lp.html', context)






@login_required
@require_POST
def concluir_lp(request, pk):
    lp = get_object_or_404(LP, pk=pk)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    try:
        password = request.POST.get('password')
        # CORREÇÃO: Usar request.user.email em vez de request.user.username
        user = authenticate(request, username=request.user.email, password=password)

        if not user:
            return alert_response('error', 'Erro de Autenticação!', 'Senha incorreta. Por favor, tente novamente.', status=403)

        with transaction.atomic():
            lp.status_lp = LP.StatusLP.CONCLUIDO
            lp.data_conclusao = timezone.now()
            lp.usuario_conclusao = request.user
            lp.user_updated = request.user
            lp.data_atualizacao = timezone.now()

            lp.full_clean()
            lp.save()

            # Registrar histórico
            HistoricoLP.objects.create(
                lp=lp,
                situacao_lp=lp.situacao_lp,
                status_lp=lp.status_lp,
                usuario_alteracao=request.user,
                numero_lp=lp.numero_lp,
                data_ultimo_lp=lp.data_ultimo_lp,
                numero_prox_lp=lp.numero_prox_lp,
                proximo_lp=lp.proximo_lp,
                mes_proximo_lp=lp.mes_proximo_lp,
                ano_proximo_lp=lp.ano_proximo_lp,
                dias_desconto_lp=lp.dias_desconto_lp,
                bol_g_pm_lp=lp.bol_g_pm_lp,
                data_publicacao_lp=lp.data_publicacao_lp,
                data_concessao_lp=lp.data_concessao_lp,
                lancamento_sipa=lp.lancamento_sipa,
                observacoes_historico=f"LP concluída por {request.user.email}" # Usar email
            )

        return alert_response('success', 'Sucesso!', 'LP concluída com sucesso!', reload_page=True)

    except ValidationError as e:
        error_msg = f'Erro de validação: {e.message_dict}'
        logger.error(f"ValidationError em concluir_lp para LP ID {pk}: {e.message_dict}", exc_info=True)
        return alert_response('error', 'Erro de Validação!', error_msg, 400, errors=e.message_dict)
    except Exception as e:
        error_msg = f'Ocorreu um erro inesperado: {str(e)}. O administrador foi notificado.'
        logger.exception(f"Erro inesperado em concluir_lp para LP ID {pk}: {e}")
        return alert_response('error', 'Erro Interno!', error_msg, 500)

    return redirect('lp:ver_lp', pk=pk)


@login_required
def nova_lp(request):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if not is_ajax:
        return alert_response('error', 'Erro!', 'Requisição inválida', 400)

    try:
        data = request.POST
        cadastro_id = data.get('cadastro_id')
        numero_lp = data.get('numero_lp')
        data_ultimo_lp_str = data.get('data_ultimo_lp')
        
        if not all([cadastro_id, numero_lp, data_ultimo_lp_str]):
            return alert_response('error', 'Erro!', 'Dados obrigatórios faltando', 400)
        
        cadastro = get_object_or_404(Cadastro, id=cadastro_id)
        
        numero_lp = int(numero_lp)
        data_ultimo_lp = date.fromisoformat(data_ultimo_lp_str)
        
        # Calcular próximo LP (5 anos depois)
        proximo_lp = data_ultimo_lp + timedelta(days=5*365)
        
        nova_lp = LP(
            cadastro=cadastro,
            numero_lp=numero_lp,
            data_ultimo_lp=data_ultimo_lp,
            situacao_lp="Aguardando",
            numero_prox_lp=numero_lp + 1,
            proximo_lp=proximo_lp,
            mes_proximo_lp=proximo_lp.month,
            ano_proximo_lp=proximo_lp.year,
            user_created=request.user,
            status_lp=LP.StatusLP.AGUARDANDO_REQUISITOS
        )
        
        nova_lp.full_clean()
        nova_lp.save()

        return alert_response('success', 'Sucesso!', 'Nova LP criada com sucesso!')
        
    except ValidationError as e:
        return alert_response('error', 'Erro de Validação', ', '.join(e.messages), 400)
    except Exception as e:
        logger.error(f"Erro ao criar LP: {str(e)}", exc_info=True)
        return alert_response('error', 'Erro Interno', f'Erro ao criar LP: {str(e)}', 500)
# backend/lp/views.py

@login_required
@require_POST
def editar_lp(request, pk):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    lp = get_object_or_404(LP, pk=pk)

    if not is_ajax:
        messages.error(request, 'Requisição inválida. Por favor, use o formulário de edição.')
        return redirect('lp:ver_lp', pk=pk)

    try:
        data = request.POST
        
        # Função auxiliar para conversão segura de valores
        def to_int(value, default=None):
            try:
                return int(value) if value not in [None, ''] else default
            except (ValueError, TypeError):
                return default

        def to_date(value, default=None):
            try:
                return date.fromisoformat(value) if value not in [None, ''] else default
            except (ValueError, TypeError):
                return default

        # Obter e converter dados dos campos do formulário
        lp.numero_lp = to_int(data.get('numero_lp'))
        lp.data_ultimo_lp = to_date(data.get('data_ultimo_lp'))
        lp.numero_prox_lp = to_int(data.get('numero_prox_lp'))
        lp.proximo_lp = to_date(data.get('proximo_lp'))
        lp.mes_proximo_lp = to_int(data.get('mes_proximo_lp'))
        lp.ano_proximo_lp = to_int(data.get('ano_proximo_lp'))
        lp.dias_desconto_lp = to_int(data.get('dias_desconto_lp'), 0)  # Default para 0
        lp.bol_g_pm_lp = data.get('bol_g_pm_lp') or None
        lp.data_publicacao_lp = to_date(data.get('data_publicacao_lp'))
        lp.data_concessao_lp = to_date(data.get('data_concessao_lp'))
        lp.lancamento_sipa = data.get('lancamento_sipa') == 'on'
        lp.observacoes = data.get('observacoes', '')
        lp.situacao_lp = data.get('situacao_lp')
        lp.status_lp = data.get('status_lp')

        lp.user_updated = request.user
        lp.data_atualizacao = timezone.now()

        # Lógica de status: se já tem data de concessão e publicação, status vira 'publicado'
        if lp.data_concessao_lp and lp.data_publicacao_lp:
            lp.status_lp = LP.StatusLP.PUBLICADO
        
        with transaction.atomic():
            lp.full_clean()  # Validação do modelo
            lp.save()

            # Registrar histórico
            HistoricoLP.objects.create(
                lp=lp,
                situacao_lp=lp.situacao_lp,
                status_lp=lp.status_lp,
                usuario_alteracao=request.user,
                numero_lp=lp.numero_lp,
                data_ultimo_lp=lp.data_ultimo_lp,
                numero_prox_lp=lp.numero_prox_lp,
                proximo_lp=lp.proximo_lp,
                mes_proximo_lp=lp.mes_proximo_lp,
                ano_proximo_lp=lp.ano_proximo_lp,
                dias_desconto_lp=lp.dias_desconto_lp,
                bol_g_pm_lp=lp.bol_g_pm_lp,
                data_publicacao_lp=lp.data_publicacao_lp,
                data_concessao_lp=lp.data_concessao_lp,
                lancamento_sipa=lp.lancamento_sipa,
                observacoes_historico=f"Dados da LP atualizados por {request.user.get_full_name() or request.user.email}"
            )

        return alert_response('success', 'Sucesso!', 'LP atualizada com sucesso!', reload_page=True)
        
    except ValidationError as e:
        # Erros de validação do modelo ou campos
        error_messages = e.message_dict if hasattr(e, 'message_dict') else {'__all__': e.messages}
        logger.warning(f"Erro de validação ao editar LP {pk}: {error_messages}")
        return alert_response('error', 'Erro de Validação', 'Por favor, corrija os erros no formulário.', 400, errors=error_messages)
    except Exception as e:
        logger.exception(f"Erro inesperado ao editar LP {pk}: {e}")
        return alert_response('error', 'Erro Interno', 'Ocorreu um erro inesperado ao editar a LP.', 500)


@login_required
@require_POST
def editar_lp(request, pk):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    lp = get_object_or_404(LP, pk=pk)

    if not is_ajax:
        messages.error(request, 'Requisição inválida. Por favor, use o formulário de edição.')
        return redirect('lp:ver_lp', pk=pk)

    try:
        data = request.POST
        
        # Função auxiliar para conversão segura de valores
        def to_int(value, default=None):
            try:
                return int(value) if value not in [None, ''] else default
            except (ValueError, TypeError):
                return default

        def to_date(value, default=None):
            try:
                return date.fromisoformat(value) if value not in [None, ''] else default
            except (ValueError, TypeError):
                return default

        # Obter e converter dados dos campos do formulário
        lp.numero_lp = to_int(data.get('numero_lp'))
        lp.data_ultimo_lp = to_date(data.get('data_ultimo_lp'))
        lp.numero_prox_lp = to_int(data.get('numero_prox_lp'))
        lp.proximo_lp = to_date(data.get('proximo_lp'))
        lp.mes_proximo_lp = to_int(data.get('mes_proximo_lp'))
        lp.ano_proximo_lp = to_int(data.get('ano_proximo_lp'))
        lp.dias_desconto_lp = to_int(data.get('dias_desconto_lp'), 0)  # Default para 0
        lp.bol_g_pm_lp = data.get('bol_g_pm_lp') or None
        lp.data_publicacao_lp = to_date(data.get('data_publicacao_lp'))
        lp.data_concessao_lp = to_date(data.get('data_concessao_lp'))
        lp.lancamento_sipa = data.get('lancamento_sipa') == 'on'
        lp.observacoes = data.get('observacoes', '')
        lp.situacao_lp = data.get('situacao_lp')
        lp.status_lp = data.get('status_lp')

        lp.user_updated = request.user
        lp.data_atualizacao = timezone.now()

        # Lógica de status: se já tem data de concessão e publicação, status vira 'publicado'
        if lp.data_concessao_lp and lp.data_publicacao_lp:
            lp.status_lp = LP.StatusLP.PUBLICADO
        
        with transaction.atomic():
            lp.full_clean()  # Validação do modelo
            lp.save()

            # Registrar histórico
            HistoricoLP.objects.create(
                lp=lp,
                situacao_lp=lp.situacao_lp,
                status_lp=lp.status_lp,
                usuario_alteracao=request.user,
                numero_lp=lp.numero_lp,
                data_ultimo_lp=lp.data_ultimo_lp,
                numero_prox_lp=lp.numero_prox_lp,
                proximo_lp=lp.proximo_lp,
                mes_proximo_lp=lp.mes_proximo_lp,
                ano_proximo_lp=lp.ano_proximo_lp,
                dias_desconto_lp=lp.dias_desconto_lp,
                bol_g_pm_lp=lp.bol_g_pm_lp,
                data_publicacao_lp=lp.data_publicacao_lp,
                data_concessao_lp=lp.data_concessao_lp,
                lancamento_sipa=lp.lancamento_sipa,
                observacoes_historico=f"Dados da LP atualizados por {request.user.get_full_name() or request.user.email}"
            )

        return alert_response('success', 'Sucesso!', 'LP atualizada com sucesso!', reload_page=True)
        
    except ValidationError as e:
        # Erros de validação do modelo ou campos
        error_messages = e.message_dict if hasattr(e, 'message_dict') else {'__all__': e.messages}
        logger.warning(f"Erro de validação ao editar LP {pk}: {error_messages}")
        return alert_response('error', 'Erro de Validação', 'Por favor, corrija os erros no formulário.', 400, errors=error_messages)
    except Exception as e:
        logger.exception(f"Erro inesperado ao editar LP {pk}: {e}")
        return alert_response('error', 'Erro Interno', 'Ocorreu um erro inesperado ao editar a LP.', 500)

@login_required
@require_POST
def confirmar_sipa_lp(request, pk):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    lp = get_object_or_404(LP, pk=pk)

    try:
        password = request.POST.get('password')
        
        if not password:
            if is_ajax:
                return alert_response('error', 'Erro de Validação!', 'A senha é obrigatória.', 400, errors={'password': 'A senha é obrigatória.'})
            messages.error(request, 'A senha é obrigatória.')
            return redirect('lp:ver_lp', pk=lp.pk)
       
        user = authenticate(request, username=request.user.email, password=password)

        if user is None or user != request.user:
            if is_ajax:
                return alert_response('error', 'Erro de Autenticação!', 'Senha incorreta.', 403, errors={'password': 'Senha incorreta.'})
            messages.error(request, 'Senha incorreta.')
            return redirect('lp:ver_lp', pk=lp.pk)
        
        with transaction.atomic():
            lp.lancamento_sipa = True
            lp.status_lp = 'lancado_sipa' # Altera o status para 'Lançado no SIPA'
            lp.user_updated = request.user
            lp.data_atualizacao = timezone.now()
            lp.full_clean()
            lp.save()

            HistoricoLP.objects.create(
                lp=lp,
                situacao_lp=lp.situacao_lp,
                status_lp=lp.status_lp,
                usuario_alteracao=request.user,
                numero_lp=lp.numero_lp,
                data_ultimo_lp=lp.data_ultimo_lp,
                numero_prox_lp=lp.numero_prox_lp,
                proximo_lp=lp.proximo_lp,
                mes_proximo_lp=lp.mes_proximo_lp,
                ano_proximo_lp=lp.ano_proximo_lp,
                dias_desconto_lp=lp.dias_desconto_lp,
                observacoes_historico=f"LP confirmada como lançada no SIPA por {request.user.email}"
            )

        if is_ajax:
            return alert_response('success', 'Sucesso!', 'Lançamento no SIPA confirmado com sucesso!', reload_page=True)
        messages.success(request, 'Lançamento no SIPA confirmado com sucesso!')
        return redirect('lp:ver_lp', pk=lp.pk)

    except ValidationError as e:
        if is_ajax:
            return alert_response('error', 'Erro de Validação', ', '.join(e.messages), 400, errors=e.message_dict)
        messages.error(request, f'Erro de validação: {", ".join(e.messages)}')
    except Exception as e:
        logger.exception(f"Erro ao confirmar SIPA para LP {pk}: {e}")
        if is_ajax:
            return alert_response('error', 'Erro Interno', 'Ocorreu um erro inesperado ao confirmar o lançamento no SIPA.', 500)
        messages.error(request, 'Ocorreu um erro inesperado ao confirmar o lançamento no SIPA. O administrador foi notificado.')
    
    return redirect('lp:ver_lp', pk=pk)



@login_required
@require_http_methods(["GET"])
def carregar_dados_sipa_lp(request, pk):
    """
    View para carregar os dados de uma LP em formato JSON para preencher o modal SIPA.
    """
    lp = get_object_or_404(LP, pk=pk)

    data = {
        'dias_desconto_lp': lp.dias_desconto_lp,
        'data_concessao_lp': lp.data_concessao_lp.strftime('%Y-%m-%d') if lp.data_concessao_lp else '',
        'numero_lp': lp.numero_lp,
        'proximo_lp': lp.proximo_lp.strftime('%Y-%m-%d') if lp.proximo_lp else '',
        'mes_proximo_lp': lp.mes_proximo_lp,
        'ano_proximo_lp': lp.ano_proximo_lp,
        'sexta_parte': lp.sexta_parte, # Supondo que você tem este campo no modelo LP
        'status_lp': lp.status_lp,
        'lancamento_sipa': lp.lancamento_sipa
    }

    return JsonResponse(data)


