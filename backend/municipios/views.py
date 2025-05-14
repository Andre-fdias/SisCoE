from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from .models import Posto, Contato, Pessoal,Cidade
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from .models import Posto
from django.contrib.auth.decorators import login_required

@login_required
def posto_list(request):
    postos = Posto.objects.all().prefetch_related('pessoal', 'cidades')
    cidades = Cidade.objects.all().select_related('posto')
    
    # Obter as choices diretamente do modelo
    municipio_choices = Cidade._meta.get_field('municipio').choices
    
    return render(request, 'posto_list.html', {
        'postos': postos,
        'cidades': cidades,
        'municipio_choices': municipio_choices  # Adicionar ao contexto principal
    })



from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.db.models import Subquery, OuterRef, Count
from .models import Posto, Pessoal
from backend.efetivo.models import DetalhesSituacao, Promocao

@login_required
def posto_detail(request, pk):
    posto = get_object_or_404(Posto, pk=pk)

    # Definimos os grupos exatamente como estão no modelo
    GRUPOS = {
        'Tc': 'Ten Cel',
        'Maj': 'Maj',
        'Cap': 'Cap',
        'Ten': 'Ten QO',
        'Ten QAOPM': 'Ten QA',
        'St/Sgt': 'St/Sgt',
        'Cb/Sd': 'Cb/Sd'
    }

    # Primeiro: Obter todos os cadastros com situação "Efetivo" no posto
    efetivos = DetalhesSituacao.objects.filter(
        situacao='Efetivo',
        posto_secao=posto.posto_secao
    ).select_related('cadastro')

    # Segundo: Para cada efetivo, pegar sua última promoção
    contagem = {grupo: 0 for grupo in GRUPOS.keys()}
    
    for efetivo in efetivos:
        ultima_promocao = Promocao.objects.filter(
            cadastro=efetivo.cadastro
        ).order_by('-ultima_promocao').first()
        
        if ultima_promocao and ultima_promocao.grupo.strip() in GRUPOS:
            grupo = ultima_promocao.grupo.strip()
            contagem[grupo] += 1

    # Preparamos os dados para o template
    efetivo_grupos = {
        'Tc': contagem.get('Tc', 0),
        'Maj': contagem.get('Maj', 0),
        'Cap': contagem.get('Cap', 0),
        'Ten': contagem.get('Ten', 0),
        'Ten_QAOPM': contagem.get('Ten QAOPM', 0),  # Usamos underscore para o template
        'St_Sgt': contagem.get('St/Sgt', 0),       # Usamos underscore para o template
        'Cb_Sd': contagem.get('Cb/Sd', 0)         # Usamos underscore para o template
    }

    # Calcula o total
    total_efetivo = sum(contagem.values())

    try:
        pessoal = Pessoal.objects.get(posto=posto)
    except Pessoal.DoesNotExist:
        pessoal = None

    context = {
        'posto': posto,
        'efetivo_grupos': efetivo_grupos,
        'total_efetivo': total_efetivo,
        'pessoal': pessoal,
    }

    return render(request, 'posto_detail.html', context)

    
@login_required
def municipio_detail(request, pk):
    cidade = get_object_or_404(Cidade, pk=pk)
    posto = cidade.posto  # Obtenha o posto relacionado à cidade
    return render(request, 'municipio_detail.html', {'cidade': cidade, 'posto': posto})

@login_required
def posto_secao_detail(request, pk):
    posto = get_object_or_404(Posto, pk=pk)
    return render(request, 'posto_secao_detail.html', {'posto': posto})


@login_required
def posto_create(request):
    sgb_choices = Posto.sgb_choices
    posto_secao_choices = Posto.posto_secao_choices
    posto_atendimento_choices = Posto.posto_atendimento_choices
    cidade_posto_choices = Posto.cidade_posto_choices
    municipio_choices = Cidade.municipio_choices
    tipo_choices = Posto.tipo_choices
    op_adm_choices = Posto.op_adm_choices

    if request.method == 'POST':
        # Dados do Posto
        posto_data = {
            'sgb': request.POST.get('sgb'),
            'posto_secao': request.POST.get('posto_secao'),
            'posto_atendimento': request.POST.get('posto_atendimento'),
            'cidade_posto': request.POST.get('cidade_posto'),
            'tipo_cidade': request.POST.get('tipo_cidade'),
            'op_adm': request.POST.get('op_adm'),
            'usuario': request.user,
        }
        
        # Processa a imagem do quartel
        if 'quartel' in request.FILES:
            posto_data['quartel'] = request.FILES['quartel']
        
        # Cria o Posto
        posto = Posto.objects.create(**posto_data)

        # Dados do Contato
        contato_data = {
            'posto': posto,
            'telefone': request.POST.get('telefone'),
            'rua': request.POST.get('rua'),
            'numero': request.POST.get('numero'),
            'complemento': request.POST.get('complemento'),
            'bairro': request.POST.get('bairro'),
            'cidade': request.POST.get('cidade'),
            'cep': request.POST.get('cep'),
            'email': request.POST.get('email_funcional'),
            'latitude': request.POST.get('latitude_contato'),
            'longitude': request.POST.get('longitude_contato'),
        }
        Contato.objects.create(**contato_data)

        # Dados do Pessoal
        pessoal_data = {
            'posto': posto,
            'cel': int(request.POST.get('cel', 0)),
            'ten_cel': int(request.POST.get('ten_cel', 0)),
            'maj': int(request.POST.get('maj', 0)),
            'cap': int(request.POST.get('cap', 0)),
            'tenqo': int(request.POST.get('ten', 0)),
            'tenqa': int(request.POST.get('tenqa', 0)),
            'asp': int(request.POST.get('asp', 0)),
            'st_sgt': int(request.POST.get('st_sgt', 0)),
            'cb_sd': int(request.POST.get('cb_sd', 0)),
        }
        Pessoal.objects.create(**pessoal_data)

        # Dados das Cidades (múltiplas entradas)
        municipios = request.POST.getlist('municipios[]')
        latitudes = request.POST.getlist('latitudes[]')
        longitudes = request.POST.getlist('longitudes[]')
        bandeiras = request.FILES.getlist('bandeiras[]')
        descricoes = request.POST.getlist('descricoes[]')
       
        for i in range(len(municipios)):
            cidade_data = {
                'posto': posto,
                'municipio': municipios[i],
                'descricao': descricoes[i],
                'latitude': latitudes[i],
                'longitude': longitudes[i],
            }
            
            if i < len(bandeiras) and bandeiras[i]:
                cidade_data['bandeira'] = bandeiras[i]
            
            Cidade.objects.create(**cidade_data)

        return redirect('municipios:posto_list')

    return render(request, 'posto_form.html', {
        'sgb_choices': sgb_choices,
        'posto_secao_choices': posto_secao_choices,
        'posto_atendimento_choices': posto_atendimento_choices,
        'cidade_posto_choices': cidade_posto_choices,
        'municipio_choices': municipio_choices,
        'tipo_choices': tipo_choices,
        'op_adm_choices': op_adm_choices
    })



from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Posto, Contato, Pessoal, Cidade

@login_required
def posto_update(request, pk):
    posto = get_object_or_404(Posto, pk=pk)
    contato = get_object_or_404(Contato, posto=posto)
    
    # Verifica se é uma requisição AJAX para atualizar cidade
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        cidade_id = request.POST.get('cidade_id')
        
        if cidade_id:
            try:
                cidade = get_object_or_404(Cidade, id=cidade_id, posto=posto)
                
                # Atualiza os dados da cidade
                cidade.municipio = request.POST.get('municipio', cidade.municipio)
                
                # Valida e converte coordenadas
                try:
                    cidade.latitude = float(request.POST.get('latitude', cidade.latitude))
                    cidade.longitude = float(request.POST.get('longitude', cidade.longitude))
                except (TypeError, ValueError):
                    return JsonResponse({
                        'success': False,
                        'message': 'Coordenadas inválidas. Use números decimais.'
                    })
                
                cidade.descricao = request.POST.get('descricao', cidade.descricao)
                
                # Trata o upload da bandeira
                if 'bandeira' in request.FILES:
                    # Remove a imagem antiga se existir
                    if cidade.bandeira:
                        cidade.bandeira.delete(save=False)
                    cidade.bandeira = request.FILES['bandeira']
                elif request.POST.get('bandeira-clear') == 'on':
                    if cidade.bandeira:
                        cidade.bandeira.delete(save=False)
                    cidade.bandeira = None
                
                cidade.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Município atualizado com sucesso!',
                    'data': {
                        'municipio': cidade.municipio,
                        'latitude': cidade.latitude,
                        'longitude': cidade.longitude,
                        'bandeira_url': cidade.bandeira.url if cidade.bandeira else ''
                    }
                })
            
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Erro ao atualizar município: {str(e)}'
                })
    
    # Processamento normal do POST (não-AJAX)
    elif request.method == 'POST':
        # Atualizando os dados do Posto
        posto.sgb = request.POST.get('sgb', posto.sgb)
        posto.posto_secao = request.POST.get('posto_secao', posto.posto_secao)
        posto.posto_atendimento = request.POST.get('posto_atendimento', posto.posto_atendimento)
        posto.cidade_posto = request.POST.get('cidade_posto', posto.cidade_posto)
        posto.tipo_cidade = request.POST.get('tipo_cidade', posto.tipo_cidade)
        posto.op_adm = request.POST.get('op_adm', posto.op_adm)

        if 'quartel' in request.FILES:
            # Remove a imagem antiga se existir
            if posto.quartel:
                posto.quartel.delete(save=False)
            posto.quartel = request.FILES['quartel']

        posto.save()

        # Atualizando Contato
        contato.telefone = request.POST.get('telefone', contato.telefone)
        contato.rua = request.POST.get('rua', contato.rua)
        contato.numero = request.POST.get('numero', contato.numero)
        contato.complemento = request.POST.get('complemento', contato.complemento)
        contato.bairro = request.POST.get('bairro', contato.bairro)
        contato.cidade = request.POST.get('cidade', contato.cidade)
        contato.cep = request.POST.get('cep', contato.cep)
        contato.email = request.POST.get('email', contato.email)

        # Validação das coordenadas
        try:
            contato.latitude = float(request.POST.get('latitude', contato.latitude or 0))
            contato.longitude = float(request.POST.get('longitude', contato.longitude or 0))
        except ValueError:
            # Pode adicionar uma mensagem de erro se necessário
            pass

        contato.save()

        # Redireciona para a página de detalhes do posto
        return redirect('municipios:posto_detail', pk=posto.pk)

    # Se for GET e AJAX (para pré-carregar dados no modal)
    elif request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        cidade_id = request.GET.get('cidade_id')
        if cidade_id:
            cidade = get_object_or_404(Cidade, id=cidade_id, posto=posto)
            return JsonResponse({
                'municipio': cidade.municipio,
                'latitude': cidade.latitude,
                'longitude': cidade.longitude,
                'descricao': cidade.descricao,
                'bandeira_url': cidade.bandeira.url if cidade.bandeira else ''
            })

    # Contexto para renderização normal (não-AJAX)
    context = {
        'posto': posto,
        'contato': contato,
        'sgb_choices': Posto._meta.get_field('sgb').choices,
        'posto_secao_choices': Posto._meta.get_field('posto_secao').choices,
        'posto_atendimento_choices': Posto._meta.get_field('posto_atendimento').choices,
        'cidade_posto_choices': Posto._meta.get_field('cidade_posto').choices,
        'tipo_choices': Posto._meta.get_field('op_adm').choices,
        'op_adm_choices': Posto._meta.get_field('tipo_cidade').choices,
    }

    return render(request, 'posto_detail.html', context)


# views.py do app municipio
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required

@login_required
def excluir_municipio(request, id):
    if request.method == 'POST':
        try:
            cadastro = get_object_or_404(Posto, id=id)
            current_user = request.user
            password = request.POST.get('password', '')

            if not check_password(password, current_user.password):
                return JsonResponse({'success': False, 'message': 'Senha incorreta! Operação cancelada.'})

            cadastro.delete()
            return JsonResponse({'success': True, 'message': 'Município excluído com sucesso.'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erro ao excluir: {str(e)}'})

    return JsonResponse({'success': False, 'message': 'Método inválido.'})


from django.shortcuts import render
from .models import Cidade

def calcular_rota(request):
    cidades = Cidade.objects.all().select_related('posto')
    return render(request, 'calcular_rota.html', {'cidades': cidades})


    from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Pessoal, Posto

@login_required
def editar_pessoal(request, pk):
    """
    View para editar os dados de pessoal de um posto específico.
    """
    posto = get_object_or_404(Posto, pk=pk)
    pessoal = get_object_or_404(Pessoal, posto=posto)

    if request.method == 'POST':
        pessoal.cel = request.POST.get('cel', 0)
        pessoal.ten_cel = request.POST.get('ten_cel', 0)
        pessoal.maj = request.POST.get('maj', 0)
        pessoal.cap = request.POST.get('cap', 0)
        pessoal.tenqo = request.POST.get('tenqo', 0)
        pessoal.tenqa = request.POST.get('tenqa', 0)
        pessoal.asp = request.POST.get('asp', 0)
        pessoal.st_sgt = request.POST.get('st_sgt', 0)
        pessoal.cb_sd = request.POST.get('cb_sd', 0)
        pessoal.save()
        # Redirecione para a página de detalhes do posto ou outra página desejada
        return redirect('municipios:posto_detail', pk=posto.pk)
    else:
        # Se a requisição não for POST, você pode renderizar um formulário
        # preenchido com os dados do pessoal (se necessário em outro cenário)
        # No seu caso, o modal já está preenchido via template.
        return render(request, 'posto_detail.html', {'posto': posto, 'pessoal': pessoal})


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Posto, Contato

@login_required
def editar_contato(request, pk):
    """
    View para editar os dados de contato de um posto específico.
    """
    posto = get_object_or_404(Posto, pk=pk)
    contato = get_object_or_404(Contato, posto=posto)

    if request.method == 'POST':
        contato.telefone = request.POST.get('telefone', '')
        contato.rua = request.POST.get('rua', '')
        contato.numero = request.POST.get('numero', '')
        contato.complemento = request.POST.get('complemento', '')
        contato.bairro = request.POST.get('bairro', '')
        contato.cidade = request.POST.get('cidade', '')
        contato.cep = request.POST.get('cep', '')
        contato.email = request.POST.get('email', '')

        latitude_str = request.POST.get('latitude', None)
        longitude_str = request.POST.get('longitude', None)

        try:
            if latitude_str:
                contato.latitude = float(latitude_str.replace(',', '.'))
            else:
                contato.latitude = None
        except ValueError:
            # Handle the case where latitude cannot be converted to a float
            # You might want to add an error message to the user
            pass  # Or add error handling

        try:
            if longitude_str:
                contato.longitude = float(longitude_str.replace(',', '.'))
            else:
                contato.longitude = None
        except ValueError:
            # Handle the case where longitude cannot be converted to a float
            # You might want to add an error message to the user
            pass  # Or add error handling

        contato.save()
        # Redirecione para a página de detalhes do posto
        return redirect('municipios:posto_detail', pk=posto.pk)
    else:
        # Se a requisição não for POST, renderize a página de detalhes do posto
        # O modal já está preenchido via template.
        return render(request, 'posto_detail.html', {'posto': posto, 'contato': contato})



from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.http import HttpResponse

def posto_print(request, pk):
    # Obtém o objeto posto ou retorna 404 se não existir
    posto = get_object_or_404(Posto, pk=pk)
    
    # Renderiza um template específico para impressão
    return render(request, 'posto_print.html', {
        'posto': posto,
    })



from django.http import JsonResponse
from django.views.decorators.http import require_POST
from geopy.distance import geodesic
import json
from .models import Cidade
from django.shortcuts import render

@require_POST
def calcular_rota(request):
    try:
        data = json.loads(request.body)
        origem_nome = data.get('origem')
        destino_nome = data.get('destino')
        origem_lat = data.get('origem_lat')
        origem_lng = data.get('origem_lng')
        destino_lat = data.get('destino_lat')
        destino_lng = data.get('destino_lng')

        if not origem_nome or not destino_nome:
            return JsonResponse({
                'success': False,
                'error': 'Origem e destino são obrigatórios'
            }, status=400)

        if not origem_lat or not origem_lng or not destino_lat or not destino_lng:
             return JsonResponse({
                'success': False,
                'error': 'Latitudes e Longitudes são obrigatórias'
            }, status=400)


        # Cálculo da distância usando geopy
        distancia = geodesic(
            (origem_lat, origem_lng),
            (destino_lat, destino_lng)
        ).km

        # Cálculo do tempo estimado (70km/h)
        tempo = round((distancia / 70) * 60)  # Em minutos

        return JsonResponse({
            'success': True,
            'distancia': round(distancia, 1),
            'tempo': tempo,
            'origem': origem_nome,
            'destino': destino_nome,
            'origem_lat': origem_lat,
            'origem_lng': origem_lng,
            'destino_lat': destino_lat,
            'destino_lng': destino_lng
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def modal_rota(request):
    """
    View para renderizar o modal de cálculo de rota
    """
    # Obter todas as cidades do banco de dados com suas coordenadas
    cidades_db = Cidade.objects.all()
    
    # Preparar as choices com os dados necessários (valor, label, lat, lng)
    cidades_choices = []
    for cidade in cidades_db:
        cidades_choices.append((
            cidade.municipio,  # valor
            cidade.get_nome_municipio(),  # label
            cidade.latitude,  # lat
            cidade.longitude  # lng
        ))
    
    # Adicionar também as choices do modelo (para garantir todas as opções)
    municipio_choices = Cidade.municipio_choices
    for choice in municipio_choices:
        if choice[0] and not any(c[0] == choice[0] for c in cidades_choices):
            # Se não estiver no banco de dados, adicionar com coordenadas padrão
            cidades_choices.append((
                choice[0],  # valor
                choice[1],  # label
                -23.5505,  # lat padrão (São Paulo)
                -46.6333   # lng padrão (São Paulo)
            ))
    
    return render(request, 'modals/modal_rota.html', {'cidades': cidades_choices})



from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from .import_utils import importar_dados  # Importe a função de importação
from django.urls import reverse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import pandas as pd

@login_required
@permission_required('municipios.add_posto')  # Ajuste a permissão conforme necessário
def importar_municipios(request):
    """
    View para importar dados de municípios a partir de um arquivo CSV ou Excel.
    """
    template_name = 'importar_municipios.html'
    redirect_url = 'municipios:posto_list'  # Use o nome correto da sua URL

    if request.method == 'POST':
        arquivo = request.FILES.get('arquivo')

        # Validações iniciais
        if not arquivo:
            messages.error(request, 'Nenhum arquivo selecionado para importação.', extra_tags='bg-red-500 text-white p-4 rounded')
            return redirect(reverse(redirect_url))

        extensao = arquivo.name.split('.')[-1].lower()
        if extensao not in ['csv', 'xls', 'xlsx']:
            messages.error(request, f'Formato de arquivo "{extensao}" não suportado. Use CSV ou Excel.', extra_tags='bg-red-500 text-white p-4 rounded')
            return redirect(reverse(redirect_url))

        if arquivo.size > 10 * 1024 * 1024:  # Limite de 10MB
            messages.error(request, 'Arquivo excede o limite de tamanho (máximo 10MB).', extra_tags='bg-red-500 text-white p-4 rounded')
            return redirect(reverse(redirect_url))

        try:
            # Ler o arquivo com Pandas
            df = None
            if extensao == 'csv':
                try:
                    df = pd.read_csv(arquivo, sep=';', encoding='utf-8-sig', dtype=str, keep_default_na=False, na_filter=False)
                except UnicodeDecodeError:
                    arquivo.seek(0)
                    df = pd.read_csv(arquivo, sep=';', encoding='latin-1', dtype=str, keep_default_na=False, na_filter=False)
            elif extensao in ['xls', 'xlsx']:
                df = pd.read_excel(arquivo, dtype=str, keep_default_na=False, na_values=[])

            # Converter o DataFrame para um arquivo CSV virtual
            csv_data = df.to_csv(sep=';', index=False, encoding='utf-8')
            # Criar um arquivo na memória
            csv_file = ContentFile(csv_data.encode('utf-8'))

            # Salvar o arquivo temporário
            file_path = default_storage.save('temp_import.csv', csv_file)
            # Obter o caminho completo do arquivo
            full_file_path = default_storage.path(file_path)
            # Chamar a função de importação
            registros_processados, erros_processamento = importar_dados(full_file_path, request.user) # Passar o usuário
            # Excluir o arquivo temporário
            default_storage.delete(file_path)

            # Feedback da importação
            if registros_processados > 0:
                messages.success(request, f'✅ {registros_processados} registro(s) importado(s) com sucesso!', extra_tags='bg-green-500 text-white p-4 rounded')

            if erros_processamento:
                total_erros = len(erros_processamento)
                erros_preview = "; ".join(erros_processamento[:5])
                erros_msg = f'⚠️ {total_erros} erro(s) ocorreram durante a importação. '
                if total_erros <= 5:
                    erros_msg += f'Erros: {erros_preview}'
                else:
                    erros_msg += f'Primeiros {5} erros: {erros_preview} (...e mais {total_erros - 5})'
                messages.warning(request, erros_msg, extra_tags='bg-yellow-500 text-white p-4 rounded')

        except Exception as e:
            messages.error(request, f'Erro ao processar o arquivo: {e}', extra_tags='bg-red-500 text-white p-4 rounded')
        
        return redirect(reverse(redirect_url))

    return render(request, template_name)