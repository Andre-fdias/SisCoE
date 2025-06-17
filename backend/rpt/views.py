# backend/rpt/views.py

# Standard library imports
from datetime import datetime, timedelta
from io import BytesIO

# Third-party imports
import pandas as pd
# Note: reportlab imports are needed in export_utils.py, not directly here usually
# from reportlab.lib.pagesizes import letter
# from reportlab.pdfgen import canvas

# Django imports
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.messages import constants
# Mantenha a importação do Prefetch
from django.db.models import Prefetch
# Importe FieldError do local correto
from django.core.exceptions import FieldError # Import FieldError for specific handling
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
import logging
from django.core.exceptions import ValidationError
from django.db import IntegrityError
# Local application imports
# Adjust the import path based on your project structure
from backend.efetivo.models import Cadastro, DetalhesSituacao, Promocao, Imagem
from .models import Cadastro_rpt, HistoricoRpt
# --- FIX for ImportError: Import the correct function name from export_utils ---
from .export_utils import export_rpt_data

# ==============================================
# VIEWS
# ==============================================


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
            messages.add_message(request, constants.ERROR, 'Cadastro não encontrado. Por favor, pesquise um RE válido.')
            return redirect('rpt:cadastrar_rpt')

        cadastro = get_object_or_404(Cadastro, id=cadastro_id)

        # Verificar se já existe um cadastro com status "aguardando" para o RE retornado
        cadastro_existente = Cadastro_rpt.objects.filter(cadastro=cadastro, status='Aguardando').exists()
        if cadastro_existente:
            messages.add_message(request, constants.ERROR, 'Militar ja possui cadasto ativo no Rpt.')
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
        messages.add_message(request, constants.SUCCESS, 'Cadastro realizado com Sucesso.')
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


from django.db import models  # Adicione esta linha
from django.db.models import Count, Q, F, Window, Subquery, OuterRef
from django.db.models.functions import RowNumber

@login_required
def ver_rpt(request, id):
    # Subquery para total_secao
    count_subquery = Cadastro_rpt.objects.filter(
        posto_secao_destino=OuterRef('posto_secao_destino')
    ).values('posto_secao_destino').annotate(
        count=Count('id')
    ).values('count')

    # Consulta principal com posicao
    cadastro_rpt = get_object_or_404(
        Cadastro_rpt.objects.annotate(
            posicao=Window(
                expression=RowNumber(),
                partition_by=[F('posto_secao_destino')],
                order_by=[
                    F('data_pedido').asc(),  # Ordem ascendente pela data
                    F('id').asc()  # Desempate pelo ID mais antigo
                ]
            ),
            total_secao=Subquery(count_subquery, output_field=models.IntegerField())
        )
        .select_related('cadastro')
        .prefetch_related('cadastro__detalhes_situacao'),
        id=id
    )

    # Dados relacionados
    cadastro = cadastro_rpt.cadastro
    detalhes_situacao = cadastro.detalhes_situacao.last()
    promocao = cadastro.promocoes.last()

   
       # Lista de inscritos com a mesma ordenação E status Aguardando
    inscritos_secao = Cadastro_rpt.objects.filter(
        posto_secao_destino=cadastro_rpt.posto_secao_destino,
        status='Aguardando'  # Filtro adicionado aqui
    ).annotate(
        posicao=Window(
            expression=RowNumber(),
            partition_by=[F('posto_secao_destino')],
            order_by=[F('data_pedido').asc(), F('id').asc()]
        )
    ).order_by('posicao')  # Ordenar pela posição calculada
    posicao_real = None
    for idx, inscrito in enumerate(inscritos_secao.filter(status='Aguardando'), start=1):
          if inscrito.id == cadastro_rpt.id:
            posicao_real = idx
            break
 
    context = {
        'cadastro_rpt': cadastro_rpt,
        'posicao': posicao_real,  # Nome corrigido
        'total_secao': cadastro_rpt.total_secao,  # Nome corrigido
        'inscritos_secao': inscritos_secao,
        'cadastro': cadastro,
        'detalhes_situacao': detalhes_situacao,
        'promocao': promocao,
    }
    return render(request, 'ver_rpt.html', context)



from django.shortcuts import render, get_object_or_404, redirect
from .models import Cadastro_rpt
from django.contrib.auth.decorators import login_required
import logging


logger = logging.getLogger(__name__)

@login_required
def editar_rpt(request, id):
    cadastro_rpt = get_object_or_404(Cadastro_rpt, id=id)

    if request.method == "GET":
        data = {
            'id': cadastro_rpt.id,
            'data_pedido': str(cadastro_rpt.data_pedido),
            'data_movimentacao': str(cadastro_rpt.data_movimentacao) if cadastro_rpt.data_movimentacao else None,
            'create': str(cadastro_rpt.create) if cadastro_rpt.create else None,
            'status': cadastro_rpt.status,
            'sgb_destino': cadastro_rpt.sgb_destino,
            'posto_secao_destino': cadastro_rpt.posto_secao_destino,
            'doc_solicitacao': cadastro_rpt.doc_solicitacao,
            'doc_alteracao': cadastro_rpt.doc_alteracao,
            'doc_movimentacao': cadastro_rpt.doc_movimentacao,
            'alteracao': cadastro_rpt.alteracao,
        }
        return JsonResponse(data)

    elif request.method == "POST":
        cadastro_rpt.data_pedido = request.POST.get('data_pedido')
        cadastro_rpt.data_movimentacao = request.POST.get('data_movimentacao') or None
        cadastro_rpt.data_alteracao = request.POST.get('data_alteracao') or None  # Garante que None seja atribuído se vazio
        cadastro_rpt.status = request.POST.get('status')
        cadastro_rpt.sgb_destino = request.POST.get('sgb_destino')
        cadastro_rpt.posto_secao_destino = request.POST.get('posto_secao_destino')
        cadastro_rpt.doc_solicitacao = request.POST.get('doc_solicitacao')
        cadastro_rpt.doc_alteracao = request.POST.get('doc_alteracao')
        cadastro_rpt.doc_movimentacao = request.POST.get('doc_movimentacao')
        cadastro_rpt.alteracao = request.POST.get('alteracao')

        try:
            cadastro_rpt.save()
            return redirect('rpt:ver_rpt', id=cadastro_rpt.id)
        except ValidationError as e:
            logger.error(f'Erro de validação ao salvar Cadastro_rpt: {e}', exc_info=True)
            return JsonResponse({'error': f'Erro de validação: {e}'}, status=400)
        except IntegrityError as e:
            logger.error(f'Erro de integridade ao salvar Cadastro_rpt: {e}', exc_info=True)
            return JsonResponse({'error': f'Erro de integridade: {e}'}, status=400)
        except Exception as e:
            logger.error(f'Erro ao salvar Cadastro_rpt: {e}', exc_info=True)
            return JsonResponse({'error': f'Erro ao salvar: {e}'}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


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



@login_required
def excluir_rpt(request, id):
    """
    View para excluir um registro de Cadastro_rpt após confirmação de senha.
    Requer método POST.
    """
    # Tenta obter o objeto ou retorna 404 se não existir
    cadastro_rpt_obj = get_object_or_404(Cadastro_rpt, id=id)
    # Define a URL de redirecionamento em caso de falha ou GET (pode ser a lista ou a página de detalhes)
    # Supondo que 'rpt:listar_rpt' é a URL da lista de RPTs
    # Supondo que 'rpt:ver_rpt' é a URL de detalhes (se existir)
    redirect_url = 'rpt:listar_rpt'
    # Se existir uma URL de detalhes, use-a como fallback em caso de erro na exclusão
    # Tente obter a URL de detalhes; se não existir, use a lista
    try:
        from django.urls import reverse
        detail_url = reverse('rpt:ver_rpt', args=[id]) # Tenta montar a URL de detalhes
        error_redirect_url = detail_url
    except:
        error_redirect_url = redirect('rpt:listar_rpt') # Fallback para a lista

    if request.method == 'POST':
        try:
            current_user = request.user
            password = request.POST.get('password', '')

            # Verificar senha
            if not password:
                 messages.add_message(request, messages.ERROR, 'Senha não fornecida. Operação cancelada.')
                 return redirect(error_redirect_url) # Redireciona de volta

            if not check_password(password, current_user.password):
                messages.add_message(request, messages.ERROR, 'Senha incorreta! Operação cancelada.')
                return redirect(error_redirect_url) # Redireciona de volta

            # Realizar exclusão
            cadastro_rpt_obj.delete()
            messages.add_message(request, messages.SUCCESS, 'Registro RPT excluído com sucesso.')
            return redirect('rpt:listar_rpt') # Redireciona para a lista após sucesso

        except Exception as e:
            messages.add_message(request, messages.ERROR, f'Erro ao excluir o registro RPT: {str(e)}')
            return redirect(error_redirect_url) # Redireciona de volta em caso de erro

    # Se a requisição não for POST, redirecionar para a lista ou página de detalhes
    messages.warning(request, 'Método inválido para exclusão.')
    return redirect(redirect_url)


@login_required
def buscar_militar_rpt(request):
    """
    Busca um militar pelo RE (via POST) para pré-preencher o formulário de cadastro RPT,
    ou exibe o formulário de busca (via GET).
    """
    # Template para exibir o formulário de busca RE
    buscar_template = 'buscar_rpt.html'
    # Template para exibir o formulário de cadastro RPT (preenchido ou vazio)
    cadastrar_template = 'cadastrar_rpt.html'
     # URL name da própria view (ou da view que exibe o form de cadastro)
    cadastro_rpt_url_name = 'rpt:cadastrar_rpt'

    if request.method == "POST":
        re = request.POST.get('re', '').strip()
        if not re:
             messages.add_message(request, constants.WARNING,'Por favor, informe o RE para buscar.')
             # Renderiza o form de cadastro vazio novamente, ou redireciona
             return render(request, cadastrar_template, {
                 'sgb_choices': Cadastro_rpt._meta.get_field('sgb_destino').choices,
                 'posto_secao_choices': Cadastro_rpt._meta.get_field('posto_secao_destino').choices,
                 'status_choices': Cadastro_rpt._meta.get_field('status').choices,
             })

        try:
            # Busca o cadastro principal
            cadastro = Cadastro.objects.get(re=re)

            # Busca os dados relacionados mais recentes (ou relevantes)
            # Usar select_related/prefetch_related aqui não é comum pois buscamos por RE específico,
            # mas pode ser útil se houver muita lógica acessando relações no template/view.
            # O uso de .first() após order_by('-id') pega o mais recente.
            detalhes = DetalhesSituacao.objects.filter(cadastro=cadastro).order_by('-id').first()
            imagem = Imagem.objects.filter(cadastro=cadastro).order_by('-id').first()
            promocao = Promocao.objects.filter(cadastro=cadastro).order_by('-id').first()

            # Adiciona mensagens informativas se dados relacionados não forem encontrados
            if not detalhes:
                messages.info(request, 'Informação: Detalhes da situação atual não encontrados para este RE.')
            if not promocao:
                 messages.info(request, 'Informação: Dados da última promoção não encontrados para este RE.')
            if not imagem:
                 messages.info(request, 'Informação: Imagem não encontrada para este RE.')


            # Prepara o contexto para renderizar o formulário de cadastro preenchido
            context = {
                'cadastro': cadastro,
                'detalhes': detalhes, # Será None se não encontrado
                'imagem': imagem,     # Será None se não encontrado
                'promocao': promocao,   # Será None se não encontrado
                # Passa as choices para os selects do formulário
                'sgb_choices': Cadastro_rpt._meta.get_field('sgb_destino').choices,
                'posto_secao_choices': Cadastro_rpt._meta.get_field('posto_secao_destino').choices,
                'status_choices': Cadastro_rpt._meta.get_field('status').choices,
                'found_re': re # Indica que a busca foi feita
            }
            # Renderiza o template do formulário de cadastro com os dados encontrados
            return render(request, cadastrar_template, context)

        except Cadastro.DoesNotExist:
            messages.add_message(request, constants.ERROR, f'Cadastro com RE "{re}" não encontrado.')
            # Renderiza o form de cadastro vazio novamente
            return render(request, cadastrar_template, {
                 'sgb_choices': Cadastro_rpt._meta.get_field('sgb_destino').choices,
                 'posto_secao_choices': Cadastro_rpt._meta.get_field('posto_secao_destino').choices,
                 'status_choices': Cadastro_rpt._meta.get_field('status').choices,
                 'searched_re': re # Passa o RE pesquisado de volta
             })
        except Cadastro.MultipleObjectsReturned:
             messages.add_message(request, constants.ERROR, f'Múltiplos cadastros encontrados com RE "{re}". Verifique a base de dados.')
             return render(request, cadastrar_template, {
                 'sgb_choices': Cadastro_rpt._meta.get_field('sgb_destino').choices,
                 'posto_secao_choices': Cadastro_rpt._meta.get_field('posto_secao_destino').choices,
                 'status_choices': Cadastro_rpt._meta.get_field('status').choices,
                 'searched_re': re
             })
        except Exception as e:
             messages.add_message(request, constants.ERROR, f'Ocorreu um erro inesperado ao buscar o militar: {str(e)}')
             # Renderiza o form de cadastro vazio novamente
             return render(request, cadastrar_template, {
                 'sgb_choices': Cadastro_rpt._meta.get_field('sgb_destino').choices,
                 'posto_secao_choices': Cadastro_rpt._meta.get_field('posto_secao_destino').choices,
                 'status_choices': Cadastro_rpt._meta.get_field('status').choices,
                 'searched_re': re
             })

    # Se a requisição for GET, exibe o formulário de busca inicial
    # (ou o formulário de cadastro RPT vazio, dependendo do fluxo desejado)
    # Se 'buscar_rpt.html' é só para digitar o RE e 'cadastrar_rpt.html' é o form principal:
    # return render(request, buscar_template)
    # Se 'cadastrar_rpt.html' contém a busca e o formulário:
    return render(request, cadastrar_template, {
        'sgb_choices': Cadastro_rpt._meta.get_field('sgb_destino').choices,
        'posto_secao_choices': Cadastro_rpt._meta.get_field('posto_secao_destino').choices,
        'status_choices': Cadastro_rpt._meta.get_field('status').choices,
    })


@login_required
def historico_rpt(request, id):
    """
    Exibe o histórico de alterações para um registro Cadastro_rpt específico.
    """
    cadastro_rpt = get_object_or_404(Cadastro_rpt.objects.select_related('cadastro'), id=id)
    # Busca o histórico, otimizando a busca pelo usuário que fez a alteração
    historico_rpt_list = HistoricoRpt.objects.filter(cadastro=cadastro_rpt).select_related('usuario_alteracao__profile').order_by('-data_alteracao') # Mais recente primeiro

    return render(request, 'historico_rpt.html', {
        'cadastro_rpt': cadastro_rpt,
        'historicoRpt': historico_rpt_list, # Nome da variável no contexto
    })


# Permissão: Apenas superusuários ou quem tem permissão específica para adicionar RPT
# Ajuste 'rpt.add_cadastro_rpt' conforme o nome da sua app e modelo
permission_required = user_passes_test(lambda u: u.is_superuser or u.has_perm('rpt.add_cadastro_rpt'))

@login_required
@permission_required
def importar_rpt(request):
    """
    View para importar dados de RPT a partir de um arquivo CSV ou Excel.
    Requer permissão e método POST com um arquivo.
    """
    importar_template = 'importar_rpt.html'
    listar_url_name = 'rpt:listar_rpt'
    importar_url_name = 'rpt:importar_rpt'

    if request.method == 'POST':
        arquivo = request.FILES.get('arquivo')

        # --- Validações Iniciais ---
        if not arquivo:
            messages.error(request, 'Nenhum arquivo selecionado para importação.')
            return redirect(importar_url_name)

        try:
            extensao = arquivo.name.split('.')[-1].lower()
        except IndexError:
             messages.error(request, 'Nome de arquivo inválido ou sem extensão.')
             return redirect(importar_url_name)


        if arquivo.size > 10 * 1024 * 1024: # Aumentado limite para 10MB
            messages.error(request, 'Arquivo excede o limite de tamanho (máximo 10MB).')
            return redirect(importar_url_name)

        # --- Leitura do Arquivo ---
        try:
            df = None
            if extensao == 'csv':
                # Tenta ler com UTF-8, depois Latin-1 como fallback comum no Brasil
                try:
                    # keep_default_na=False e na_filter=False evitam que 'NA' seja lido como NaN automaticamente
                    df = pd.read_csv(arquivo, sep=';', encoding='utf-8-sig', dtype=str, keep_default_na=False, na_filter=False)
                except UnicodeDecodeError:
                    arquivo.seek(0) # Volta ao início do arquivo
                    df = pd.read_csv(arquivo, sep=';', encoding='latin-1', dtype=str, keep_default_na=False, na_filter=False)
            elif extensao in ['xls', 'xlsx']:
                df = pd.read_excel(arquivo, dtype=str, keep_default_na=False, na_values=[]) # na_values=[] similar a keep_default_na=False
            else:
                messages.error(request, f'Formato de arquivo "{extensao}" não suportado. Use CSV (separado por ponto e vírgula) ou Excel (XLS, XLSX).')
                return redirect(importar_url_name)

        except Exception as e:
            messages.error(request, f'Erro ao ler o arquivo: {e}. Verifique se o arquivo está no formato correto, não corrompido, e se a codificação/separador (para CSV) estão corretos.')
            return redirect(importar_url_name)

        # --- Validação de Colunas ---
        colunas_obrigatorias = {'cadastro_re', 'data_pedido', 'status', 'sgb_destino', 'posto_secao_destino', 'doc_solicitacao'}
        colunas_arquivo = set(df.columns)

        if not colunas_obrigatorias.issubset(colunas_arquivo):
            missing = colunas_obrigatorias - colunas_arquivo
            messages.error(request, f'Colunas obrigatórias faltando no arquivo: {", ".join(sorted(list(missing)))}')
            return redirect(importar_url_name)

        # --- Função Auxiliar para Conversão de Datas ---
        def converter_data(valor_str, field_name):
            valor_str = str(valor_str).strip()
            # Considera várias formas de vazio/NA
            if not valor_str or valor_str.lower() in ['na', 'n/a', 'nan', 'none', '', '#n/d']:
                return None

            # Tenta converter de número serial do Excel
            try:
                if valor_str.replace('.', '', 1).isdigit():
                    excel_date_num = float(valor_str)
                    # Evita converter números muito grandes ou pequenos que não são datas
                    if 1 < excel_date_num < 300000:
                         # Base do Excel para Windows (1900) - Dia 0 é 30/12/1899
                         base_date = datetime(1899, 12, 30)
                         delta = timedelta(days=excel_date_num)
                         return (base_date + delta).date()
            except ValueError:
                pass # Não era um número simples

            # Tenta formatos de data comuns (Adicione mais se necessário)
            formatos_data = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d', '%d/%m/%y', '%d.%m.%Y', '%d.%m.%y']
            for fmt in formatos_data:
                try:
                    return datetime.strptime(valor_str, fmt).date()
                except ValueError:
                    continue

            # Se nenhum formato funcionou
            raise ValueError(f'Formato de data inválido ou não reconhecido ("{valor_str}") para o campo "{field_name}"')

        # --- Processamento das Linhas ---
        registros_processados = 0
        erros_processamento = []
        User = get_user_model() # Modelo de usuário ativo

        for index, row in df.iterrows():
            linha_num = index + 2 # Linha no arquivo (1-based + cabeçalho)
            try:
                # Ignora linhas completamente vazias (considerando várias formas de NA)
                if row.isnull().all() or all(str(v).strip().lower() in ['', 'na', 'n/a', 'nan', 'none', '#n/d'] for v in row.values):
                    continue

                # --- Validação e Limpeza dos Dados da Linha ---
                cadastro_re = str(row.get('cadastro_re', '')).strip()
                if not cadastro_re: raise ValueError('Coluna "cadastro_re" não pode estar vazia.')

                # Busca o Cadastro associado
                try:
                    # select_related(None) força a não buscar relações automaticamente aqui
                    cadastro_obj = Cadastro.objects.select_related(None).get(re=cadastro_re)
                except Cadastro.DoesNotExist:
                    raise ValueError(f'Cadastro com RE "{cadastro_re}" não encontrado no sistema.')
                except Cadastro.MultipleObjectsReturned:
                    raise ValueError(f'Múltiplos cadastros encontrados com RE "{cadastro_re}". Corrija a base de dados.')

                # Campos obrigatórios
                data_pedido = converter_data(row.get('data_pedido'), 'data_pedido')
                if not data_pedido: raise ValueError('Coluna "data_pedido" inválida ou vazia.')

                status = str(row.get('status', '')).strip()
                if not status: raise ValueError('Coluna "status" não pode estar vazia.')
                # Opcional: Validar contra choices do modelo
                status_choices = [choice[0] for choice in Cadastro_rpt._meta.get_field('status').choices]
                if status not in status_choices: raise ValueError(f'Valor "{status}" inválido para o campo "status". Válidos: {", ".join(status_choices)}')

                sgb_destino = str(row.get('sgb_destino', '')).strip()
                if not sgb_destino: raise ValueError('Coluna "sgb_destino" não pode estar vazia.')
                # Opcional: Validar SGB

                posto_secao_destino = str(row.get('posto_secao_destino', '')).strip()
                if not posto_secao_destino: raise ValueError('Coluna "posto_secao_destino" não pode estar vazia.')
                # Opcional: Validar Posto/Seção

                doc_solicitacao = str(row.get('doc_solicitacao', '')).strip()
                if not doc_solicitacao: raise ValueError('Coluna "doc_solicitacao" não pode estar vazia.')

                # Campos opcionais
                data_movimentacao = converter_data(row.get('data_movimentacao'), 'data_movimentacao') # Permite None
                data_alteracao = converter_data(row.get('data_alteracao'), 'data_alteracao') # Permite None

                # Trata campos de texto opcionais, convertendo vazios/NA para None (se modelo permitir null=True)
                def clean_optional_text(value):
                    val = str(value).strip()
                    return val if val and val.lower() not in ['na', 'n/a', 'nan', 'none', '#n/d'] else None

                doc_alteracao = clean_optional_text(row.get('doc_alteracao'))
                doc_movimentacao = clean_optional_text(row.get('doc_movimentacao'))
                alteracao = clean_optional_text(row.get('alteracao'))

                # --- Criação do Objeto RPT ---
                # Opcional: Verificar duplicidade antes de criar
                if Cadastro_rpt.objects.filter(
                        cadastro=cadastro_obj, data_pedido=data_pedido, sgb_destino=sgb_destino,
                        posto_secao_destino=posto_secao_destino, doc_solicitacao=doc_solicitacao
                    ).exists():
                    raise ValueError("Solicitação RPT duplicada já existe no sistema.")


                Cadastro_rpt.objects.create(
                    cadastro=cadastro_obj,
                    data_pedido=data_pedido,
                    status=status,
                    sgb_destino=sgb_destino,
                    posto_secao_destino=posto_secao_destino,
                    doc_solicitacao=doc_solicitacao,
                    data_movimentacao=data_movimentacao, # Passa None se for o caso
                    data_alteracao=data_alteracao,      # Passa None se for o caso
                    doc_alteracao=doc_alteracao,        # Passa None se for o caso
                    doc_movimentacao=doc_movimentacao,  # Passa None se for o caso
                    create=datetime.now(),                # Passa None se for o caso
                    usuario_alteracao=request.user      # Usuário que realizou a importação
                )
                registros_processados += 1

            except Exception as e:
                erros_processamento.append(f"Linha {linha_num}: {str(e)}")
                # Continua para a próxima linha mesmo se houver erro nesta
                continue

        # --- Feedback Final da Importação ---
        if registros_processados > 0:
            messages.success(request, f'✅ {registros_processados} registro(s) RPT importado(s) com sucesso!')

        if erros_processamento:
            total_erros = len(erros_processamento)
            erros_preview = "; ".join(erros_processamento[:5]) # Mostra os 5 primeiros erros
            erros_msg = f'⚠️ {total_erros} erro(s) ocorreram durante a importação. '
            if total_erros <= 5:
                erros_msg += f'Erros: {erros_preview}'
            else:
                erros_msg += f'Primeiros {5} erros: {erros_preview} (...e mais {total_erros - 5})'
            # Considerar logar todos os erros para análise posterior
            messages.warning(request, erros_msg)
            # Talvez oferecer download do log de erros?

        return redirect(listar_url_name) # Redireciona para a lista após o processo

    # Se GET, renderiza o formulário de importação
    return render(request, importar_template)


from django.http import HttpResponse
from django.contrib import messages
from django.shortcuts import redirect
from .export_utils import export_rpt_data

def exportar_rpt(request):
    try:
        # Coletar parâmetros COM VALOR PADRÃO PARA STATUS
        export_format = request.GET.get('format', 'xlsx').lower()
        posto_secao = request.GET.get('posto_secao_destino')

        # APLICAR FILTROS OBRIGATÓRIOS
        filters = {
            'status': 'Aguardando'  # Garante que o status seja sempre "Aguardando"
        }
        if posto_secao:
            filters['posto_secao_destino'] = posto_secao

        # Gerar e retornar a resposta diretamente
        response = export_rpt_data(request, export_format, **filters)
        return response

    except ValueError as e:
        messages.error(request, f'Erro na exportação: {str(e)}')
        return redirect('rpt:listar_rpt')
    except Exception as e:
        messages.error(request, f'Erro na exportação: {str(e)}')
        return redirect('rpt:listar_rpt')
