from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from backend.documentos.models import Documento
from backend.efetivo.models import Cadastro, Promocao, Imagem, DetalhesSituacao, CatEfetivo
from backend.municipios.models import Pessoal
from backend.bm.models import Cadastro_bm
from datetime import datetime, date, timedelta
from django.db.models import Q, Sum, Count # Adicionado Sum e Count aqui
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from backend.agenda.models import Lembrete, Tarefa
from django.views.generic import TemplateView, View
from backend.documentos.models import Documento, Arquivo
from django.db.models import Prefetch
from django.contrib import messages
from django.utils import timezone
import logging
import json
from backend.accounts.decorators import permissao_necessaria, apply_model_permissions_filter, permission_required, group_required
from backend.core.utils import filter_by_user_sgb

logger = logging.getLogger(__name__)

def capa(request):
    template_name = 'landing.html'
    return render(request, template_name)


# backend/core/views.py (correção na função index)
@login_required
def index(request):
    hoje = datetime.now()
    mes_atual = hoje.month

    # Verifica se o usuário está autenticado antes de acessar atributos
    cadastro_do_usuario = None
    user_permissoes = None
    
    if request.user.is_authenticated:
        cadastro_do_usuario = getattr(request.user, 'cadastro', None)
        user_permissoes = getattr(request.user, 'permissoes', None)

    # Removido o retorno precoce para permitir que a página seja renderizada
    # mesmo que o usuário não tenha um cadastro militar vinculado.
    if not cadastro_do_usuario:
        messages.warning(request, 'Seu usuário não está vinculado a um cadastro militar. Algumas funcionalidades podem estar limitadas. Por favor, entre em contato com o administrador.')

    FUNCAO_CHOICES_MAP = {
        'Comandante': 'CMT_GB',
        'Subcomandante': 'SUBCMT',
        'Ch Seç Adm': 'CH SEC ADM',
        'Ch SAT': 'CH SAT',
        'Cmt do 1º SGB': 'CMT 1ºSGB',
        'Cmt do 2º SGB': 'CMT 2ºSGB',
        'Cmt do 3º SGB': 'CMT 3ºSGB',
        'Cmt do 4º SGB': 'CMT 4ºSGB',
        'Cmt do 5º SGB': 'CMT 5ºSGB',
    }

    def get_ocupante_por_funcao(funcao_nome):
        try:
            funcao_valor = FUNCAO_CHOICES_MAP.get(funcao_nome)
            queryset = Cadastro.objects.filter(
                detalhes_situacao__funcao=funcao_valor,
                detalhes_situacao__situacao='Efetivo'
            )
            queryset = filter_by_user_sgb(queryset, request.user)
            queryset = queryset.prefetch_related('imagens', 'promocoes', 'detalhes_situacao').order_by('-detalhes_situacao__apresentacao_na_unidade')
            ocupante = queryset.first()
            if ocupante:
                ocupante.latest_promocao = ocupante.promocoes.order_by('-data_alteracao').first()
            return ocupante
        except Exception as e:
            logger.error(f"Erro ao buscar {funcao_nome}: {str(e)}")
            return None

    comandante = get_ocupante_por_funcao('Comandante')
    subcomandante = get_ocupante_por_funcao('Subcomandante')

    chefes = {
        cargo: get_ocupante_por_funcao(cargo)
        for cargo in ['Ch Seç Adm', 'Ch SAT', 'Cmt do 1º SGB', 'Cmt do 2º SGB',
                     'Cmt do 3º SGB', 'Cmt do 4º SGB', 'Cmt do 5º SGB']
    }

    imagens_carrossel = Arquivo.objects.filter(tipo='IMAGEM').select_related('documento').order_by('-documento__data_documento')

    # Para aniversariantes:
    aniversariantes_qs = Cadastro.objects.filter(nasc__month=mes_atual)
    
    # Aplica filtro por SGB se o usuário tem permissão 'sgb' E um cadastro associado.
    # Caso contrário, mostra todos os aniversariantes do mês (não filtra por SGB).
    if user_permissoes == 'sgb' and cadastro_do_usuario:
        user_sgb = None
        latest_situacao = DetalhesSituacao.objects.filter(
            cadastro=cadastro_do_usuario
        ).order_by('-data_alteracao').first()
        if latest_situacao:
            user_sgb = latest_situacao.sgb
        
        if user_sgb:
            aniversariantes = aniversariantes_qs.filter(detalhes_situacao__sgb=user_sgb).distinct()
        else:
            aniversariantes = Cadastro.objects.none() # Sem SGB associado para usuário 'sgb', não mostra nenhum
    elif request.user.is_superuser or user_permissoes in ['admin', 'gestor']:
        # Superusuários, admin e gestores veem todos os aniversariantes sem filtro de SGB
        aniversariantes = aniversariantes_qs
    else:
        # Usuários 'basico' ou outros que não se enquadram nas categorias acima, veem todos os aniversariantes.
        aniversariantes = aniversariantes_qs

    aniversariantes = aniversariantes.order_by('nasc__day').prefetch_related('imagens', 'promocoes', 'detalhes_situacao')[:100]

    for funcionario in aniversariantes:
        try:
            # Garantindo que obtemos a promoção correta
            if hasattr(funcionario, 'promocoes') and funcionario.promocoes.exists():
                funcionario.posto_grad_recente = funcionario.promocoes.order_by('-data_alteracao').first().posto_grad
            else:
                funcionario.posto_grad_recente = None
            
            # Buscar o DetalhesSituacao mais recente para o SGB e Posto/Seção
            latest_situacao = funcionario.detalhes_situacao.order_by('-data_alteracao').first()
            if latest_situacao:
                funcionario.latest_sgb = latest_situacao.sgb
                funcionario.latest_posto_secao = latest_situacao.posto_secao
            else:
                funcionario.latest_sgb = "N/A"
                funcionario.latest_posto_secao = "N/A"

        except Exception as e:
            logger.error(f"Erro ao obter promoção ou detalhes de situação para {funcionario.email}: {str(e)}")
            funcionario.posto_grad_recente = None
            funcionario.latest_sgb = "Erro"
            funcionario.latest_posto_secao = "Erro"

    documentos = Documento.objects.all().order_by('-data_criacao')[:100]

    user_action_logs = request.user.useractionlog_set.all().order_by('-timestamp')[:10] if request.user.is_authenticated else []

    lembretes = Lembrete.objects.filter(
        user=request.user,
        data__year=hoje.year,
        data__month=hoje.month
    ).order_by('data') if request.user.is_authenticated else []

    tarefas = Tarefa.objects.filter(
        user=request.user,
        data_inicio__year=hoje.year,
        data_inicio__month=hoje.month
    ).order_by('data_inicio') if request.user.is_authenticated else []

    context = {
        'aniversariantes': aniversariantes,
        'documentos': documentos,
        'mes_atual': mes_atual,
        'meses': [
            (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'),
            (4, 'Abril'), (5, 'Maio'), (6, 'Junho'),
            (7, 'Julho'), (8, 'Agosto'), (9, 'Setembro'),
            (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
        ],
        'hoje': hoje,
        'lembretes': lembretes,
        'tarefas': tarefas,
        'comandante': comandante,
        'subcomandante': subcomandante,
        'chefes': chefes,
        'imagens_carrossel': imagens_carrossel,
        'cadastro': cadastro_do_usuario,
        'user_action_logs': user_action_logs,
    }
    
    return render(request, 'index.html', context)


@login_required
@permissao_necessaria(level='admin')
def dashboard(request):
    template_name = 'dashboard.html'
    return render(request, template_name)

def exibir_cadastros(request):
    cadastros = Cadastro.objects.all()
    return render(request, 'index.html', {'cadastros': cadastros})

def dashboard_view(request):
    try:
        pessoal_aggregation = Pessoal.objects.aggregate(
            total_cel=Sum('cel'),
            total_ten_cel=Sum('ten_cel'),
            total_maj=Sum('maj'),
            total_cap=Sum('cap'),
            total_tenqo=Sum('tenqo'),
            total_tenqa=Sum('tenqa'),
            total_asp=Sum('asp'),
            total_st_sgt=Sum('st_sgt'),
            total_cb_sd=Sum('cb_sd')
        )
        
        efetivo_fixado = sum(v if v is not None else 0 for v in pessoal_aggregation.values())

        # Correção: usar 'detalhes_situacao' (com underscore)
        efetivo_existente = Cadastro.objects.filter(
            detalhes_situacao__situacao="Efetivo",
        ).count()

        claro = max(efetivo_fixado - efetivo_existente, 0)

        percentual_claro_cb = round((claro / efetivo_fixado * 100), 1) if efetivo_fixado > 0 else 0
        
        bombeiros_municipais = Cadastro_bm.objects.filter(
            situacao="Efetivo"
        ).count()
        
        percentual_claro_cb_bcm = round(((efetivo_fixado - (efetivo_existente + bombeiros_municipais)) / efetivo_fixado * 100), 1) if efetivo_fixado > 0 else 0

        hoje = timezone.now().date()
        mes_passado = hoje - timedelta(days=30)
        
        variacao_fixado = 0
        
        # Correção: usar 'detalhes_situacao' (com underscore)
        existente_mes_passado = Cadastro.objects.filter(
            detalhes_situacao__situacao="Efetivo",
            detalhes_situacao__data_alteracao__date__lte=mes_passado
        ).count()
        variacao_existente = calcular_variacao(existente_mes_passado, efetivo_existente)
        
        claro_mes_passado = max(efetivo_fixado - existente_mes_passado, 0)
        variacao_claro = calcular_variacao(claro_mes_passado, claro)
        
        bm_mes_passado = Cadastro_bm.objects.filter(
            situacao="Efetivo",
            create_at__date__lte=mes_passado
        ).count()
        variacao_bm = calcular_variacao(bm_mes_passado, bombeiros_municipais)

        # Correção: usar 'detalhes_situacao' (com underscore)
        sgb_distribution = DetalhesSituacao.objects.filter(
            situacao="Efetivo"
        ).values('sgb').annotate(
            existente=Count('id'),
        ).order_by('sgb')
        
        for sgb in sgb_distribution:
            sgb_fixado = Pessoal.objects.filter(
                posto__sgb=sgb['sgb']
            ).aggregate(
                total=Sum('cel') + Sum('ten_cel') + Sum('maj') + Sum('cap') + 
                      Sum('tenqo') + Sum('tenqa') + Sum('asp') + 
                      Sum('st_sgt') + Sum('cb_sd')
            )['total'] or 0
            sgb['fixado'] = sgb_fixado
            sgb['claro'] = max(sgb_fixado - sgb['existente'], 0)
            sgb['percentage'] = round((sgb['existente'] / sgb_fixado * 100), 1) if sgb_fixado > 0 else 0

        # Correção: usar 'detalhes_situacao' (com underscore)
        recent_movements = DetalhesSituacao.objects.filter(
            data_alteracao__date__gte=mes_passado
        ).order_by('-data_alteracao')[:5]
        
        formatted_movements = []
        for mov in recent_movements:
            movement_type = 'transfer' if 'transfer' in mov.situacao.lower() else 'admission' if 'admission' in mov.situacao.lower() else 'other'
            formatted_movements.append({
                'type': movement_type,
                'description': f"{mov.cadastro.nome_de_guerra} - {mov.situacao}",
                'date': mov.data_alteracao.strftime('%d/%m/%Y'),
                'unit': mov.sgb,
                'time': mov.data_alteracao.strftime('%H:%M')
            })

        context = {
            'efetivo_fixado': efetivo_fixado or 0,
            'efetivo_existente': efetivo_existente or 0,
            'claro': claro or 0,
            'percentual_claro_cb': percentual_claro_cb or 0,
            'percentual_claro_cb_bcm': percentual_claro_cb_bcm or 0,
            'bombeiros_municipais': bombeiros_municipais or 0,
            'variacao_fixado': variacao_fixado,
            'variacao_existente': variacao_existente,
            'variacao_claro': variacao_claro,
            'variacao_bm': variacao_bm,
            'sgb_data': sgb_distribution,
            'recent_movements': formatted_movements,
            'evolution_data': {
                'labels': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'],
                'fixado': [600, 605, 610, 615, 620, 625, 630, 632, 633, 634, 635, 635],
                'existente': [480, 490, 495, 500, 505, 510, 515, 518, 520, 521, 522, 522]
            },
            'rank_distribution': {
                'labels': ['Oficiais', 'Sargentos', 'Cabos', 'Soldados', 'Temporários'],
                'data': [45, 120, 150, 180, 27]
            },
            'age_distribution': {
                'labels': ['18-24', '25-29', '30-34', '35-39', '40-44', '45+'],
                'data': [85, 120, 150, 90, 60, 17]
            },
            'health_distribution': {
                'labels': ['Apto', 'Apto c/ Restrição', 'Inapto Temporário', 'Inapto Permanente'],
                'data': [380, 90, 40, 12]
            }
        }
        return render(request, 'dashboard.html', context)

    except Exception as e:
        print(f"Erro na dashboard_view: {str(e)}")
        # Loga o traceback completo para depuração
        logger.error("Erro na dashboard_view:", exc_info=True)
        return render(request, 'dashboard.html', {
            'efetivo_fixado': 0,
            'efetivo_existente': 0,
            'claro': 0,
            'percentual_claro_cb': 0,
            'percentual_claro_cb_bcm': 0,
            'bombeiros_municipais': 0,
            'variacao_fixado': 0,
            'variacao_existente': 0,
            'variacao_claro': 0,
            'variacao_bm': 0,
            # Adicione outras variáveis de contexto vazias ou padrão para evitar erros no template
            'sgb_data': [],
            'recent_movements': [],
            'evolution_data': {'labels': [], 'fixado': [], 'existente': []},
            'rank_distribution': {'labels': [], 'data': []},
            'age_distribution': {'labels': [], 'data': []},
            'health_distribution': {'labels': [], 'data': []}
        })

def calcular_variacao(valor_anterior, valor_atual):
    if valor_anterior == 0:
        return 100 if valor_atual > 0 else 0
    return round(((valor_atual - valor_anterior) / valor_anterior) * 100, 1)

class CalendarioView(TemplateView):
    template_name = 'calendario.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_year = datetime.now().year
        
        eventos_gb = [
            {"title": "Aniversário EB Itaí", "start": f"{current_year}-02-23", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário do CB/SP", "start": f"{current_year}-03-10", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário COBOM Scb", "start": f"{current_year}-03-31", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário - PB Botucatu", "start": f"{current_year}-04-14", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Anivers. PB Itapeva", "start": f"{current_year}-05-29", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Feriado Nacional - Dia do Trabalho", "start": f"{current_year}-05-01", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Aniversário do CB/Bra", "start": f"{current_year}-07-02", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário PB Salto", "start": f"{current_year}-07-16", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário PB Tatuí", "start": f"{current_year}-08-08", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário BB Boituva", "start": f"{current_year}-09-03", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário PB Itu", "start": f"{current_year}-09-06", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário - PB Avaré", "start": f"{current_year}-09-15", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário BB Porto Feliz", "start": f"{current_year}-10-26", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário BB Tietê", "start": f"{current_year}-10-27", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário PB Cerrado", "start": f"{current_year}-11-12", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário PB Votorantim", "start": f"{current_year}-12-08", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário BB Apiaí", "start": f"{current_year}-12-10", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário da PM", "start": f"{current_year}-12-15", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário PB Eden", "start": f"{current_year}-12-16", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário BB Cap.Bonito", "start": f"{current_year}-12-17", "color": "#3b82f6", "tipo": "Evento GB"}
        ]

        feriados_nacionais = [
            {"title": "Feriado Nacional - Ano Novo", "start": f"{current_year}-01-01", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Carnaval", "start": f"{current_year}-03-03", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Carnaval", "start": f"{current_year}-03-04", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Carnaval", "start": f"{current_year}-03-05", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Sexta-Feira Santa", "start": f"{current_year}-04-18", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Dia de Tiradentes", "start": f"{current_year}-04-21", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Dia do Trabalho", "start": f"{current_year}-05-01", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Corpus Christi", "start": f"{current_year}-06-19", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Independência do Brasil", "start": f"{current_year}-09-07", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Nossa Senhora Aparecida", "start": f"{current_year}-10-12", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Dia das Crianças", "start": f"{current_year}-10-12", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Dia do Professor", "start": f"{current_year}-10-15", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Dia do Servidor Público", "start": f"{current_year}-10-28", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Dia de Finados", "start": f"{current_year}-11-02", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Proclamação da República", "start": f"{current_year}-11-15", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Consciência Negra", "start": f"{current_year}-11-20", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Natal", "start": f"{current_year}-12-25", "color": "#ef4444", "tipo": "Nacional"}
        ]

        feriados_estaduais = [
            {"title": "Feriado Estadual - Revolução Constitucionalista", "start": f"{current_year}-07-09", "color": "#f59e0b", "tipo": "Estadual"}
        ]

        feriados_municipais = [
            {"title": "Feriado Municipal - Aniversário de Sorocaba", "start": f"{current_year}-06-15", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Dia do Padroeiro (São Pedro)", "start": f"{current_year}-06-29", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Votorantim", "start": f"{current_year}-08-25", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Piedade", "start": f"{current_year}-07-02", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Itu", "start": f"{current_year}-02-02", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Porto Feliz", "start": f"{current_year}-09-10", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Salto", "start": f"{current_year}-08-10", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de São Roque", "start": f"{current_year}-08-16", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Ibiúna", "start": f"{current_year}-03-24", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Itapeva", "start": f"{current_year}-09-20", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Itararé", "start": f"{current_year}-05-20", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Apiaí", "start": f"{current_year}-03-18", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Capão Bonito", "start": f"{current_year}-04-19", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Itapetininga", "start": f"{current_year}-11-05", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Angatuba", "start": f"{current_year}-12-20", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Boituva", "start": f"{current_year}-12-23", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Tatuí", "start": f"{current_year}-08-11", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Tietê", "start": f"{current_year}-03-21", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Laranjal Paulista", "start": f"{current_year}-10-27", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Botucatu", "start": f"{current_year}-04-14", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Itaí", "start": f"{current_year}-08-26", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Avaré", "start": f"{current_year}-09-15", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Itatinga", "start": f"{current_year}-12-20", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Piraju", "start": f"{current_year}-03-21", "color": "#10b981", "tipo": "Municipal"}
        ]

        todos_eventos = eventos_gb + feriados_nacionais + feriados_estaduais + feriados_municipais
        
        context['eventos_json'] = json.dumps(todos_eventos)
        context['eventos_fixos'] = todos_eventos
        
        return context  

@login_required
@permissao_necessaria(level='admin')
def dashboard(request):
    template_name = 'dashboard.html'
    return render(request, template_name)

def exibir_cadastros(request):
    cadastros = Cadastro.objects.all()
    return render(request, 'index.html', {'cadastros': cadastros})

def dashboard_view(request):
    try:
        pessoal_aggregation = Pessoal.objects.aggregate(
            total_cel=Sum('cel'),
            total_ten_cel=Sum('ten_cel'),
            total_maj=Sum('maj'),
            total_cap=Sum('cap'),
            total_tenqo=Sum('tenqo'),
            total_tenqa=Sum('tenqa'),
            total_asp=Sum('asp'),
            total_st_sgt=Sum('st_sgt'),
            total_cb_sd=Sum('cb_sd')
        )
        
        efetivo_fixado = sum(v if v is not None else 0 for v in pessoal_aggregation.values())

        # Correção: usar 'detalhes_situacao' (com underscore)
        efetivo_existente = Cadastro.objects.filter(
            detalhes_situacao__situacao="Efetivo",
        ).count()

        claro = max(efetivo_fixado - efetivo_existente, 0)

        percentual_claro_cb = round((claro / efetivo_fixado * 100), 1) if efetivo_fixado > 0 else 0
        
        bombeiros_municipais = Cadastro_bm.objects.filter(
            situacao="Efetivo"
        ).count()
        
        percentual_claro_cb_bcm = round(((efetivo_fixado - (efetivo_existente + bombeiros_municipais)) / efetivo_fixado * 100), 1) if efetivo_fixado > 0 else 0

        hoje = timezone.now().date()
        mes_passado = hoje - timedelta(days=30)
        
        variacao_fixado = 0
        
        # Correção: usar 'detalhes_situacao' (com underscore)
        existente_mes_passado = Cadastro.objects.filter(
            detalhes_situacao__situacao="Efetivo",
            detalhes_situacao__data_alteracao__date__lte=mes_passado
        ).count()
        variacao_existente = calcular_variacao(existente_mes_passado, efetivo_existente)
        
        claro_mes_passado = max(efetivo_fixado - existente_mes_passado, 0)
        variacao_claro = calcular_variacao(claro_mes_passado, claro)
        
        bm_mes_passado = Cadastro_bm.objects.filter(
            situacao="Efetivo",
            create_at__date__lte=mes_passado
        ).count()
        variacao_bm = calcular_variacao(bm_mes_passado, bombeiros_municipais)

        # Correção: usar 'detalhes_situacao' (com underscore)
        sgb_distribution = DetalhesSituacao.objects.filter(
            situacao="Efetivo"
        ).values('sgb').annotate(
            existente=Count('id'),
        ).order_by('sgb')
        
        for sgb in sgb_distribution:
            sgb_fixado = Pessoal.objects.filter(
                posto__sgb=sgb['sgb']
            ).aggregate(
                total=Sum('cel') + Sum('ten_cel') + Sum('maj') + Sum('cap') + 
                      Sum('tenqo') + Sum('tenqa') + Sum('asp') + 
                      Sum('st_sgt') + Sum('cb_sd')
            )['total'] or 0
            sgb['fixado'] = sgb_fixado
            sgb['claro'] = max(sgb_fixado - sgb['existente'], 0)
            sgb['percentage'] = round((sgb['existente'] / sgb_fixado * 100), 1) if sgb_fixado > 0 else 0

        # Correção: usar 'detalhes_situacao' (com underscore)
        recent_movements = DetalhesSituacao.objects.filter(
            data_alteracao__date__gte=mes_passado
        ).order_by('-data_alteracao')[:5]
        
        formatted_movements = []
        for mov in recent_movements:
            movement_type = 'transfer' if 'transfer' in mov.situacao.lower() else 'admission' if 'admission' in mov.situacao.lower() else 'other'
            formatted_movements.append({
                'type': movement_type,
                'description': f"{mov.cadastro.nome_de_guerra} - {mov.situacao}",
                'date': mov.data_alteracao.strftime('%d/%m/%Y'),
                'unit': mov.sgb,
                'time': mov.data_alteracao.strftime('%H:%M')
            })

        context = {
            'efetivo_fixado': efetivo_fixado or 0,
            'efetivo_existente': efetivo_existente or 0,
            'claro': claro or 0,
            'percentual_claro_cb': percentual_claro_cb or 0,
            'percentual_claro_cb_bcm': percentual_claro_cb_bcm or 0,
            'bombeiros_municipais': bombeiros_municipais or 0,
            'variacao_fixado': variacao_fixado,
            'variacao_existente': variacao_existente,
            'variacao_claro': variacao_claro,
            'variacao_bm': variacao_bm,
            'sgb_data': sgb_distribution,
            'recent_movements': formatted_movements,
            'evolution_data': {
                'labels': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'],
                'fixado': [600, 605, 610, 615, 620, 625, 630, 632, 633, 634, 635, 635],
                'existente': [480, 490, 495, 500, 505, 510, 515, 518, 520, 521, 522, 522]
            },
            'rank_distribution': {
                'labels': ['Oficiais', 'Sargentos', 'Cabos', 'Soldados', 'Temporários'],
                'data': [45, 120, 150, 180, 27]
            },
            'age_distribution': {
                'labels': ['18-24', '25-29', '30-34', '35-39', '40-44', '45+'],
                'data': [85, 120, 150, 90, 60, 17]
            },
            'health_distribution': {
                'labels': ['Apto', 'Apto c/ Restrição', 'Inapto Temporário', 'Inapto Permanente'],
                'data': [380, 90, 40, 12]
            }
        }
        return render(request, 'dashboard.html', context)

    except Exception as e:
        print(f"Erro na dashboard_view: {str(e)}")
        # Loga o traceback completo para depuração
        logger.error("Erro na dashboard_view:", exc_info=True)
        return render(request, 'dashboard.html', {
            'efetivo_fixado': 0,
            'efetivo_existente': 0,
            'claro': 0,
            'percentual_claro_cb': 0,
            'percentual_claro_cb_bcm': 0,
            'bombeiros_municipais': 0,
            'variacao_fixado': 0,
            'variacao_existente': 0,
            'variacao_claro': 0,
            'variacao_bm': 0,
            # Adicione outras variáveis de contexto vazias ou padrão para evitar erros no template
            'sgb_data': [],
            'recent_movements': [],
            'evolution_data': {'labels': [], 'fixado': [], 'existente': []},
            'rank_distribution': {'labels': [], 'data': []},
            'age_distribution': {'labels': [], 'data': []},
            'health_distribution': {'labels': [], 'data': []}
        })

def calcular_variacao(valor_anterior, valor_atual):
    if valor_anterior == 0:
        return 100 if valor_atual > 0 else 0
    return round(((valor_atual - valor_anterior) / valor_anterior) * 100, 1)

class CalendarioView(TemplateView):
    template_name = 'calendario.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_year = datetime.now().year
        
        eventos_gb = [
            {"title": "Aniversário EB Itaí", "start": f"{current_year}-02-23", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário do CB/SP", "start": f"{current_year}-03-10", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário COBOM Scb", "start": f"{current_year}-03-31", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário - PB Botucatu", "start": f"{current_year}-04-14", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Anivers. PB Itapeva", "start": f"{current_year}-05-29", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Feriado Nacional - Dia do Trabalho", "start": f"{current_year}-05-01", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Aniversário do CB/Bra", "start": f"{current_year}-07-02", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário PB Salto", "start": f"{current_year}-07-16", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário PB Tatuí", "start": f"{current_year}-08-08", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário BB Boituva", "start": f"{current_year}-09-03", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário PB Itu", "start": f"{current_year}-09-06", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário - PB Avaré", "start": f"{current_year}-09-15", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário BB Porto Feliz", "start": f"{current_year}-10-26", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário BB Tietê", "start": f"{current_year}-10-27", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário PB Cerrado", "start": f"{current_year}-11-12", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário PB Votorantim", "start": f"{current_year}-12-08", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário BB Apiaí", "start": f"{current_year}-12-10", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário da PM", "start": f"{current_year}-12-15", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário PB Eden", "start": f"{current_year}-12-16", "color": "#3b82f6", "tipo": "Evento GB"},
            {"title": "Aniversário BB Cap.Bonito", "start": f"{current_year}-12-17", "color": "#3b82f6", "tipo": "Evento GB"}
        ]

        feriados_nacionais = [
            {"title": "Feriado Nacional - Ano Novo", "start": f"{current_year}-01-01", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Carnaval", "start": f"{current_year}-03-03", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Carnaval", "start": f"{current_year}-03-04", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Carnaval", "start": f"{current_year}-03-05", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Sexta-Feira Santa", "start": f"{current_year}-04-18", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Dia de Tiradentes", "start": f"{current_year}-04-21", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Dia do Trabalho", "start": f"{current_year}-05-01", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Corpus Christi", "start": f"{current_year}-06-19", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Independência do Brasil", "start": f"{current_year}-09-07", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Nossa Senhora Aparecida", "start": f"{current_year}-10-12", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Dia das Crianças", "start": f"{current_year}-10-12", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Dia do Professor", "start": f"{current_year}-10-15", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Dia do Servidor Público", "start": f"{current_year}-10-28", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Dia de Finados", "start": f"{current_year}-11-02", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Proclamação da República", "start": f"{current_year}-11-15", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Consciência Negra", "start": f"{current_year}-11-20", "color": "#ef4444", "tipo": "Nacional"},
            {"title": "Feriado Nacional - Natal", "start": f"{current_year}-12-25", "color": "#ef4444", "tipo": "Nacional"}
        ]

        feriados_estaduais = [
            {"title": "Feriado Estadual - Revolução Constitucionalista", "start": f"{current_year}-07-09", "color": "#f59e0b", "tipo": "Estadual"}
        ]

        feriados_municipais = [
            {"title": "Feriado Municipal - Aniversário de Sorocaba", "start": f"{current_year}-06-15", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Dia do Padroeiro (São Pedro)", "start": f"{current_year}-06-29", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Votorantim", "start": f"{current_year}-08-25", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Piedade", "start": f"{current_year}-07-02", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Itu", "start": f"{current_year}-02-02", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Porto Feliz", "start": f"{current_year}-09-10", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Salto", "start": f"{current_year}-08-10", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de São Roque", "start": f"{current_year}-08-16", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Ibiúna", "start": f"{current_year}-03-24", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Itapeva", "start": f"{current_year}-09-20", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Itararé", "start": f"{current_year}-05-20", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Apiaí", "start": f"{current_year}-03-18", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Capão Bonito", "start": f"{current_year}-04-19", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Itapetininga", "start": f"{current_year}-11-05", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Angatuba", "start": f"{current_year}-12-20", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Boituva", "start": f"{current_year}-12-23", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Tatuí", "start": f"{current_year}-08-11", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Tietê", "start": f"{current_year}-03-21", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Laranjal Paulista", "start": f"{current_year}-10-27", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Botucatu", "start": f"{current_year}-04-14", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Itaí", "start": f"{current_year}-08-26", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Avaré", "start": f"{current_year}-09-15", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Itatinga", "start": f"{current_year}-12-20", "color": "#10b981", "tipo": "Municipal"},
            {"title": "Feriado Municipal - Aniversário de Piraju", "start": f"{current_year}-03-21", "color": "#10b981", "tipo": "Municipal"}
        ]

        todos_eventos = eventos_gb + feriados_nacionais + feriados_estaduais + feriados_municipais
        
        context['eventos_json'] = json.dumps(todos_eventos)
        context['eventos_fixos'] = todos_eventos
        
        return context  

@login_required
def global_search_view(request):
    """
    View para realizar a busca global no sistema.
    Recebe um termo de busca via parâmetro 'q' na URL e retorna os resultados.
    """
    from .search import GlobalSearch

    query = request.GET.get('q', '').strip()
    results = []

    if query:
        results = GlobalSearch.search(query)
    
    context = {
        'query': query,
        'results': results,
    }
    return render(request, 'global_search/results.html', context)
