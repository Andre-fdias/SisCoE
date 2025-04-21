from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .models import User
from .models import Profile
from backend.documentos.models import Documento
from django.shortcuts import render
from backend.efetivo.models import Cadastro, Promocao, Imagem, DetalhesSituacao
from backend.municipios.models import  Pessoal
from backend.bm.models import Cadastro_bm
from datetime import datetime, date
from django.db.models import Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from backend.agenda.models import Lembrete, Tarefa  # Importe os modelos Lembrete e Tarefa
from django.views.generic import TemplateView, View
from backend.documentos.models import Documento, Arquivo
from django.db.models import Prefetch


def capa(request):
    template_name = 'landing.html'
    return render(request, template_name)






@login_required
def index(request):
    hoje = datetime.now()
    mes_atual = hoje.month

    print("\n=== INÍCIO DA VIEW ===")

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
            print(f"Buscando função: {funcao_nome}")
            funcao_valor = FUNCAO_CHOICES_MAP.get(funcao_nome)
            print(f"Valor da função: {funcao_valor}")
            queryset = Cadastro.objects.filter(
                detalhes_situacao__funcao=funcao_valor,
                detalhes_situacao__situacao='Efetivo',
                detalhes_situacao__cat_efetivo='ATIVO'
            ).prefetch_related('imagens', 'promocoes', 'detalhes_situacao').order_by('-detalhes_situacao__apresentacao_na_unidade')
            ocupante = queryset.first()
            if ocupante:
                ocupante.latest_promocao = ocupante.promocoes.order_by('-data_alteracao').first()
                print(f"  {funcao_nome}: {ocupante.nome_de_guerra}, Última Promoção: {ocupante.latest_promocao}") # Debug
                if ocupante.latest_promocao:
                    print(f"    Posto/Graduação: {ocupante.latest_promocao.posto_grad}") # Debug
            return ocupante
        except Exception as e:
            print(f"Erro ao buscar {funcao_nome}: {str(e)}")
            return None

    comandante = get_ocupante_por_funcao('Comandante')
    subcomandante = get_ocupante_por_funcao('Subcomandante')

    chefes = {
        cargo: get_ocupante_por_funcao(cargo)
        for cargo in ['Ch Seç Adm', 'Ch SAT', 'Cmt do 1º SGB', 'Cmt do 2º SGB',
                     'Cmt do 3º SGB', 'Cmt do 4º SGB', 'Cmt do 5º SGB']
    }

    imagens_carrossel = Arquivo.objects.filter(tipo='IMAGEM').select_related('documento').order_by('-documento__data_documento')[:2]

    aniversariantes = Cadastro.objects.filter(
        nasc__month=mes_atual
    ).order_by('nasc__day').prefetch_related(
        'imagens', 'promocoes', 'detalhes_situacao'
    )[:100]

    for funcionario in aniversariantes:
        try:
           funcionario.posto_grad_recente = funcionario.promocoes.order_by('-data_alteracao').first().posto_grad if funcionario.promocoes.exists() else None
        except Promocao.DoesNotExist:
            funcionario.posto_grad_recente = None

    documentos = Documento.objects.all().order_by('-data_criacao')[:100]

    lembretes = Lembrete.objects.filter(
        user=request.user,
        data__year=hoje.year,
        data__month=hoje.month
    ).order_by('data')

    tarefas = Tarefa.objects.filter(
        user=request.user,
        data_inicio__year=hoje.year,
        data_inicio__month=hoje.month
    ).order_by('data_inicio')

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
    }
    print("=== FIM DA VIEW ===")
    return render(request, 'index.html', context)



from django.shortcuts import render
from django.views.generic import TemplateView
from datetime import datetime
from calendar import monthcalendar

class CalendarioView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = datetime.now().year
        month = datetime.now().month

        cal = monthcalendar(year, month)
        month_name = datetime(year, month, 1).strftime("%B")

        def criar_evento_dict(day, titulo, cor, tipo):
            return {"day": day, "title": titulo, "color": cor, "tipo": tipo}

        # Eventos do 15º GB (only day is relevant here)
        eventos_gb_simples = [
            criar_evento_dict(23, "Aniversário EB Itaí", "#3b82f6", "Evento GB"),
            criar_evento_dict(10, "Aniversário do CB/SP", "#3b82f6", "Evento GB"),
            criar_evento_dict(31, "Aniversário COBOM Scb", "#3b82f6", "Evento GB"),
            criar_evento_dict(14, "Aniversário - PB Botucatu", "#3b82f6", "Evento GB"),
            criar_evento_dict(29, "Anivers. PB Itapeva", "#3b82f6", "Evento GB"),
            criar_evento_dict(2, "Aniversário do CB/Bra", "#3b82f6", "Evento GB"),
            criar_evento_dict(16, "Aniversário PB Salto", "#3b82f6", "Evento GB"),
            criar_evento_dict(8, "Aniversário PB Tatuí", "#3b82f6", "Evento GB"),
            criar_evento_dict(3, "Aniversário BB Boituva", "#3b82f6", "Evento GB"),
            criar_evento_dict(6, "Aniversário PB Itu", "#3b82f6", "Evento GB"),
            criar_evento_dict(15, "Aniversário - PB Avaré", "#3b82f6", "Evento GB"),
            criar_evento_dict(26, "Aniversário BB Porto Feliz", "#3b82f6", "Evento GB"),
            criar_evento_dict(27, "Aniversário BB Tietê", "#3b82f6", "Evento GB"),
            criar_evento_dict(12, "Aniversário PB Cerrado", "#3b82f6", "Evento GB"),
            criar_evento_dict(8, "Aniversário PB Votorantim", "#3b82f6", "Evento GB"),
            criar_evento_dict(10, "Aniversário BB Apiaí", "#3b82f6", "Evento GB"),
            criar_evento_dict(15, "Aniversário da PM", "#3b82f6", "Evento GB"),
            criar_evento_dict(16, "Aniversário PB Eden", "#3b82f6", "Evento GB"),
            criar_evento_dict(17, "Aniversário BB Cap.Bonito", "#3b82f6", "Evento GB")
        ]

        # Feriados Nacionais
        feriados_nacionais_simples = [
            criar_evento_dict(1, "Ano Novo", "#ef4444", "Nacional"),
            criar_evento_dict(18, "Sexta-Feira Santa", "#ef4444", "Nacional"),
            criar_evento_dict(21, "Tiradentes", "#ef4444", "Nacional"),
            criar_evento_dict(1, "Dia do Trabalho", "#ef4444", "Nacional"),
            criar_evento_dict(7, "Independência", "#ef4444", "Nacional"),
            criar_evento_dict(12, "N.S. Aparecida", "#ef4444", "Nacional"),
            criar_evento_dict(2, "Finados", "#ef4444", "Nacional"),
            criar_evento_dict(15, "Proclamação República", "#ef4444", "Nacional"),
            criar_evento_dict(25, "Natal", "#ef4444", "Nacional")
        ]

        # Feriados Estaduais
        feriados_estaduais_simples = [
            criar_evento_dict(9, "Revolução Constitucionalista", "#f59e0b", "Estadual")
        ]

        # Feriados Municipais
        feriados_municipais_simples = [
            criar_evento_dict(2, "Aniversário Itu", "#10b981", "Municipal"),
            criar_evento_dict(18, "Aniversário Apiaí", "#10b981", "Municipal"),
            criar_evento_dict(21, "Aniversário Tietê", "#10b981", "Municipal"),
            criar_evento_dict(19, "Aniversário Capão Bonito", "#10b981", "Municipal"),
            criar_evento_dict(15, "Aniversário Sorocaba", "#10b981", "Municipal"),
            criar_evento_dict(29, "Dia do Padroeiro", "#10b981", "Municipal"),
            criar_evento_dict(10, "Aniversário Salto", "#10b981", "Municipal"),
            criar_evento_dict(11, "Aniversário Tatuí", "#10b981", "Municipal"),
            criar_evento_dict(25, "Aniversário Votorantim", "#10b981", "Municipal"),
            criar_evento_dict(10, "Aniversário Porto Feliz", "#10b981", "Municipal"),
            criar_evento_dict(20, "Aniversário Itapeva", "#10b981", "Municipal"),
            criar_evento_dict(27, "Aniversário Laranjal Paulista", "#10b981", "Municipal"),
            criar_evento_dict(5, "Aniversário Itapetininga", "#10b981", "Municipal"),
            criar_evento_dict(20, "Aniversário Angatuba", "#10b981", "Municipal"),
            criar_evento_dict(23, "Aniversário Boituva", "#10b981", "Municipal")
        ]

        todos_eventos_simples = (
            eventos_gb_simples +
            feriados_nacionais_simples +
            feriados_estaduais_simples +
            feriados_municipais_simples
        )

        event_dict = {}
        for event in todos_eventos_simples:
            if event['day'] not in event_dict:
                event_dict[event['day']] = []
            event_dict[event['day']].append({'title': event['title'], 'color': event['color'], 'tipo': event['tipo']})

        context.update({
            'calendar': cal,
            'month_name': month_name,
            'year': year,
            'event_dict': event_dict,
        })
        return context



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


def exibir_cadastros(request):
    cadastros = Cadastro.objects.all()
    return render(request, 'index.html', {'cadastros': cadastros})




from django.db.models import Sum, Count, Q
from backend.municipios.models import Pessoal
from backend.efetivo.models import Cadastro, DetalhesSituacao
from backend.bm.models import Cadastro_bm
from datetime import date, timedelta
from django.utils import timezone

def dashboard_view(request):
    try:
        # 1. Efetivo Fixado - Soma de todo o pessoal dos postos
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
        
        # Calcula o total, substituindo None por 0
        efetivo_fixado = sum(v if v is not None else 0 for v in pessoal_aggregation.values())

        # 2. Efetivo Existente - Correção: usando Cadastro através do relacionamento
        efetivo_existente = Cadastro.objects.filter(
            detalhes_situacao__situacao="Efetivo",
        ).count()

        # 3. Claro (diferença entre fixado e existente)
        claro = max(efetivo_fixado - efetivo_existente, 0)  # Garante não negativo

        # 4. % de Claro - Dois cálculos diferentes
        percentual_claro_cb = round((claro / efetivo_fixado * 100), 1) if efetivo_fixado > 0 else 0
        
        # 5. Bombeiros Municipais
        bombeiros_municipais = Cadastro_bm.objects.filter(
            situacao="Efetivo"
        ).count()
        
        # Cálculo do percentual Claro CB + BCM
        percentual_claro_cb_bcm = round(((claro + bombeiros_municipais) / efetivo_fixado * 100), 1) if efetivo_fixado > 0 else 0

        # Cálculo das variações em relação ao mês anterior
        hoje = timezone.now().date()
        mes_passado = hoje - timedelta(days=30)
        
        # Variação do Efetivo Fixado (assumindo que não muda frequentemente)
        variacao_fixado = 0  # Normalmente fixo
        
        # Variação do Efetivo Existente
        existente_mes_passado = Cadastro.objects.filter(
            detalhes_situacao__situacao="Efetivo",
            detalhes_situacao__data_alteracao__date__lte=mes_passado
        ).count()
        variacao_existente = calcular_variacao(existente_mes_passado, efetivo_existente)
        
        # Variação do Claro
        claro_mes_passado = max(efetivo_fixado - existente_mes_passado, 0)
        variacao_claro = calcular_variacao(claro_mes_passado, claro)
        
        # Variação dos Bombeiros Municipais
        bm_mes_passado = Cadastro_bm.objects.filter(
            situacao="Efetivo",
            create_at__date__lte=mes_passado
        ).count()
        variacao_bm = calcular_variacao(bm_mes_passado, bombeiros_municipais)

        # Dados para os gráficos
        # Distribuição por SGB
        sgb_distribution = DetalhesSituacao.objects.filter(
            situacao="Efetivo"
        ).values('sgb').annotate(
            existente=Count('id'),
        ).order_by('sgb')
        
        # Adicionando dados fixados por SGB
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

        # Movimentações recentes (últimos 30 dias)
        recent_movements = DetalhesSituacao.objects.filter(
            data_alteracao__date__gte=mes_passado
        ).order_by('-data_alteracao')[:5]
        
        # Transformar em formato para o template
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
            # Cards principais
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
            
            # Dados para gráficos e tabelas
            'sgb_data': sgb_distribution,
            'recent_movements': formatted_movements,
            
            # Dados temporários para os gráficos
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
        # Retorna valores padrão em caso de erro
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
        })

def calcular_variacao(valor_anterior, valor_atual):
    if valor_anterior == 0:
        return 100 if valor_atual > 0 else 0
    return round(((valor_atual - valor_anterior) / valor_anterior) * 100, 1)