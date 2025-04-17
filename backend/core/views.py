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

def capa(request):
    template_name = 'landing.html'
    return render(request, template_name)


@login_required
def index(request):
    hoje = datetime.now()
    mes_atual = hoje.month

    # Debug
    print("\n=== INÍCIO DA VIEW ===")
    
    # Mapeamento de cargos fixos
    CARGO_CHOICES_MAP = {
        'Comandante': '703150000 - CMT',
        'Subcomandante': '703159000 - SUB CMT',
        'Ch Seç Adm': '703159100 - SEC ADM',
        'Cmt do 1º SGB': '703151000 - CMT 1º SGB',
        'Cmt do 2º SGB': '703152000 - CMT 2º SGB',
        'Cmt do 3º SGB': '703153000 - CMT 3º SGB',
        'Cmt do 4º SGB': '703154000 - CMT 4º SGB',
        'Cmt do 5º SGB': '703155000 - CMT 5º SGB',
    }

    # Função otimizada para buscar ocupantes
    def get_ocupante_cargo(cargo_nome):
        try:
            return Cadastro.objects.filter(
                detalhes_situacao__posto_secao=CARGO_CHOICES_MAP[cargo_nome],
                detalhes_situacao__situacao='Efetivo',
                detalhes_situacao__cat_efetivo='Ativo'
            ).select_related('detalhes_situacao')\
             .prefetch_related('imagens', 'promocoes')\
             .first()
        except Exception as e:
            print(f"Erro ao buscar {cargo_nome}: {str(e)}")
            return None

    # Busca dos ocupantes
    comandante = get_ocupante_cargo('Comandante')
    subcomandante = get_ocupante_cargo('Subcomandante')
    
    chefes = {
        cargo: get_ocupante_cargo(cargo) 
        for cargo in ['Ch Seç Adm', 'Cmt do 1º SGB', 'Cmt do 2º SGB', 
                     'Cmt do 3º SGB', 'Cmt do 4º SGB', 'Cmt do 5º SGB']
    }
   # Buscar as 2 últimas publicações de imagens para o carrossel
    imagens_carrossel = Arquivo.objects.filter(tipo='IMAGEM').select_related('documento').order_by('-documento__data_documento')[:2]

  # Aniversariantes - agora sem paginação
    aniversariantes = Cadastro.objects.filter(
        nasc__month=mes_atual
    ).order_by('nasc__day').prefetch_related(
        'imagens', 'promocoes', 'detalhes_situacao'
    )[:100]  # Limite para 100 registros para teste

    # Adicionando posto_grad_recente
    for funcionario in aniversariantes:
        try:
            funcionario.posto_grad_recente = funcionario.promocoes.latest('ultima_promocao').posto_grad
        except Promocao.DoesNotExist:
            funcionario.posto_grad_recente = None

    # Documentos - limitando a 100 registros para teste
    documentos = Documento.objects.all().order_by('-data_criacao')[:100]


    # Lembretes e tarefas
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
            (7, 'Julho'), (8, 'Agosto'), (9, 'Setembro'),  # Corrigido o número do mês
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
    return render(request, 'index.html', context)


from django.views.generic import TemplateView
from datetime import datetime
from django.shortcuts import render

class CalendarioView(TemplateView):
    template_name = 'calendario.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_year = datetime.now().year

        eventos_gb = [
            {"titulo": "Aniversário EB Itaí", "data": f"{current_year}-02-23", "color": "#3b82f6", "tipo": "Evento GB"},
            {"titulo": "Aniversário do CB/SP", "data": f"{current_year}-03-10", "color": "#3b82f6", "tipo": "Evento GB"},
            {"titulo": "Aniversário COBOM Scb", "data": f"{current_year}-03-31", "color": "#3b82f6", "tipo": "Evento GB"},
            {"titulo": "Aniversário - PB Botucatu", "data": f"{current_year}-04-14", "color": "#3b82f6", "tipo": "Evento GB"},
            {"titulo": "Anivers. PB Itapeva", "data": f"{current_year}-05-29", "color": "#3b82f6", "tipo": "Evento GB"},
            {"titulo": "Aniversário do CB/Bra", "data": f"{current_year}-07-02", "color": "#3b82f6", "tipo": "Evento GB"},
            {"titulo": "Aniversário PB Salto", "data": f"{current_year}-07-16", "color": "#3b82f6", "tipo": "Evento GB"},
            {"titulo": "Aniversário PB Tatuí", "data": f"{current_year}-08-08", "color": "#3b82f6", "tipo": "Evento GB"},
            {"titulo": "Aniversário BB Boituva", "data": f"{current_year}-09-03", "color": "#3b82f6", "tipo": "Evento GB"},
            {"titulo": "Aniversário PB Itu", "data": f"{current_year}-09-06", "color": "#3b82f6", "tipo": "Evento GB"},
            {"titulo": "Aniversário - PB Avaré", "data": f"{current_year}-09-15", "color": "#3b82f6", "tipo": "Evento GB"},
            {"titulo": "Aniversário BB Porto Feliz", "data": f"{current_year}-10-26", "color": "#3b82f6", "tipo": "Evento GB"},
            {"titulo": "Aniversário BB Tietê", "data": f"{current_year}-10-27", "color": "#3b82f6", "tipo": "Evento GB"},
            {"titulo": "Aniversário PB Cerrado", "data": f"{current_year}-11-12", "color": "#3b82f6", "tipo": "Evento GB"},
            {"titulo": "Aniversário PB Votorantim", "data": f"{current_year}-12-08", "color": "#3b82f6", "tipo": "Evento GB"},
            {"titulo": "Aniversário BB Apiaí", "data": f"{current_year}-12-10", "color": "#3b82f6", "tipo": "Evento GB"},
            {"titulo": "Aniversário da PM", "data": f"{current_year}-12-15", "color": "#3b82f6", "tipo": "Evento GB"},
            {"titulo": "Aniversário PB Eden", "data": f"{current_year}-12-16", "color": "#3b82f6", "tipo": "Evento GB"},
            {"titulo": "Aniversário BB Cap.Bonito", "data": f"{current_year}-12-17", "color": "#3b82f6", "tipo": "Evento GB"}
        ]

        feriados_nacionais = [
            {"titulo": "Feriado Nacional - Ano Novo", "data": f"{current_year}-01-01", "color": "#ef4444", "tipo": "Nacional"},
            {"titulo": "Feriado Nacional - Carnaval", "data": f"{current_year}-03-03", "color": "#ef4444", "tipo": "Nacional"},
            {"titulo": "Feriado Nacional - Carnaval", "data": f"{current_year}-03-04", "color": "#ef4444", "tipo": "Nacional"},
            {"titulo": "Feriado Nacional - Carnaval", "data": f"{current_year}-03-05", "color": "#ef4444", "tipo": "Nacional"},
            {"titulo": "Feriado Nacional - Sexta-Feira Santa", "data": f"{current_year}-04-18", "color": "#ef4444", "tipo": "Nacional"},
            {"titulo": "Feriado Nacional - Dia de Tiradentes", "data": f"{current_year}-04-21", "color": "#ef4444", "tipo": "Nacional"},
            {"titulo": "Feriado Nacional - Dia do Trabalho", "data": f"{current_year}-05-01", "color": "#ef4444", "tipo": "Nacional"},
            {"titulo": "Feriado Nacional - Corpus Christi", "data": f"{current_year}-06-19", "color": "#ef4444", "tipo": "Nacional"},
            {"titulo": "Feriado Nacional - Independência do Brasil", "data": f"{current_year}-09-07", "color": "#ef4444", "tipo": "Nacional"},
            {"titulo": "Feriado Nacional - Nossa Senhora Aparecida", "data": f"{current_year}-10-12", "color": "#ef4444", "tipo": "Nacional"},
            {"titulo": "Feriado Nacional - Dia das Crianças", "data": f"{current_year}-10-12", "color": "#ef4444", "tipo": "Nacional"},
            {"titulo": "Feriado Nacional - Dia do Professor", "data": f"{current_year}-10-15", "color": "#ef4444", "tipo": "Nacional"},
            {"titulo": "Feriado Nacional - Dia do Servidor Público", "data": f"{current_year}-10-28", "color": "#ef4444", "tipo": "Nacional"},
            {"titulo": "Feriado Nacional - Dia de Finados", "data": f"{current_year}-11-02", "color": "#ef4444", "tipo": "Nacional"},
            {"titulo": "Feriado Nacional - Proclamação da República", "data": f"{current_year}-11-15", "color": "#ef4444", "tipo": "Nacional"},
            {"titulo": "Feriado Nacional - Consciência Negra", "data": f"{current_year}-11-20", "color": "#ef4444", "tipo": "Nacional"},
            {"titulo": "Feriado Nacional - Natal", "data": f"{current_year}-12-25", "color": "#ef4444", "tipo": "Nacional"}
        ]

        feriados_estaduais = [
            {"titulo": "Feriado Estadual - Revolução Constitucionalista", "data": f"{current_year}-07-09", "color": "#f59e0b", "tipo": "Estadual"}
        ]

        feriados_municipais = [
            {"titulo": "Feriado Municipal - Aniversário de Sorocaba", "data": f"{current_year}-06-15", "color": "#10b981", "tipo": "Municipal"},
            {"titulo": "Feriado Municipal - Dia do Padroeiro (São Pedro)", "data": f"{current_year}-06-29", "color": "#10b981", "tipo": "Municipal"},
            {"titulo": "Feriado Municipal - Aniversário de Votorantim", "data": f"{current_year}-08-25", "color": "#10b981", "tipo": "Municipal"},
            {"titulo": "Feriado Municipal - Aniversário de Piedade", "data": f"{current_year}-07-02", "color": "#10b981", "tipo": "Municipal"},
            {"titulo": "Feriado Municipal - Aniversário de Itu", "data": f"{current_year}-02-02", "color": "#10b981", "tipo": "Municipal"},
            {"titulo": "Feriado Municipal - Aniversário de Porto Feliz", "data": f"{current_year}-09-10", "color": "#10b981", "tipo": "Municipal"},
            {"titulo": "Feriado Municipal - Aniversário de Salto", "data": f"{current_year}-08-10", "color": "#10b981", "tipo": "Municipal"},
            {"titulo": "Feriado Municipal - Aniversário de São Roque", "data": f"{current_year}-08-16", "color": "#10b981", "tipo": "Municipal"},
            {"titulo": "Feriado Municipal - Aniversário de Ibiúna", "data": f"{current_year}-03-24", "color": "#10b981", "tipo": "Municipal"},
            {"titulo": "Feriado Municipal - Aniversário de Itapeva", "data": f"{current_year}-09-20", "color": "#10b981", "tipo": "Municipal"},
            {"titulo": "Feriado Municipal - Aniversário de Itararé", "data": f"{current_year}-05-20", "color": "#10b981", "tipo": "Municipal"},
            {"titulo": "Feriado Municipal - Aniversário de Apiaí", "data": f"{current_year}-03-18", "color": "#10b981", "tipo": "Municipal"},
            {"titulo": "Feriado Municipal - Aniversário de Capão Bonito", "data": f"{current_year}-04-19", "color": "#10b981", "tipo": "Municipal"},
            {"titulo": "Feriado Municipal - Aniversário de Itapetininga", "data": f"{current_year}-11-05", "color": "#10b981", "tipo": "Municipal"},
            {"titulo": "Feriado Municipal - Aniversário de Angatuba", "data": f"{current_year}-12-20", "color": "#10b981", "tipo": "Municipal"},
            {"titulo": "Feriado Municipal - Aniversário de Boituva", "data": f"{current_year}-12-23", "color": "#10b981", "tipo": "Municipal"},
            {"titulo": "Feriado Municipal - Aniversário de Tatuí", "data": f"{current_year}-08-11", "color": "#10b981", "tipo": "Municipal"},
            {"titulo": "Feriado Municipal - Aniversário de Tietê", "data": f"{current_year}-03-21", "color": "#10b981", "tipo": "Municipal"},
            {"titulo": "Feriado Municipal - Aniversário de Laranjal Paulista", "data": f"{current_year}-10-27", "color": "#10b981", "tipo": "Municipal"},
            {"titulo": "Feriado Municipal - Aniversário de Botucatu", "data": f"{current_year}-04-14", "color": "#10b981", "tipo": "Municipal"},
            {"titulo": "Feriado Municipal - Aniversário de Itaí", "data": f"{current_year}-08-26", "color": "#10b981", "tipo": "Municipal"},
            {"titulo": "Feriado Municipal - Aniversário de Avaré", "data": f"{current_year}-09-15", "color": "#10b981", "tipo": "Municipal"},
            {"titulo": "Feriado Municipal - Aniversário de Itatinga", "data": f"{current_year}-12-20", "color": "#10b981", "tipo": "Municipal"},
            {"titulo": "Feriado Municipal - Aniversário de Piraju", "data": f"{current_year}-03-21", "color": "#10b981", "tipo": "Municipal"}
        ]

        # Combinar todos os eventos
        todos_eventos = eventos_gb + feriados_nacionais + feriados_estaduais + feriados_municipais
        todos_eventos.sort(key=lambda x: x['data'])

        context.update({
            'eventos': todos_eventos,
            'eventos_fixos': todos_eventos,  # Adicionado para DataTables
            'current_year': current_year
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




class CalendarioEventosView(View):
    def get(self, request, *args, **kwargs):
        # Obter parâmetros de data (FullCalendar envia start e end)
        start = request.GET.get('start')
        end = request.GET.get('end')
        
        try:
            start_date = datetime.strptime(start, '%Y-%m-%d').date()
            end_date = datetime.strptime(end, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return JsonResponse([], safe=False)
        
        # Lista para armazenar todos os eventos
        eventos = []
        
        # 1. Feriados Municipais
        feriados_municipais = self.get_feriados_municipais(start_date.year)
        for cidade, feriados in feriados_municipais.items():
            for feriado in feriados:
                if start_date <= feriado['date'] <= end_date:
                    eventos.append({
                        'title': f"{feriado['name']} ({cidade})",
                        'start': feriado['date'].isoformat(),
                        'color': '#ef4444',  # Vermelho
                        'allDay': True
                    })
        
        # 2. Datas Comemorativas do 15º GB
        datas_comemorativas = self.get_datas_comemorativas(start_date.year)
        for data_com in datas_comemorativas:
            if start_date <= data_com['date'] <= end_date:
                eventos.append({
                    'title': data_com['name'],
                    'start': data_com['date'].isoformat(),
                    'color': '#f59e0b',  # Amarelo
                    'allDay': True
                })
        
        # 3. Eventos Institucionais
        eventos_institucionais = self.get_eventos_institucionais(start_date.year)
        for evento in eventos_institucionais:
            if start_date <= evento['date'] <= end_date:
                eventos.append({
                    'title': evento['name'],
                    'start': evento['date'].isoformat(),
                    'color': '#3b82f6',  # Azul
                    'allDay': True
                })
        
        # 4. Lembretes do usuário
        lembretes = Lembrete.objects.filter(
            user=request.user,
            data__gte=start_date,
            data__lte=end_date
        )
        for lembrete in lembretes:
            eventos.append({
                'title': lembrete.titulo,
                'start': lembrete.data.isoformat(),
                'color': '#8b5cf6',  # Violeta
                'allDay': True
            })
        
        # 5. Tarefas do usuário
        tarefas = Tarefa.objects.filter(
            user=request.user,
            data_inicio__gte=start_date,
            data_inicio__lte=end_date
        )
        for tarefa in tarefas:
            eventos.append({
                'title': tarefa.titulo,
                'start': tarefa.data_inicio.isoformat(),
                'color': '#10b981',  # Verde
                'allDay': not tarefa.hora_inicio  # Se não tem hora, é o dia todo
            })
        
        return JsonResponse(eventos, safe=False)
    
    def get_feriados_municipais(self, year):
        return {
            "Sorocaba": [
                {"name": "Aniversário de Sorocaba", "date": date(year, 6, 15)},
                {"name": "Dia do Padroeiro (São Pedro)", "date": date(year, 6, 29)}
            ],
            # ... (todos os outros municípios)
        }
    
    def get_datas_comemorativas(self, year):
        return [
            {"name": "Dia do Bombeiro (15º GB)", "date": date(year, 7, 2)},
            {"name": "Fundação do 15º GB", "date": date(year, 10, 10)}
        ]
    
    def get_eventos_institucionais(self, year):
        return [
            {"name": "ANIVERSÁRIO DO CSM/MOpB", "date": date(year, 2, 14)},
            {"name": "SOLENIDADE DE 62 ANOS DO 15º GB", "date": date(year, 3, 7)},
            {"name": "ANIVERSÁRIO DO 1º GB", "date": date(year, 3, 27)},
            {"name": "SOLENIDADE DE 23 ANOS DO 18ºGB", "date": date(year, 4, 9)},
            {"name": "SOLENIDADE DE 13 ANOS DO 17º GB", "date": date(year, 4, 16)}
        ]


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