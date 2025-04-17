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
    cidades = Cidade.objects.all().select_related('posto')  # Novo queryset
    return render(request, 'posto_list.html', {
        'postos': postos,
        'cidades': cidades  # Adicionar ao contexto
    })

@login_required
def posto_detail(request, pk):
    posto = get_object_or_404(Posto, pk=pk)
    try:
        pessoal = Pessoal.objects.get(posto=posto)
    except Pessoal.DoesNotExist:
        # Handle the case where no Pessoal object exists for this Posto
        pessoal = None  # Or create an empty Pessoal object if needed

    context = {
        'posto': posto,
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
            'quartel': request.FILES.get('quartel')
            }
        
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
            'tenqo': int(request.POST.get('ten', 0)),  # Corrigido para match com o template
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
            Cidade.objects.create(
                posto=posto,
                municipio=municipios[i],
                descricao=descricoes[i],  # Nova linha
                latitude=latitudes[i],
                longitude=longitudes[i],
                bandeira=bandeiras[i] if i < len(bandeiras) else None
            )

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
from .models import Posto, Contato

def posto_update(request, pk):
    posto = get_object_or_404(Posto, pk=pk)
    contato = get_object_or_404(Contato, posto=posto)

    # Obtendo todos os choices diretamente do modelo
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

    if request.method == 'POST':
        # Atualizando os dados do Posto
        posto.sgb = request.POST.get('sgb', posto.sgb)
        posto.posto_secao = request.POST.get('posto_secao', posto.posto_secao)
        posto.posto_atendimento = request.POST.get('posto_atendimento', posto.posto_atendimento)
        posto.cidade_posto = request.POST.get('cidade_posto', posto.cidade_posto)
        posto.tipo_cidade = request.POST.get('tipo_cidade', posto.tipo_cidade)
        posto.op_adm = request.POST.get('op_adm', posto.op_adm)

        if 'quartel' in request.FILES:
            posto.quartel = request.FILES['quartel']

        posto.save()

        # Atualizando ou criando Contato
        contato.telefone = request.POST.get('telefone', contato.telefone)
        contato.rua = request.POST.get('rua', contato.rua)
        contato.numero = request.POST.get('numero', contato.numero)
        contato.complemento = request.POST.get('complemento', contato.complemento)
        contato.bairro = request.POST.get('bairro', contato.bairro)
        contato.cidade = request.POST.get('cidade', contato.cidade)
        contato.cep = request.POST.get('cep', contato.cep)
        contato.email = request.POST.get('email', contato.email)

        # **Correção para latitude e longitude**
        try:
            contato.latitude = float(request.POST.get('latitude', 0)) # Usar 0 como padrão se não for fornecido
            contato.longitude = float(request.POST.get('longitude', 0))
        except ValueError:
            # Log the error or handle it appropriately (e.g., show an error message to the user)
            print("Erro: Latitude ou longitude inválida.")
            # Optionally, you could set default values or skip saving these fields
            # contato.latitude = 0
            # contato.longitude = 0
            # or
            # pass  # Skip saving contato if lat/long are invalid
        
        contato.save()

        # Redireciona para a página de detalhes do posto
        return redirect('municipios:posto_detail', pk=posto.pk)

    return render(request, 'posto_detail.html', {'posto': posto, 'contato': contato})


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