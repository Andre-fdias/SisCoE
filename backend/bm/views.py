from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from .models import Cadastro_bm, Imagem_bm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.messages import constants
from datetime import datetime
from django.contrib.auth.decorators import user_passes_test



def listar_bm(request):
    cadastros = Cadastro_bm.objects.all()
    return render(request, 'listar_bm.html', {'cadastros': cadastros})

def ver_bm(request, pk):
    cadastro = get_object_or_404(Cadastro_bm, pk=pk)
    return render(request, 'ver_bm.html', {'cadastro': cadastro})

@login_required
def cadastrar_bm(request):
    if request.method == 'GET':
        context = {
            'genero': Cadastro_bm.genero_choices,
            'ovb': Cadastro_bm.ovb_choices,
            'esb': Cadastro_bm.esb_choices,
            'sgb': Cadastro_bm.sgb_choices,
            'posto_secao': Cadastro_bm.posto_secao_choices,
            'cat_cnh': Cadastro_bm.cat_cnh_choices,
            'funcao': Cadastro_bm.funcao_choices,
            'situacao': Cadastro_bm.situacao_choices,
            'alteracao': Cadastro_bm.alteracao_choices,
        }
        return render(request, 'cadastro_bm.html', context)

    elif request.method == "POST":
        print("Dados recebidos no POST:")
        print(request.POST)

        cpf = request.POST.get('cpf')
        if Cadastro_bm.objects.filter(cpf=cpf).exists():
            messages.add_message(request, constants.ERROR, 'Erro: CPF já cadastrado.', extra_tags='bg-red-500 text-white p-4 rounded')
            return redirect('bm:cadastrar_bm')

        try:
            # Validação de datas
            admissao = request.POST.get('admissao')
            nasc = request.POST.get('nasc')
            apresentacao_na_unidade = request.POST.get('apresentacao_na_unidade')
            saida_da_unidade = request.POST.get('saida_da_unidade')

            # Verificar se as datas estão no formato correto
            for date_str in [admissao, nasc, apresentacao_na_unidade, saida_da_unidade]:
                if date_str:
                    datetime.strptime(date_str, '%Y-%m-%d')

            cadastro = Cadastro_bm(
                nome=request.POST.get('nome'),
                nome_de_guerra=request.POST.get('nome_de_guerra'),
                situacao=request.POST.get('situacao'),
                sgb=request.POST.get('sgb'),
                posto_secao=request.POST.get('posto_secao'),
                cpf=request.POST.get('cpf'),
                rg=request.POST.get('rg'),
                cnh=request.POST.get('cnh'),
                cat_cnh=request.POST.get('cat_cnh'),
                esb=request.POST.get('esb'),
                ovb=request.POST.get('ovb'),
                admissao=admissao,
                nasc=nasc,
                email=request.POST.get('email'),
                telefone=request.POST.get('telefone'),
                apresentacao_na_unidade=apresentacao_na_unidade,
                saida_da_unidade=saida_da_unidade,
                funcao=request.POST.get('funcao'),
                genero=request.POST.get('genero'),
                user=request.user,
            )

            cadastro.save()


            # Upload da imagem
            if request.FILES.get('image'):
                imagem = Imagem_bm(
                    cadastro=cadastro,
                    image=request.FILES.get('image'),
                    user=request.user
                )
                imagem.save()
                print("Imagem salva com sucesso")


            messages.success(request, "Cadastro realizado com sucesso!",  extra_tags='bg-green-500 text-white p-4 rounded')
            return redirect('bm:listar_bm')
        except ValueError as e:
            messages.add_message(request, constants.ERROR, f'Erro ao cadastrar: {e}', extra_tags='bg-red-500 text-white p-4 rounded')
            return redirect('bm:cadastrar_bm')
    return render(request, 'cadastro_bm.html')


@login_required
def editar_bm(request, pk):
    cadastro = get_object_or_404(Cadastro_bm, pk=pk)
    if request.method == "POST":
        cadastro.nome = request.POST.get('nome')
        cadastro.nome_de_guerra = request.POST.get('nome_de_guerra')
        cadastro.situacao = request.POST.get('situacao')
        cadastro.sgb = request.POST.get('sgb')
        cadastro.posto_secao = request.POST.get('posto_secao')
        cadastro.cpf = request.POST.get('cpf')
        cadastro.rg = request.POST.get('rg')
        cadastro.cnh = request.POST.get('cnh')
        cadastro.cat_cnh = request.POST.get('cat_cnh')
        cadastro.categoria = request.POST.get('categoria')
        cadastro.esb = request.POST.get('esb')
        cadastro.ovb = request.POST.get('ovb')
        cadastro.admissao = request.POST.get('admissao')
        cadastro.nasc = request.POST.get('nasc')
        cadastro.email = request.POST.get('email')
        cadastro.telefone = request.POST.get('telefone')
        cadastro.apresentacao_na_unidade = request.POST.get('apresentacao_na_unidade')
        cadastro.saida_da_unidade = request.POST.get('saida_da_unidade')
        cadastro.funcao = request.POST.get('funcao')
        cadastro.genero = request.POST.get('genero')

        # Upload da imagem
        if 'image' in request.FILES:
            imagem = Imagem_bm(cadastro=cadastro, image=request.FILES['image'], user=request.user)
            imagem.save()

        cadastro.save()
        messages.success(request, "Cadastro atualizado com sucesso!")
        return redirect('bm:listar_bm')

    context = {
        'cadastro': cadastro,
        'genero': Cadastro_bm.genero_choices,
        'ovb': Cadastro_bm.ovb_choices,
        'esb': Cadastro_bm.esb_choices,
        'sgb': Cadastro_bm.sgb_choices,
        'posto_secao': Cadastro_bm.posto_secao_choices,
        'cat_cnh': Cadastro_bm.cat_cnh_choices,
        'funcao': Cadastro_bm.funcao_choices,
        'situacao': Cadastro_bm.situacao_choices,
        'alteracao': Cadastro_bm.alteracao_choices,
    }
    return render(request, 'editar_bm.html', context)
def excluir_bm(request, pk):
    cadastro = get_object_or_404(Cadastro_bm, pk=pk)
    if request.method == "POST":
        cadastro.delete()
        return redirect('bm:listar_bm')
    return render(request, 'bm/excluir_bm.html', {'cadastro': cadastro})

import pandas as pd
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime
from .models import Cadastro_bm

@login_required
@user_passes_test(lambda u: u.is_superuser)
def importar_bm(request):
    if request.method == 'POST' and request.FILES.get('arquivo'):
        arquivo = request.FILES['arquivo']
        extensao = arquivo.name.split('.')[-1].lower()
        
        try:
            if extensao == 'csv':
                df = pd.read_csv(arquivo)
            elif extensao in ['xls', 'xlsx']:
                df = pd.read_excel(arquivo)
            else:
                messages.error(request, 'Formato de arquivo não suportado!')
                return redirect('bm:importar_bm')
            
            # Converter nomes das colunas para minúsculas
            df.columns = df.columns.str.lower()
            
            for index, row in df.iterrows():
                # Verificar CPF único
                if Cadastro_bm.objects.filter(cpf=row['cpf']).exists():
                    continue  # Pula registro duplicado
                
                # Converter datas
                def converter_data(data_str):
                    try:
                        return datetime.strptime(str(data_str), '%Y-%m-%d').date()
                    except:
                        return None
                
                Cadastro_bm.objects.create(
                    nome=row.get('nome', ''),
                    nome_de_guerra=row.get('nome_de_guerra', ''),
                    situacao=row.get('situacao', 'Efetivo'),
                    sgb=row.get('sgb', ''),
                    posto_secao=row.get('posto_secao', ''),
                    cpf=row.get('cpf', ''),
                    rg=row.get('rg', ''),
                    cnh=row.get('cnh', ''),
                    cat_cnh=row.get('cat_cnh', ''),
                    esb=row.get('esb', 'NÃO'),
                    ovb=row.get('ovb', 'NÃO POSSUI'),
                    admissao=converter_data(row.get('admissao')),
                    nasc=converter_data(row.get('nasc')),
                    email=row.get('email', ''),
                    telefone=row.get('telefone', ''),
                    apresentacao_na_unidade=converter_data(row.get('apresentacao_na_unidade')),
                    saida_da_unidade=converter_data(row.get('saida_da_unidade')),
                    funcao=row.get('funcao', ''),
                    genero=row.get('genero', 'Masculino'),
                    user=request.user
                )
            
            messages.success(request, f'Dados importados com sucesso! {len(df)} registros processados.')
            return redirect('bm:listar_bm')
            
        except Exception as e:
            messages.error(request, f'Erro na importação: {str(e)}')
            return redirect('bm:importar_bm')
    
    return render(request, 'importar_bm.html')