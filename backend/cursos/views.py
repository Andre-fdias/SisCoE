# backend/cursos/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import ProtectedError
from datetime import datetime as dt
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .models import Medalha, Cadastro
from datetime import datetime
import json



@login_required
def medalha_list(request):
    medalhas = Medalha.objects.all().select_related('cadastro')
    cadastros = Cadastro.objects.all().order_by('nome')
    
    context = {
        'medalhas': medalhas,
        'cadastros': cadastros,
        'honraria_choices': Medalha.HONRARIA_CHOICES,
        'title': 'Lista de Medalhas'
    }
    return render(request, 'cursos/medalha_list.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def medalha_edit(request, pk):
    medalha = get_object_or_404(Medalha, pk=pk)
    
    if request.method == 'GET':
        return JsonResponse({
            'cadastro_id': medalha.cadastro.id,
            'honraria': medalha.honraria,
            'bol_g_pm_lp': medalha.bol_g_pm_lp or '',
            'data_publicacao_lp': medalha.data_publicacao_lp.strftime('%Y-%m-%d') if medalha.data_publicacao_lp else '',
            'observacoes': medalha.observacoes or ''
        })

    if request.method == 'POST':
        try:
            cadastro_id = request.POST.get('cadastro')
            honraria = request.POST.get('honraria')
            bol_g_pm_lp = request.POST.get('bol_g_pm_lp', '').strip() or None
            data_publicacao_lp = request.POST.get('data_publicacao_lp') or None
            observacoes = request.POST.get('observacoes', '').strip() or None

            with transaction.atomic():
                cadastro = Cadastro.objects.get(pk=cadastro_id)
                medalha.cadastro = cadastro
                medalha.honraria = honraria
                medalha.bol_g_pm_lp = bol_g_pm_lp
                medalha.observacoes = observacoes
                
                if data_publicacao_lp:
                    medalha.data_publicacao_lp = datetime.strptime(data_publicacao_lp, '%Y-%m-%d').date()
                
                medalha.usuario_alteracao = request.user
                medalha.save()

            return JsonResponse({'success': True})
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


from django.views.decorators.http import require_http_methods


@login_required
@require_http_methods(["POST"])
def medalha_delete(request, pk):
    medalha = get_object_or_404(Medalha, pk=pk)
    try:
        medalha.delete()
        messages.success(request, 'Medalha excluída com sucesso!', extra_tags='success_message') # Adicione extra_tags
    except Exception as e:
        messages.error(request, f'Erro ao excluir medalha: {str(e)}', extra_tags='error_message') # Adicione extra_tags
    return redirect('cursos:medalha_list')


from django.db import transaction  # Importação necessária
from datetime import datetime  # Importe datetime para conversão de datas
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .models import Medalha, Cadastro
from datetime import datetime

@login_required
def medalha_create(request):
    """
    Permite o cadastro de múltiplas medalhas para um militar.
    """
    if request.method == 'POST':
        try:
            with transaction.atomic():
                militar_id = request.POST.get('militar_id')
                num_medalhas = int(request.POST.get('num_medalhas', 1))
                
                if not militar_id:
                    raise ValueError("O militar é obrigatório.")

                cadastro = Cadastro.objects.get(pk=militar_id)

                for i in range(num_medalhas):
                    honraria = request.POST.get(f'honraria_{i}')
                    if not honraria:
                        raise ValueError(f"Honraria é obrigatória para a medalha #{i + 1}")

                    bol_g_pm_lp = request.POST.get(f'bol_g_pm_lp_{i}', '').strip() or None
                    data_publicacao_lp = request.POST.get(f'data_publicacao_lp_{i}') or None
                    observacoes = request.POST.get(f'observacoes_{i}', '').strip() or None

                    data_publicacao = None
                    if data_publicacao_lp:
                        try:
                            data_publicacao = datetime.strptime(data_publicacao_lp, '%Y-%m-%d').date()
                        except ValueError:
                            raise ValueError(f"Data inválida na medalha #{i + 1}. Use AAAA-MM-DD.")

                    Medalha.objects.create(
                        cadastro=cadastro,
                        honraria=honraria,
                        bol_g_pm_lp=bol_g_pm_lp,
                        data_publicacao_lp=data_publicacao,
                        observacoes=observacoes,
                        usuario_alteracao=request.user
                    )

                messages.success(request, f"{num_medalhas} medalha(s) cadastrada(s)!", extra_tags='success_message') # Adicione extra_tags
                return redirect('cursos:medalha_list')

        except Cadastro.DoesNotExist:
            messages.error(request, "Militar não encontrado.", extra_tags='error_message') # Adicione extra_tags
        except ValueError as e:
            messages.error(request, str(e), extra_tags='error_message') # Adicione extra_tags
        except Exception as e:
            messages.error(request, f"Erro: {str(e)}", extra_tags='error_message') # Adicione extra_tags
    
    return redirect('cursos:buscar_militar_medalha')

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.messages import constants
from django.contrib.auth.decorators import login_required
from backend.efetivo.models import Cadastro, DetalhesSituacao, Promocao, Imagem
from django.contrib.messages import constants # Já estava aqui, mas agora será mais explícito


@login_required
def buscar_militar_medalha(request):
    """
    Busca um militar pelo RE (via POST) para pré-preencher o formulário de cadastro de medalha,
    ou exibe o formulário de busca (via GET).
    """
    template_name = 'cursos/medalha_form.html'

    if request.method == "POST":
        re = request.POST.get('re', '').strip()
        if not re:
            messages.add_message(
                request, 
                constants.WARNING, # Use constants.WARNING para ser mais claro
                'Por favor, informe o RE para buscar.', 
                extra_tags='warning_message' # Tag mais genérica para avisos
            )
            return render(request, template_name, {
                'honraria_choices': Medalha.HONRARIA_CHOICES,
            })

        try:
            cadastro = Cadastro.objects.get(re=re)

            promocao = Promocao.objects.filter(cadastro=cadastro).order_by('-id').first()
            detalhes = DetalhesSituacao.objects.filter(cadastro=cadastro).order_by('-id').first()
            imagem = Imagem.objects.filter(cadastro=cadastro).order_by('-id').first()

            posto_grad = promocao.posto_grad if promocao else "Não informado"
            sgb = detalhes.sgb if detalhes else "Não informado"
            posto_secao = detalhes.posto_secao if detalhes else "Não informado"

            if not detalhes:
                messages.info(
                    request, 
                    'Atenção: Dados de SGB e Posto/Seção não encontrados.', 
                    extra_tags='info_message' # Tag mais genérica para informações
                )
            if not promocao:
                messages.info(
                    request, 
                    'Atenção: Dados de Posto/Graduação não encontrados.', 
                    extra_tags='info_message'
                )
            if not imagem:
                messages.info(
                    request, 
                    'Atenção: Foto de perfil não encontrada.', 
                    extra_tags='info_message'
                )

            context = {
                'cadastro': cadastro,
                'detalhes': {
                    'sgb': sgb,
                    'posto_secao': posto_secao
                },
                'promocao': {
                    'posto_grad': posto_grad
                },
                'imagem': imagem,
                'honraria_choices': Medalha.HONRARIA_CHOICES,
                'found_re': re
            }
            return render(request, template_name, context)

        except Cadastro.DoesNotExist:
            messages.add_message(
                request, 
                constants.ERROR, # Use constants.ERROR
                f'Militar com RE {re} não encontrado.', 
                extra_tags='error_message' # Use a nova tag de erro
            )
            return render(request, template_name, {
                'honraria_choices': Medalha.HONRARIA_CHOICES,
                'searched_re': re
            })

        except Exception as e:
            messages.add_message(
                request, 
                constants.ERROR, 
                f'Erro ao buscar militar: {str(e)}', 
                extra_tags='error_message' # Use a nova tag de erro
            )
            return render(request, template_name, {
                'honraria_choices': Medalha.HONRARIA_CHOICES,
            })

    return render(request, template_name, {
        'honraria_choices': Medalha.HONRARIA_CHOICES,
    })




# backend/cursos/views.py

# ... (seus imports existentes)
from django.http import HttpResponse # Importe HttpResponse para a exportação
import csv # Para lidar com CSV na exportação
from io import TextIOWrapper, BytesIO # Para lidar com arquivos em memória na importação
from tablib import Dataset # Importe Dataset para a importação
from django.db import transaction # Já deve estar importado

# Importe seu resource
from .resources import MedalhaResource 


@login_required
@require_http_methods(["GET"]) # A exportação geralmente é um GET
def export_medalhas_csv(request):
    medalha_resource = MedalhaResource()
    # Pega todos os dados
    queryset = Medalha.objects.all().select_related('cadastro') 
    dataset = medalha_resource.export(queryset)
    
    # O format() pode ser 'csv', 'json', 'xls', 'xlsx' (se tiver as libs instaladas)
    response = HttpResponse(dataset.csv, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="medalhas.csv"'
    return response

@login_required
@require_http_methods(["GET", "POST"])
def import_medalhas_csv(request):
    if request.method == 'POST':
        # Verifica se um arquivo foi enviado
        if 'csv_file' not in request.FILES:
            messages.error(request, 'Nenhum arquivo CSV foi selecionado para importação.', extra_tags='error_message')
            return redirect('cursos:medalha_list')

        csv_file = request.FILES['csv_file']

        # Verifica o tipo do arquivo (opcional, mas recomendado)
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Formato de arquivo inválido. Por favor, envie um arquivo CSV.', extra_tags='error_message')
            return redirect('cursos:medalha_list')

        # Abre o arquivo em modo de texto para leitura
        data_set = Dataset()
        try:
            # Decode o arquivo para string (UTF-8 é comum para CSV)
            decoded_file = csv_file.read().decode('utf-8')
            # Carrega os dados do CSV
            data_set.load(decoded_file, format='csv')
        except UnicodeDecodeError:
            messages.error(request, 'Não foi possível decodificar o arquivo CSV. Verifique a codificação (tente UTF-8).', extra_tags='error_message')
            return redirect('cursos:medalha_list')
        except Exception as e:
            messages.error(request, f'Erro ao ler o arquivo CSV: {str(e)}', extra_tags='error_message')
            return redirect('cursos:medalha_list')

        medalha_resource = MedalhaResource()
        try:
            with transaction.atomic(): # Garante atomicidade da transação
                # dry_run=True executa a importação sem salvar no banco de dados para verificar erros
                result = medalha_resource.import_data(data_set, dry_run=True, raise_errors=True, collect_failed_rows=True)

                if not result.has_errors() and not result.has_validation_errors():
                    # Se não houver erros, executa a importação real
                    medalha_resource.import_data(data_set, dry_run=False, raise_errors=True, collect_failed_rows=True)
                    messages.success(request, 'Medalhas importadas com sucesso!', extra_tags='success_message')
                else:
                    # Coleta e exibe erros de validação ou importação
                    error_messages = []
                    if result.has_validation_errors():
                        for row_errors in result.validation_errors:
                            for field_error in row_errors.field_errors:
                                error_messages.append(f"Linha {row_errors.row_num}: Campo '{field_error.field}': {field_error.errors[0]}")
                    if result.has_errors():
                        for error in result.errors:
                            error_messages.append(f"Erro na linha {error.line}: {error.error_message}")
                    
                    messages.error(request, f'Erro(s) na importação: <br>' + '<br>'.join(error_messages), extra_tags='error_message')

        except ValueError as e:
            messages.error(request, f'Erro de validação durante a importação: {str(e)}', extra_tags='error_message')
        except Exception as e:
            messages.error(request, f'Erro inesperado durante a importação: {str(e)}', extra_tags='error_message')
        
        return redirect('cursos:medalha_list')
    
    # Se for GET, apenas redireciona para a lista para que a página de listagem seja exibida
    # ou você pode renderizar um template específico para o formulário de importação se preferir
    return redirect('cursos:medalha_list')


@login_required
def importar_medalhas_view(request):
    # Esta view simplesmente renderiza o formulário de importação.
    # A lógica de POST para importação já está em 'import_medalhas_csv'.
    return render(request, 'cursos/importar_medalhas.html')



from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import ProtectedError
from datetime import datetime 
from backend.efetivo.models import Cadastro, DetalhesSituacao, Promocao, Imagem
from .models import Curso, Medalha # Importe o modelo Curso
import traceback # Para logging detalhado de exceções


# --- List View (Cursos) ---

@login_required
def curso_list(request):
    """
    Exibe a lista de todos os cursos cadastrados.
    """
    cursos = Curso.objects.all().order_by('-id')  # Ordena da mais recente para a mais antiga
    cadastros = Cadastro.objects.all().order_by('nome') # Adiciona todos os cadastros
    
    context = {
        'cursos': cursos,
        'cadastros': cadastros, # Adiciona cadastros ao contexto
        'curso_choices': Curso.CURSOS_CHOICES, # Adiciona as choices de curso ao contexto
        'title': "Lista de Cursos"
    }
    return render(request, 'cursos/curso_list.html', context)



@login_required
def curso_create(request):
    """
    Permite o cadastro de um novo curso para um militar.
    Processa múltiplos cursos em uma única requisição POST.
    """
    context = {
        'title': "Cadastrar Curso",
        'curso_choices': Curso.CURSOS_CHOICES   # Renamed to match template for consistency
    }
    template_name = 'cursos/curso_form.html'

    if request.method == 'POST':
        # Captura o RE do militar que foi buscado na etapa anterior
        re = request.POST.get('militar_re_display')
        cadastro_id = request.POST.get('militar_id')
        
        if not cadastro_id:
            messages.error(request, 'É necessário buscar e selecionar um militar antes de cadastrar cursos.')
            return redirect('cursos:buscar_militar_curso')

        try:
            cadastro = get_object_or_404(Cadastro, pk=cadastro_id)
            
            # Prepara para processar múltiplos formulários de curso
            num_cursos = int(request.POST.get('num_cursos', 0))
            cursos_salvos_count = 0
            
            for i in range(num_cursos):
                curso_tipo = request.POST.get(f'curso_{i}')
                # outros_cursos = request.POST.get(f'outro_curso_{i}') # REMOVED: outros_cursos
                data_publicacao_str = request.POST.get(f'data_publicacao_{i}')
                bol_publicacao = request.POST.get(f'bol_publicacao_{i}')
                observacoes = request.POST.get(f'observacoes_{i}', '')

                # Validações básicas para cada curso
                if not curso_tipo or not data_publicacao_str or not bol_publicacao:
                    messages.warning(request, f'Ignorando curso {i+1}: Campos obrigatórios não preenchidos.')
                    continue

                try:
                    data_publicacao = dt.strptime(data_publicacao_str, '%Y-%m-%d').date()
                except ValueError:
                    messages.warning(request, f'Ignorando curso {i+1}: Formato de data inválido. Use AAAA-MM-DD.')
                    continue
                
                # if curso_tipo == 'OUTRO' and not outros_cursos: # REMOVED: outros_cursos
                #     messages.warning(request, f'Ignorando curso {i+1}: O nome do "Outro Curso" é obrigatório.')
                #     continue

                Curso.objects.create(
                    cadastro=cadastro,
                    curso=curso_tipo,
                    # outro_curso=outros_cursos if curso_tipo == 'OUTRO' else '', # REMOVED: outros_cursos
                    data_publicacao=data_publicacao,
                    bol_publicacao=bol_publicacao,
                    observacoes=observacoes,
                    usuario_alteracao=request.user
                )
                cursos_salvos_count += 1
            
            if cursos_salvos_count > 0:
                messages.success(request, f'{cursos_salvos_count} curso(s) cadastrado(s) com sucesso para o RE {re}!')
                # Redireciona para a lista de cursos
                return redirect('cursos:curso_list')
            else:
                messages.info(request, 'Nenhum curso foi cadastrado. Verifique os dados e tente novamente.')
                # Se nenhum curso foi salvo, renderiza o formulário novamente com os dados do militar
                context.update({
                    'found_militar': True,
                    'cadastro': {
                        'id': cadastro.id,
                        're': cadastro.re,
                        'nome': cadastro.nome_guerra,
                    },
                    'found_re': re,
                })
                return render(request, template_name, context)

        except Cadastro.DoesNotExist:
            messages.error(request, f'Militar com RE {re} não encontrado.')
            return redirect('cursos:buscar_militar_curso')
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar curso: {str(e)}')
            print(traceback.format_exc()) # Log do erro no console
            # Se der erro, renderiza o formulário novamente com os dados do militar
            context.update({
                'found_militar': True,
                'cadastro': {
                    'id': cadastro.id,
                    're': cadastro.re,
                    'nome': cadastro.nome_guerra,
                },
                'found_re': re,
            })
            return render(request, template_name, context)
            
    # GET request: Renderiza o formulário (geralmente após buscar o militar)
    # Se houver um 'militar_id' e 'militar_re' na sessão (vindo de buscar_militar_curso),
    # use-os para pré-popular o formulário.
    militar_id_session = request.session.pop('militar_id_curso', None)
    militar_re_session = request.session.pop('militar_re_curso', None)
    militar_nome_session = request.session.pop('militar_nome_curso', None)

    if militar_id_session and militar_re_session and militar_nome_session:
        context.update({
            'found_militar': True,
            'cadastro': {
                'id': militar_id_session,
                're': militar_re_session,
                'nome': militar_nome_session,
            },
            'found_re': militar_re_session,
        })
    return render(request, template_name, context)

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

# backend/cursos/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .models import Curso, Cadastro # Make sure to import Curso
import json

# ... other views ...

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Curso

@login_required
@require_http_methods(["GET", "POST"])
def curso_edit(request, pk):
    curso = get_object_or_404(Curso, pk=pk)

    if request.method == 'GET':
        return JsonResponse({
            'success': True,
            'curso': {
                'id': curso.id,
                'cadastro_id': curso.cadastro.id,
                'curso': curso.curso,
                'data_publicacao': curso.data_publicacao.strftime('%Y-%m-%d'),
                'bol_publicacao': curso.bol_publicacao,
                'observacoes': curso.observacoes
            }
        })

    elif request.method == 'POST':
        try:
            curso.cadastro_id = request.POST.get('cadastro_id')
            curso.curso = request.POST.get('curso')
            curso.data_publicacao = request.POST.get('data_publicacao')
            curso.bol_publicacao = request.POST.get('bol_publicacao')
            curso.observacoes = request.POST.get('observacoes')
            curso.usuario_alteracao = request.user
            curso.save()
            
            return JsonResponse({'success': True, 'message': 'Curso atualizado com sucesso!'})
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
        

        
@login_required
@require_http_methods(["POST"]) # Garante que só POSTs podem ser usados para exclusão
def curso_delete(request, pk):
    curso = get_object_or_404(Curso, pk=pk)

    try:
        curso.delete()
        return JsonResponse({'success': True, 'message': 'Curso excluído com sucesso!'})
    except ProtectedError:
        return JsonResponse({
            'success': False,
            'error': 'Não é possível excluir este curso pois existem outras entidades que dependem dele.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erro ao excluir o curso: {str(e)}'
        }, status=400)


# --- Buscar Militar para Curso ---
@login_required
def buscar_militar_curso(request):
    template_name = 'cursos/curso_form.html'
    
    # GARANTA QUE AS CHOICES SÃO SEMPRE PASSADAS, COMO NAS OUTRAS VIEWS
    context = {
        'title': "Cadastrar Curso", # Pode querer mudar o título para "Buscar Militar" ou "Cadastro de Curso"
        'curso_choices': Curso.CURSOS_CHOICES, # <-- Use o nome consistente 'curso_choices' e direto do modelo
        'submitted_data': request.session.pop('submitted_form_data', {}),
        'errors': request.session.pop('form_errors', {}),
        'cadastro': None,
        'imagem': None,
        'detalhes': {},
        'promocao': {},
    }

    # ADICIONE OS PRINTS DE DEBUG TAMBÉM AQUI
    print(f"\n--- DEBUG VIEWS.PY - buscar_militar_curso ---")
    print(f"Variável curso_choices no contexto: {context['curso_choices']}")
    print(f"Tipo de curso_choices: {type(context['curso_choices'])}")
    print(f"É uma lista vazia? {not context['curso_choices']}")
    print(f"--- FIM DEBUG VIEWS.PY - buscar_militar_curso ---\n")

    if request.method == "POST":
        re = request.POST.get('re', '').strip()
        context['searched_re'] = re

        if not re:
            messages.warning(request, 'Por favor, informe o RE para buscar.')
            return render(request, template_name, context)

        try:
            cadastro = Cadastro.objects.get(re=re)
            promocao_obj = Promocao.objects.filter(cadastro=cadastro).order_by('-id').first()
            detalhes_obj = DetalhesSituacao.objects.filter(cadastro=cadastro).order_by('-id').first()
            imagem_obj = Imagem.objects.filter(cadastro=cadastro).order_by('-id').first()

            context.update({
                'cadastro': cadastro,
                'detalhes': {
                    'sgb': detalhes_obj.sgb if detalhes_obj else "Não informado",
                    'posto_secao': detalhes_obj.posto_secao if detalhes_obj else "Não informado"
                },
                'promocao': {
                    'posto_grad': promocao_obj.posto_grad if promocao_obj else "Não informado"
                },
                'imagem': imagem_obj,
                'found_re': re,
                # Pode ser útil passar o ID e RE do militar encontrado para o formulário de cadastro,
                # para que ele saiba a qual militar o curso será associado.
                # Se 'curso_form.html' tiver um campo hidden para 'militar_id', preencha-o aqui.
                # 'militar_id': cadastro.id,
                # 'militar_re_display': cadastro.re,
            })
            
            if not detalhes_obj:
                messages.info(request, 'Atenção: Dados de SGB e Posto/Seção não encontrados.')
            if not promocao_obj:
                messages.info(request, 'Atenção: Dados de Posto/Graduação não encontrados.')
            if not imagem_obj:
                messages.info(request, 'Atenção: Foto de perfil não encontrada.')

        except Cadastro.DoesNotExist:
            messages.error(request, f'Militar com RE {re} não encontrado.')
        except Exception as e:
            messages.error(request, f'Erro ao buscar militar: {str(e)}')
            print(traceback.format_exc())

        return render(request, template_name, context)

    return render(request, template_name, context)



# backend/cursos/views.py

# ... (seus imports existentes, como datetime, transaction, JsonResponse, etc.)
from django.http import HttpResponse # Importe HttpResponse
import csv # Para lidar com CSV
from io import TextIOWrapper, BytesIO # Para lidar com arquivos em memória
from tablib import Dataset # Importe Dataset
from .resources import MedalhaResource, CursoResource # Importe seu CursoResource também!
from .models import Medalha, Cadastro, Curso # Certifique-se de importar o modelo Curso

# ... (todas as suas views existentes para medalhas e cursos)

# --- Views de Exportação/Importação para Cursos ---

@login_required
@require_http_methods(["GET"])
def export_cursos_csv(request):
    curso_resource = CursoResource()
    queryset = Curso.objects.all().select_related('cadastro') # Inclua select_related se precisar de dados do Cadastro
    dataset = curso_resource.export(queryset)
    
    response = HttpResponse(dataset.csv, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="cursos.csv"'
    return response

@login_required
@require_http_methods(["GET", "POST"])
def import_cursos_csv(request):
    if request.method == 'POST':
        if 'csv_file' not in request.FILES:
            messages.error(request, 'Nenhum arquivo CSV foi selecionado para importação de cursos.', extra_tags='error_message')
            return redirect('cursos:curso_list')

        csv_file = request.FILES['csv_file']

        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Formato de arquivo inválido. Por favor, envie um arquivo CSV para cursos.', extra_tags='error_message')
            return redirect('cursos:curso_list')

        data_set = Dataset()
        try:
            decoded_file = csv_file.read().decode('utf-8')
            data_set.load(decoded_file, format='csv')
        except UnicodeDecodeError:
            messages.error(request, 'Não foi possível decodificar o arquivo CSV de cursos. Verifique a codificação (tente UTF-8).', extra_tags='error_message')
            return redirect('cursos:curso_list')
        except Exception as e:
            messages.error(request, f'Erro ao ler o arquivo CSV de cursos: {str(e)}', extra_tags='error_message')
            return redirect('cursos:curso_list')

        curso_resource = CursoResource()
        try:
            with transaction.atomic():
                result = curso_resource.import_data(data_set, dry_run=True, raise_errors=True, collect_failed_rows=True)

                if not result.has_errors() and not result.has_validation_errors():
                    curso_resource.import_data(data_set, dry_run=False, raise_errors=True, collect_failed_rows=True)
                    messages.success(request, 'Cursos importados com sucesso!', extra_tags='success_message')
                else:
                    error_messages = []
                    if result.has_validation_errors():
                        for row_errors in result.validation_errors:
                            for field_error in row_errors.field_errors:
                                error_messages.append(f"Linha {row_errors.row_num}: Campo '{field_error.field}': {field_error.errors[0]}")
                    if result.has_errors():
                        for error in result.errors:
                            error_messages.append(f"Erro na linha {error.line}: {error.error_message}")
                    
                    messages.error(request, f'Erro(s) na importação de cursos: <br>' + '<br>'.join(error_messages), extra_tags='error_message')

        except ValueError as e:
            messages.error(request, f'Erro de validação durante a importação de cursos: {str(e)}', extra_tags='error_message')
        except Exception as e:
            messages.error(request, f'Erro inesperado durante a importação de cursos: {str(e)}', extra_tags='error_message')
        
        return redirect('cursos:curso_list')
    
    return redirect('cursos:curso_list')


@login_required
def importar_cursos_view(request):
    # Esta view renderiza o formulário de importação para cursos.
    return render(request, 'cursos/importar_cursos.html', {'title': 'Importar Cursos'})




from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction

import datetime as dt
import traceback

@login_required
def user_curso_list(request):
    """
    Exibe a lista de cursos do usuário logado.
    """
    cadastro = request.user.cadastro
    cursos = Curso.objects.filter(cadastro=cadastro).order_by('-data_publicacao')
    
    context = {
        'cursos': cursos,
        'title': "Meus Cursos"
    }
    return render(request, 'cursos/usuario_cursos.html', context)

@login_required
def user_curso_create(request):
    """
    Permite o cadastro de novos cursos para o próprio usuário logado.
    Processa múltiplos cursos em uma única requisição POST.
    """
    cadastro = request.user.cadastro
    context = {
        'title': "Cadastrar Meus Cursos",
        'curso_choices': Curso.CURSOS_CHOICES,
        'cadastro': cadastro
    }

    if request.method == 'POST':
        num_cursos = int(request.POST.get('num_cursos', 0))
        cursos_salvos_count = 0
        
        for i in range(num_cursos):
            curso_tipo = request.POST.get(f'curso_{i}')
            data_publicacao_str = request.POST.get(f'data_publicacao_{i}')
            bol_publicacao = request.POST.get(f'bol_publicacao_{i}')
            observacoes = request.POST.get(f'observacoes_{i}', '')

            # Validações básicas para cada curso
            if not curso_tipo or not data_publicacao_str or not bol_publicacao:
                messages.warning(request, f'Ignorando curso {i+1}: Campos obrigatórios não preenchidos.')
                continue

            try:
                data_publicacao = dt.datetime.strptime(data_publicacao_str, '%Y-%m-%d').date()
            except ValueError:
                messages.warning(request, f'Ignorando curso {i+1}: Formato de data inválido. Use AAAA-MM-DD.')
                continue

            Curso.objects.create(
                cadastro=cadastro,
                curso=curso_tipo,
                data_publicacao=data_publicacao,
                bol_publicacao=bol_publicacao,
                observacoes=observacoes,
                usuario_alteracao=request.user
            )
            cursos_salvos_count += 1
        
        if cursos_salvos_count > 0:
            messages.success(request, f'{cursos_salvos_count} curso(s) cadastrado(s) com sucesso!')
            return redirect('cursos:user_curso_list')
        else:
            messages.info(request, 'Nenhum curso foi cadastrado. Verifique os dados e tente novamente.')
    
    return render(request, 'cursos/usuario_curso_form.html', context)

@login_required
@require_http_methods(["GET", "POST"])
def user_curso_edit(request, pk):
    """
    Edita um curso existente do usuário logado.
    """
    curso = get_object_or_404(Curso, pk=pk)
    
    # Verifica se o curso pertence ao usuário logado
    if curso.cadastro != request.user.cadastro:
        return JsonResponse({'success': False, 'error': 'Acesso não autorizado'}, status=403)

    if request.method == 'GET':
        return JsonResponse({
            'success': True,
            'curso': {
                'id': curso.id,
                'curso': curso.curso,
                'data_publicacao': curso.data_publicacao.strftime('%Y-%m-%d'),
                'bol_publicacao': curso.bol_publicacao,
                'observacoes': curso.observacoes
            }
        })

    elif request.method == 'POST':
        try:
            curso.curso = request.POST.get('curso')
            curso.data_publicacao = request.POST.get('data_publicacao')
            curso.bol_publicacao = request.POST.get('bol_publicacao')
            curso.observacoes = request.POST.get('observacoes')
            curso.usuario_alteracao = request.user
            curso.save()
            
            return JsonResponse({'success': True, 'message': 'Curso atualizado com sucesso!'})
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_http_methods(["POST"])
def user_curso_delete(request, pk):
    """
    Exclui um curso do usuário logado.
    """
    curso = get_object_or_404(Curso, pk=pk)
    
    # Verifica se o curso pertence ao usuário logado
    if curso.cadastro != request.user.cadastro:
        return JsonResponse({
            'success': False,
            'error': 'Acesso não autorizado'
        }, status=403)

    try:
        curso.delete()
        return JsonResponse({'success': True, 'message': 'Curso excluído com sucesso!'})
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erro ao excluir o curso: {str(e)}'
        }, status=400)
    

    # backend/cursos/views.py

# backend/cursos/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import ProtectedError
from datetime import datetime as dt
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Medalha, Cadastro, Curso # Certifique-se de importar Curso se ainda não o fez
from backend.core.models import Profile
from datetime import datetime
import json


# ... suas outras views ...
@login_required
def user_curso_create(request):
    """
    Cria novos cursos para o usuário logado.
    """
    try:
        # Obtém o perfil do usuário logado
        user_profile = Profile.objects.get(user=request.user)
        
        if not user_profile.cadastro:
            messages.error(request, 'Seu perfil não está vinculado a um cadastro militar.', 
                         extra_tags='bg-red-500 text-white p-4 rounded')
            return redirect('core:index')  # Use uma URL válida
        
        cadastro = user_profile.cadastro

        if request.method == 'POST':
            num_cursos = int(request.POST.get('num_cursos', 1))
            success_count = 0

            for i in range(num_cursos):
                curso = request.POST.get(f'curso_{i}')
                data_publicacao = request.POST.get(f'data_publicacao_{i}')
                bol_publicacao = request.POST.get(f'bol_publicacao_{i}')
                observacoes = request.POST.get(f'observacoes_{i}', '')

                if all([curso, data_publicacao, bol_publicacao]):
                    try:
                        # Cria o curso associado ao cadastro do usuário
                        Curso.objects.create(
                            cadastro=cadastro,
                            curso=curso,
                            data_publicacao=data_publicacao,
                            bol_publicacao=bol_publicacao,
                            observacoes=observacoes,
                            usuario_cadastro=request.user
                        )
                        success_count += 1
                    except Exception as e:
                        messages.error(request, f'Erro ao salvar curso #{i+1}: {str(e)}',
                                     extra_tags='bg-red-500 text-white p-4 rounded')
            
            if success_count > 0:
                messages.success(request, f'{success_count} curso(s) cadastrado(s) com sucesso!',
                               extra_tags='bg-green-500 text-white p-4 rounded')
            else:
                messages.error(request, 'Nenhum curso foi cadastrado. Verifique os dados.',
                             extra_tags='bg-red-500 text-white p-4 rounded')
            
            # Redireciona para a lista de cursos do usuário
            return redirect('cursos:usuario_cursos', cadastro_id=cadastro.id)

        # Se for GET, mostrar o formulário de cadastro
        # (Você precisará criar este template ou redirecionar para onde o formulário está)
        return render(request, 'cursos/usuario_cursos.html', {
            'cadastro': cadastro,
            'title': 'Cadastrar Novo Curso'
        })

    except Profile.DoesNotExist:
        messages.error(request, 'Perfil do usuário não encontrado.',
                     extra_tags='bg-red-500 text-white p-4 rounded')
        return redirect('core:index')  # Use uma URL válida
    except Exception as e:
        messages.error(request, f'Erro inesperado: {str(e)}',
                     extra_tags='bg-red-500 text-white p-4 rounded')
        return redirect('core:index')  # Use uma URL válida