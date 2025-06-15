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
        data_inicio_periodo=lp_instance.data_inicio_periodo, 
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
    historico_lp = HistoricoLP.objects.filter(lp=lp).order_by('-data_alteracao')

    # Inicializando variáveis
    progresso_percentual = 0
    dias_restantes_periodo = 0
    dias_decorridos_periodo = 0
    total_dias_periodo = 0
    is_apta_concessao = False
    data_inicio_periodo = None
    data_fim_periodo = None

    # Se temos a data do último LP, podemos calcular o período aquisitivo
    if lp.data_ultimo_lp:
        # O início do período aquisitivo é o dia seguinte ao último LP
        data_inicio_periodo = lp.data_ultimo_lp + timedelta(days=1)
        
        # O fim do período aquisitivo é 5 anos depois do início
        data_fim_periodo = data_inicio_periodo + relativedelta(years=5) - timedelta(days=1)
        
        hoje = timezone.localdate()
        
        # Calculando o total de dias do período
        total_dias_periodo = (data_fim_periodo - data_inicio_periodo).days
        
        # Se o período ainda não começou
        if hoje < data_inicio_periodo:
            dias_decorridos_periodo = 0
            dias_restantes_periodo = total_dias_periodo
        
        # Se o período já terminou
        elif hoje > data_fim_periodo:
            dias_decorridos_periodo = total_dias_periodo
            dias_restantes_periodo = 0
            progresso_percentual = 100
        
        # Se estamos dentro do período
        else:
            dias_decorridos_periodo = (hoje - data_inicio_periodo).days
            dias_restantes_periodo = (data_fim_periodo - hoje).days
            
            if total_dias_periodo > 0:
                progresso_percentual = (dias_decorridos_periodo / total_dias_periodo) * 100
        
        # Verificando se a LP está apta para concessão
        is_apta_concessao = (
            lp.status_lp == LP.StatusLP.AGUARDANDO_REQUISITOS and 
            progresso_percentual >= 100
        )

    context = {
        'lp': lp,
        'historico_lp': historico_lp,
        'n_choices': N_CHOICES,
        'situacao_choices': situacao_choices,
        'status_lp_choices': LP.StatusLP.choices,
        'progresso_percentual': round(progresso_percentual, 2),
        'dias_decorridos_periodo': dias_decorridos_periodo,
        'dias_restantes_periodo': dias_restantes_periodo,
        'total_dias_periodo': total_dias_periodo,
        'is_apta_concessao': is_apta_concessao,
        'data_inicio_periodo': data_inicio_periodo,  # Passando para o template
        'data_fim_periodo': data_fim_periodo,        # Passando para o template
        'hoje': timezone.localdate(),
    }
    return render(request, 'lp/detalhar_lp.html', context)



@login_required
@require_POST
def editar_concessao_lp(request, pk):
    lp = get_object_or_404(LP, pk=pk)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        data_concessao_str = request.POST.get('data_concessao')
        bol_g_pm_lp = request.POST.get('bol_g_pm_lp')
        data_publicacao_str = request.POST.get('data_publicacao')
        
        errors = {}
        if not data_concessao_str:
            errors['data_concessao'] = 'A data de concessão é obrigatória.'
        
        if data_concessao_str:
            try:
                data_concessao = datetime.strptime(data_concessao_str, '%Y-%m-%d').date()
            except ValueError:
                errors['data_concessao'] = 'Formato de data inválido para Data de Concessão.'
        else:
            data_concessao = None

        if data_publicacao_str:
            try:
                data_publicacao = datetime.strptime(data_publicacao_str, '%Y-%m-%d').date()
            except ValueError:
                errors['data_publicacao'] = 'Formato de data inválido para Data de Publicação.'
        else:
            data_publicacao = None

        if data_concessao and data_publicacao and data_publicacao < data_concessao:
            errors['data_publicacao'] = 'A data de publicação não pode ser anterior à data de concessão.'

        if errors:
            if is_ajax:
                return alert_response('error', 'Erro de Validação!', 'Verifique os dados informados.', errors=errors, status=400)
            for field, msg in errors.items():
                messages.error(request, msg)
            return redirect('lp:ver_lp', pk=lp.id)

        try:
            with transaction.atomic():
                lp.data_concessao_lp = data_concessao
                lp.bol_g_pm_lp = bol_g_pm_lp
                lp.data_publicacao_lp = data_publicacao
                
                if lp.data_concessao_lp:
                    lp.situacao_lp = "Concedido"
                    lp.status_lp = LP.StatusLP.CONCEDIDA
                
                lp.user_updated = request.user
                lp.save()
                
                create_historico_lp(lp, request.user, "Dados de concessão de LP editados.")

                success_msg = 'Dados de concessão da LP atualizados com sucesso!'
                if is_ajax:
                    return alert_response('success', 'Sucesso!', success_msg, reload_page=True) 
                messages.success(request, success_msg)
                return redirect('lp:ver_lp', pk=lp.id)
        except Exception as e:
            error_msg = f'Ocorreu um erro inesperado ao atualizar a LP: {str(e)}'
            logger.exception(f"Erro em editar_concessao_lp: {str(e)}")
            if is_ajax:
                return alert_response('error', 'Erro Interno!', error_msg, status=500)
            messages.error(request, error_msg)

    if is_ajax:
        return alert_response('error', 'Erro!', 'Requisição inválida.', status=400)
    return redirect('lp:ver_lp', pk=lp.id)


@login_required
@require_POST
def concluir_lp(request, pk):
    lp = get_object_or_404(LP, pk=pk)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if not request.user.check_password(request.POST.get('password')):
        error_msg = 'Senha incorreta.'
        if is_ajax:
            return JsonResponse({'success': False, 'error': error_msg}, status=401)
        messages.error(request, error_msg)
        return redirect('lp:ver_lp', pk=lp.id)

    data_conclusao_str = request.POST.get('data_conclusao')
    if not data_conclusao_str:
        error_msg = 'A data de conclusão é obrigatória.'
        if is_ajax:
            return JsonResponse({'success': False, 'error': error_msg}, status=400)
        messages.error(request, error_msg)
        return redirect('lp:ver_lp', pk=lp.id)
    
    try:
        data_conclusao = datetime.strptime(data_conclusao_str, '%Y-%m-%d').date()
    except ValueError:
        error_msg = 'Formato de data inválido.'
        if is_ajax:
            return JsonResponse({'success': False, 'error': error_msg}, status=400)
        messages.error(request, error_msg)
        return redirect('lp:ver_lp', pk=lp.id)

    try:
        with transaction.atomic():
            lp.situacao_lp = "Concluído"
            lp.status_lp = LP.StatusLP.CONCLUIDA
            lp.data_concessao_lp = data_conclusao 
            lp.user_updated = request.user
            lp.usuario_conclusao = request.user
            lp.save()
            
            create_historico_lp(lp, request.user, f"LP concluída em {data_conclusao.strftime('%d/%m/%Y')}.")
            
            success_message = f'LP {lp.numero_lp} concluída com sucesso!'
            if is_ajax:
                return JsonResponse({'success': True, 'message': success_message, 'reload_page': True}) 
            messages.success(request, success_message)
            return redirect('lp:ver_lp', pk=lp.id)

    except Exception as e:
        error_msg = f'Erro ao concluir a LP: {str(e)}'
        logger.exception(f"Erro em concluir_lp: {str(e)}")
        if is_ajax:
            return JsonResponse({'success': False, 'error': error_msg}, status=500)
        messages.error(request, error_msg)
        return redirect('lp:ver_lp', pk=lp.id)

@login_required
@require_POST
def editar_dias_desconto_lp(request, pk):
    lp = get_object_or_404(LP, pk=pk)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    dias_desconto_str = request.POST.get('dias_desconto_lp')
    if not dias_desconto_str:
        error_msg = 'O número de dias de desconto é obrigatório.'
        if is_ajax:
            return alert_response('error', 'Erro!', error_msg, status=400)
        messages.error(request, error_msg)
        return redirect('lp:ver_lp', pk=lp.id)

    try:
        dias_desconto = int(dias_desconto_str)
        if dias_desconto < 0:
            raise ValueError("O número de dias de desconto não pode ser negativo.")
    except ValueError as e:
        error_msg = f'Valor inválido para dias de desconto: {str(e)}'
        if is_ajax:
            return alert_response('error', 'Erro!', error_msg, status=400)
        messages.error(request, error_msg)
        return redirect('lp:ver_lp', pk=lp.id)

    try:
        with transaction.atomic():
            lp.dias_desconto_lp = dias_desconto
            lp.user_updated = request.user
            lp.save()
            
            create_historico_lp(lp, request.user, f"Dias de desconto da LP alterados para {dias_desconto} dias.")

            success_msg = 'Dias de desconto da LP atualizados com sucesso!'
            if is_ajax:
                return alert_response('success', 'Sucesso!', success_msg, reload_page=True)
            messages.success(request, success_msg)
            return redirect('lp:ver_lp', pk=lp.id)
    except Exception as e:
        error_msg = f'Ocorreu um erro inesperado ao atualizar os dias de desconto: {str(e)}'
        logger.exception(f"Erro em editar_dias_desconto_lp: {str(e)}")
        if is_ajax:
            return alert_response('error', 'Erro Interno!', error_msg, status=500)
        messages.error(request, error_msg)
        return redirect('lp:ver_lp', pk=lp.id)

@login_required
@require_POST
def confirmar_sipa_lp(request, pk):
    lp = get_object_or_404(LP, pk=pk)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    password = request.POST.get('password')
    bol_g_pm_sipa = request.POST.get('bol_g_pm_sipa', '').strip()

    if not request.user.check_password(password):
        error_msg = 'Senha incorreta.'
        if is_ajax:
            return JsonResponse({'success': False, 'error': error_msg, 'alert': {'type': 'error', 'title': 'Erro!', 'message': error_msg}}, status=401)
        messages.error(request, error_msg)
        return redirect('lp:ver_lp', pk=lp.id)

    try:
        with transaction.atomic():
            lp.lancamento_sipa = True
            lp.user_updated = request.user
            
            if bol_g_pm_sipa:
                lp.bol_g_pm_lp = bol_g_pm_sipa

            if lp.status_lp == LP.StatusLP.CONCEDIDA:
                lp.status_lp = LP.StatusLP.PENDENTE_SIPA 

            lp.save()
            
            create_historico_lp(lp, request.user, f"LP lançada/confirmada no SIPA. BOL GPm: {bol_g_pm_sipa or 'Não informado'}")

            success_msg = f'Lançamento da LP {lp.numero_lp} no SIPA confirmado com sucesso!'
            if is_ajax:
                return JsonResponse({'success': True, 'message': success_msg, 'alert': {'type': 'success', 'title': 'Sucesso!', 'message': success_msg}, 'reload_page': True})
            messages.success(request, success_msg)
            return redirect('lp:ver_lp', pk=lp.id)
    except Exception as e:
        error_msg = f'Erro ao confirmar o lançamento da LP no SIPA: {str(e)}'
        logger.exception(f"Erro em confirmar_sipa_lp: {str(e)}")
        if is_ajax:
            return JsonResponse({'success': False, 'error': error_msg, 'alert': {'type': 'error', 'title': 'Erro Interno!', 'message': error_msg}}, status=500)
        messages.error(request, error_msg)
        return redirect('lp:ver_lp', pk=lp.id)


@login_required
@require_POST
def excluir_lp(request, pk):
    lp = get_object_or_404(LP, pk=pk)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    password = request.POST.get('password')

    if not request.user.check_password(password):
        error_msg = 'Senha incorreta.'
        if is_ajax:
            return JsonResponse({'success': False, 'error': error_msg, 'alert': {'type': 'error', 'title': 'Erro!', 'message': error_msg}}, status=401)
        messages.error(request, error_msg)
        return redirect('lp:ver_lp', pk=lp.id)

    try:
        with transaction.atomic():
            cadastro_id = lp.cadastro.id 
            lp_numero = lp.numero_lp
            
            HistoricoLP.objects.create(
                lp=lp, 
                usuario_alteracao=request.user,
                situacao_lp="Excluída", 
                status_lp=LP.StatusLP.CONCLUIDA, 
                numero_lp=lp.numero_lp,
                data_ultimo_lp=lp.data_ultimo_lp,
                data_inicio_periodo=lp.data_inicio_periodo, 
                data_alteracao=timezone.now(),
                observacoes_historico=f"LP {lp_numero} excluída por {request.user.username}."
            )
            
            lp.delete()

            success_msg = f'LP {lp_numero} excluída com sucesso.'
            if is_ajax:
                redirect_url = reverse('lp:listar_lp') 
                return JsonResponse({'success': True, 'message': success_msg, 'alert': {'type': 'success', 'title': 'Sucesso!', 'message': success_msg}, 'redirect_url': redirect_url})
            messages.success(request, success_msg)
            return redirect('lp:listar_lp') 
            
    except Exception as e:
        error_msg = f'Erro ao excluir a LP: {str(e)}'
        logger.exception(f"Erro em excluir_lp: {str(e)}")
        if is_ajax:
            return JsonResponse({'success': False, 'error': error_msg, 'alert': {'type': 'error', 'title': 'Erro Interno!', 'message': error_msg}}, status=500)
        messages.error(request, error_msg)
        return redirect('lp:ver_lp', pk=pk) 


@login_required
def listar_lp(request): 
    lps = LP.objects.all().order_by('cadastro__nome_de_guerra', 'numero_lp')
    context = {
        'lps': lps,
        'N_CHOICES': N_CHOICES 
    }
    return render(request, 'lp/listar_lp.html', context)
