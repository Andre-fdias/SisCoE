from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.messages import constants
from backend.efetivo.models import Cadastro, DetalhesSituacao, Promocao, Imagem  # Ajuste a importação conforme necessário
from .models import Cadastro_rpt, HistoricoRpt
from django.db.models import Prefetch
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import datetime, timedelta
from .models import Cadastro_rpt
from backend.efetivo.models import Cadastro  # Importe o modelo Cadastro
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from .export_utils import export_rpt_data
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

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

   
      # Lista de inscritos com a mesma ordenação
    inscritos_secao = Cadastro_rpt.objects.filter(
        posto_secao_destino=cadastro_rpt.posto_secao_destino
    ).annotate(
        posicao=Window(
            expression=RowNumber(),
            partition_by=[F('posto_secao_destino')],
            order_by=[F('data_pedido').asc(), F('id').asc()]
        )
    ).order_by('posicao')  # Ordenar pela posição calculada
    posicao_real = None
    for idx, inscrito in enumerate(inscritos_secao, start=1):
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

    status_choices = Cadastro_rpt._meta.get_field('status').choices
    posto_secao_choices = Cadastro_rpt._meta.get_field('posto_secao_destino').choices
    sgb_choices = Cadastro_rpt._meta.get_field('sgb_destino').choices
    alteracao_choices = Cadastro_rpt._meta.get_field('alteracao').choices

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

        try:
            cadastro_rpt.save()
            return redirect('rpt:ver_rpt', id=cadastro_rpt.id)
        except Exception as e:
            logger.error(f'Erro ao salvar Cadastro_rpt: {e}', exc_info=True)
            # Você pode adicionar uma mensagem de erro para o usuário aqui
            # messages.error(request, 'Ocorreu um erro ao salvar o registro.')
            return redirect('rpt:listar_rpt')  # Redireciona para a lista em caso de erro

    context = {
        'cadastro_rpt': cadastro_rpt,
        'status_choices': status_choices,
        'posto_secao_choices': posto_secao_choices,
        'sgb_choices': sgb_choices,
        'alteracao_choices': alteracao_choices,
    }
    return render(request, 'editar_rpt.html', context)

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


@login_required
@user_passes_test(lambda u: u.is_superuser)
def importar_rpt(request):
    if request.method == 'POST' and request.FILES.get('arquivo'):
        arquivo = request.FILES['arquivo']
        extensao = arquivo.name.split('.')[-1].lower()

        try:
            if arquivo.size > 5 * 1024 * 1024:
                messages.error(request, 'Arquivo muito grande (máximo 5MB).', extra_tags='bg-red-500 text-white p-4 rounded')
                return redirect('rpt:importar_rpt')

            try:
                if extensao == 'csv':
                    df = pd.read_csv(arquivo, sep=';', encoding='utf-8-sig', dtype=str, keep_default_na=False, na_filter=False)
                elif extensao in ['xls', 'xlsx']:
                    df = pd.read_excel(arquivo, dtype=str, keep_default_na=False, na_values=[])
                else:
                    messages.error(request, 'Formato inválido (use CSV ou Excel).', extra_tags='bg-red-500 text-white p-4 rounded')
                    return redirect('rpt:importar_rpt')
            except Exception as e:
                messages.error(request, f'Erro ao ler arquivo: {e}', extra_tags='bg-red-500 text-white p-4 rounded')
                return redirect('rpt:importar_rpt')

            colunas_obrigatorias = {'cadastro_re', 'data_pedido', 'status', 'sgb_destino', 'posto_secao_destino', 'doc_solicitacao'}

            if missing := colunas_obrigatorias - set(df.columns):
                messages.error(request, f'Colunas faltando: {", ".join(missing)}', extra_tags='bg-red-500 text-white p-4 rounded')
                return redirect('rpt:importar_rpt')

            erros_pre_validacao = []
            for index, row in df.iterrows():
                try:
                    if all(str(v).strip() in ['', 'nan', 'N/A'] for v in row):
                        continue
                    for campo in colunas_obrigatorias:
                        valor = str(row.get(campo, '')).strip()
                        if valor in ['', 'nan', 'N/A']:
                            raise ValueError(f'Campo "{campo}" está vazio ou é inválido')
                except Exception as e:
                    erros_pre_validacao.append(f"Linha {index + 2}: {str(e)}")

            if erros_pre_validacao:
                erros_msg = f'Erros críticos: {", ".join(erros_pre_validacao[:3])}... (total: {len(erros_pre_validacao)})'
                messages.error(request, erros_msg, extra_tags='bg-red-500 text-white p-4 rounded')
                return redirect('rpt:importar_rpt')

            campos_nao_obrigatorios = list(set(df.columns) - colunas_obrigatorias)
            df[campos_nao_obrigatorios] = df[campos_nao_obrigatorios].replace(['', None, 'nan'], 'N/A')

            registros_processados = 0
            erros_processamento = []

            def converter_data(valor, field_name):
                valor = str(valor).strip()
                if valor == 'N/A':
                    return None

                if valor.replace('.', '').isdigit():
                    try:
                        return (datetime(1899, 12, 30) + timedelta(days=float(valor))).date()
                    except:
                        pass

                formatos = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d']
                for fmt in formatos:
                    try:
                        return datetime.strptime(valor, fmt).date()
                    except:
                        continue
                raise ValueError(f'Formato de data inválido: "{valor}"')

            for index, row in df.iterrows():
                try:
                    if all(str(v) == 'N/A' for v in row):
                        continue

                    try:
                        cadastro = Cadastro.objects.get(re=row['cadastro_re'].strip())
                    except Cadastro.DoesNotExist:
                        raise ValueError(f'Cadastro com RE {row["cadastro_re"]} não encontrado')

                    data_pedido = converter_data(row['data_pedido'], 'data_pedido')

                    Cadastro_rpt.objects.create(
                        cadastro=cadastro,
                        data_pedido=data_pedido,
                        status=row['status'].strip(),
                        sgb_destino=row['sgb_destino'].strip(),
                        posto_secao_destino=row['posto_secao_destino'].strip(),
                        doc_solicitacao=row['doc_solicitacao'].strip(),
                        data_movimentacao=converter_data(row.get('data_movimentacao', 'N/A'), 'data_movimentacao'),
                        data_alteracao=converter_data(row.get('data_alteracao', 'N/A'), 'data_alteracao'),
                        doc_alteracao=row.get('doc_alteracao', 'N/A').strip(),
                        doc_movimentacao=row.get('doc_movimentacao', 'N/A').strip(),
                        alteracao=row.get('alteracao', 'N/A').strip(),
                        usuario_alteracao=request.user
                    )
                    registros_processados += 1

                except Exception as e:
                    erros_processamento.append(f"Linha {index + 2}: {str(e)}")
                    continue

            if registros_processados > 0:
                msg = f'✅ {registros_processados} registros importados com sucesso!'
                messages.success(request, msg, extra_tags='bg-green-500 text-white p-4 rounded')

            if erros_processamento:
                erros_msg = f'⚠️ {len(erros_processamento)} erro(s): ' + ', '.join(erros_processamento[:3])
                if len(erros_processamento) > 3:
                    erros_msg += f' (...mais {len(erros_processamento)-3})'
                messages.warning(request, erros_msg, extra_tags='bg-yellow-500 text-white p-4 rounded')

            return redirect('rpt:listar_rpt')

        except Exception as e:
            messages.error(request, f'❌ Falha na importação: {str(e)}', extra_tags='bg-red-500 text-white p-4 rounded')
            return redirect('rpt:importar_rpt')

    return render(request, 'importar_rpt.html')

def exportar_rpt(request):
    if request.method == 'POST':
        format_type = request.POST.get('export_format')
        if not format_type:
            return HttpResponseBadRequest("Formato de exportação não especificado")

        queryset = Cadastro_rpt.objects.all().values(
            'cadastro__re', 'cadastro__nome_de_guerra', 'data_pedido', 'status',
            'sgb_destino', 'posto_secao_destino', 'doc_solicitacao',
            'data_movimentacao', 'data_alteracao', 'doc_alteracao', 'doc_movimentacao',
            'alteracao'
        )
        df = pd.DataFrame(list(queryset))
        df.columns = [
            'RE', 'Nome de Guerra', 'Data Pedido', 'Status', 'SGB Destino',
            'Posto/Seção Destino', 'Doc. Solicitação', 'Data Movimentação',
            'Data Alteração', 'Doc. Alteração', 'Doc. Movimentação', 'Alteração'
        ]

        if format_type == 'xlsx':
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="rpt_data.xlsx"'
            df.to_excel(response, index=False)
            return response

        elif format_type == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="rpt_data.csv"'
            df.to_csv(response, index=False, sep=';', encoding='utf-8-sig')
            return response

        elif format_type == 'pdf':
            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesizes=letter)
            p.drawString(100, 750, "Dados RPT")
            y = 700
            for index, row in df.iterrows():
                row_str = ", ".join(map(str, row.values))
                p.drawString(100, y, row_str)
                y -= 20
            p.save()
            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="rpt_data.pdf"'
            return response

    return HttpResponseBadRequest("Método não permitido")