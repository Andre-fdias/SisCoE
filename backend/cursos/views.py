# backend/cursos/views.py

# Importações padrão do Django
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse # Adicionado HttpResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import ProtectedError, Prefetch
from django.utils import timezone
from django.contrib.messages import constants # Para usar constants.SUCCESS, etc.

# Importações de bibliotecas externas
import datetime as dt
from datetime import datetime
import json
import logging
import csv
from io import TextIOWrapper, BytesIO
from tablib import Dataset
import traceback

# Importações de modelos e resources da sua aplicação
from .models import Medalha, Curso
from backend.efetivo.models import Cadastro, DetalhesSituacao, Promocao, Imagem, HistoricoDetalhesSituacao
from .resources import MedalhaResource, CursoResource # Certifique-se de ter esses resources

# Configuração de logger
logger = logging.getLogger(__name__)


# Funções auxiliares (se houver, mantidas ou adaptadas)
def get_cadastro_do_usuario(user):
    """
    Retorna o objeto Cadastro associado ao Profile do usuário logado.
    Corrige o AttributeError: 'User' object has no attribute 'cadastro'.
    Assume que o modelo Cadastro tem uma relação OneToOneField ou ForeignKey com User
    e que o related_name é 'cadastros'.
    """
    try:
        # Acessa o objeto Cadastro através do related_name 'cadastros'
        # Se for OneToOneField, user.cadastros retorna o objeto diretamente.
        # Se for ForeignKey, user.cadastros.first() ou user.cadastros.get(...) seria necessário,
        # mas para um único cadastro por usuário, OneToOneField é mais provável.
        # A mensagem de erro "Did you mean: 'cadastros'?" sugere fortemente 'user.cadastros'.
        return user.cadastros 
    except Cadastro.DoesNotExist:
        logger.warning(f"Cadastro não encontrado para o usuário {user.username}.")
        return None
    except Exception as e:
        logger.error(f"Erro inesperado ao obter Cadastro para o usuário {user.username}: {str(e)}", exc_info=True)
        return None



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


# backend/cursos/views.py
# backend/cursos/views.py

# Importações padrão do Django
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404 # Adicionado HttpResponse, Http404
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import ProtectedError, Prefetch
from django.utils import timezone
from django.contrib.messages import constants # Para usar constants.SUCCESS, etc.
from django.contrib.auth import get_user_model # Importar o modelo User

# Importações de bibliotecas externas
import datetime as dt
from datetime import datetime
import json
import logging
import csv
from io import TextIOWrapper, BytesIO
from tablib import Dataset
import traceback

# Importações de modelos e resources da sua aplicação
from .models import Medalha, Curso
from backend.efetivo.models import Cadastro, DetalhesSituacao, Promocao, Imagem, HistoricoDetalhesSituacao
# Assumindo que resources são usados para import/export, mantenho. Ajuste se não for o caso.
from .resources import MedalhaResource, CursoResource 

# Configuração de logger
logger = logging.getLogger(__name__)

# Obter o modelo de usuário personalizado
User = get_user_model()


# --- Views para Cursos do Usuário Logado ---

@login_required
def user_curso_list(request):
    """
    Exibe a lista de cursos do usuário logado.
    """
    # Acessa o cadastro diretamente do usuário logado
    if not hasattr(request.user, 'cadastro') or not request.user.cadastro:
        messages.error(request, 'Seu perfil não está vinculado a um cadastro militar.', 
                       extra_tags='error_message')
        return redirect('core:index')

    cadastro = request.user.cadastro
    cursos = Curso.objects.filter(cadastro=cadastro).order_by('-data_publicacao')
    
    # Obter dados adicionais para o contexto (detalhes, promocao, etc.)
    detalhes = cadastro.detalhes_situacao.order_by('-apresentacao_na_unidade').first()
    promocao = cadastro.promocoes.order_by('-data_alteracao').first()
    promocoes = cadastro.promocoes.order_by('-data_alteracao')
    
    context = {
        'cursos': cursos,
        'title': "Meus Cursos",
        'cadastro': cadastro, # Passa o objeto cadastro para o template
        'detalhes': detalhes,
        'promocao': promocao,
        'promocoes': promocoes,
        'today': timezone.now().date(),
        'curso_choices': Curso.CURSOS_CHOICES, # Garante que as choices estão disponíveis
        # Adicione as choices dos modelos para os selects no template
        'situacao_choices': DetalhesSituacao.situacao_choices,
        'sgb_choices': DetalhesSituacao.sgb_choices,
        'posto_secao_choices': DetalhesSituacao.posto_secao_choices,
        'esta_adido_choices': DetalhesSituacao.esta_adido_choices,
        'funcao_choices': DetalhesSituacao.funcao_choices,
        'prontidao_choices': DetalhesSituacao.prontidao_choices,
        'posto_grad_choices': Promocao.posto_grad_choices,
        'quadro_choices': Promocao.quadro_choices,
        'grupo_choices': Promocao.grupo_choices,
        'genero_choices': Cadastro.genero_choices,
        'alteracao_choices': Cadastro.alteracao_choices,
    }
    return render(request, 'cursos/usuario_cursos.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def user_curso_create(request):
    """
    Permite ao usuário logado cadastrar novos cursos para seu próprio perfil.
    GET: Exibe o formulário de cadastro de cursos.
    POST: Processa o envio do formulário, permitindo o cadastro de múltiplos cursos.
    """
    try:
        # Acessa o cadastro diretamente do usuário logado
        if not hasattr(request.user, 'cadastro') or not request.user.cadastro:
            if request.method == 'GET':
                messages.error(request, 'Seu perfil não está vinculado a um cadastro militar.', extra_tags='error_message')
                return redirect('core:index')
            return JsonResponse({
                'success': False, 
                'error': 'Seu perfil não está vinculado a um cadastro militar.'
            }, status=400)

        cadastro = request.user.cadastro
    except Exception as e:
        logger.error(f"Erro inesperado ao carregar cadastro para criação de cursos: {str(e)}", exc_info=True)
        if request.method == 'GET':
            messages.error(request, f'Erro inesperado ao carregar dados do perfil: {str(e)}', extra_tags='error_message')
            return redirect('core:index')
        return JsonResponse({
            'success': False, 
            'error': f'Erro inesperado ao carregar dados do perfil: {str(e)}'
        }, status=500)

    # Obter dados adicionais para o contexto
    today = timezone.now().date()
    detalhes = cadastro.detalhes_situacao.order_by('-apresentacao_na_unidade').first()
    promocao = cadastro.promocoes.order_by('-data_alteracao').first()
    promocoes = cadastro.promocoes.order_by('-data_alteracao')

    if request.method == 'POST':
        num_cursos = int(request.POST.get('num_cursos', 0))
        cursos_salvos_count = 0
        errors = []
        
        with transaction.atomic():
            for i in range(num_cursos):
                curso_tipo = request.POST.get(f'curso_{i}')
                data_publicacao_str = request.POST.get(f'data_publicacao_{i}')
                bol_publicacao = request.POST.get(f'bol_publicacao_{i}', '').strip()
                observacoes = request.POST.get(f'observacoes_{i}', '').strip()

                # Validação dos campos obrigatórios
                if not curso_tipo:
                    errors.append(f'Curso #{i+1}: Tipo de curso é obrigatório.')
                    continue
                if not data_publicacao_str:
                    errors.append(f'Curso #{i+1}: Data de Publicação é obrigatória.')
                    continue

                try:
                    data_publicacao = datetime.strptime(data_publicacao_str, '%Y-%m-%d').date()
                    
                    # Verificar se a data não é futura
                    if data_publicacao > timezone.now().date():
                        errors.append(f'Curso #{i+1}: Data de publicação não pode ser futura.')
                        continue
                        
                except ValueError:
                    errors.append(f'Curso #{i+1}: Formato de data inválido. Use AAAA-MM-DD.')
                    continue

                try:
                    Curso.objects.create(
                        cadastro=cadastro,
                        curso=curso_tipo,
                        data_publicacao=data_publicacao,
                        bol_publicacao=bol_publicacao,
                        observacoes=observacoes,
                        usuario_alteracao=request.user
                    )
                    cursos_salvos_count += 1
                except Exception as e:
                    logger.error(f"Erro ao salvar curso #{i+1}: {str(e)}", exc_info=True)
                    errors.append(f'Curso #{i+1}: Erro ao salvar - {str(e)}')
        
        if errors:
            return JsonResponse({
                'success': False, 
                'error': 'Alguns erros ocorreram: ' + '; '.join(errors)
            }, status=400)
        elif cursos_salvos_count > 0:
            return JsonResponse({
                'success': True, 
                'message': f'{cursos_salvos_count} curso(s) cadastrado(s) com sucesso!'
            })
        else:
            return JsonResponse({
                'success': False, 
                'error': 'Nenhum curso foi cadastrado. Verifique os dados e tente novamente.'
            }, status=400)

    # Renderizar template para GET
    # A lista de medalhas e cursos do militar pode não ser necessária na view de criação.
    # Mas se o template 'usuario_cursos.html' espera isso, mantemos.
    medalhas_do_militar = Medalha.objects.filter(cadastro=cadastro).order_by('-data_publicacao_lp')
    cursos_do_militar = Curso.objects.filter(cadastro=cadastro).order_by('-data_publicacao')

    context = {
        'cadastro': cadastro,
        'title': 'Cadastrar Novo Curso',
        'medalhas_do_militar': medalhas_do_militar,
        'cursos_do_militar': cursos_do_militar,
        'curso_choices': Curso.CURSOS_CHOICES,

        'detalhes': detalhes,
        'promocao': promocao,
        'today': today,
        'promocoes': promocoes,
        
        # Adicione as choices dos modelos para os selects no template
        'situacao_choices': DetalhesSituacao.situacao_choices,
        'sgb_choices': DetalhesSituacao.sgb_choices,
        'posto_secao_choices': DetalhesSituacao.posto_secao_choices,
        'esta_adido_choices': DetalhesSituacao.esta_adido_choices,
        'funcao_choices': DetalhesSituacao.funcao_choices,
        'prontidao_choices': DetalhesSituacao.prontidao_choices,
        'posto_grad_choices': Promocao.posto_grad_choices,
        'quadro_choices': Promocao.quadro_choices,
        'grupo_choices': Promocao.grupo_choices,
        'genero_choices': Cadastro.genero_choices,
        'alteracao_choices': Cadastro.alteracao_choices,
    }
    return render(request, 'cursos/usuario_cursos.html', context)

@login_required
@require_http_methods(["GET", "POST"])
def user_curso_edit(request, pk):
    """
    Permite ao usuário logado editar um de seus cursos.
    GET: Retorna os dados do curso em formato JSON.
    POST: Atualiza o curso e retorna uma resposta JSON.
    """
    try:
        # Garante que só pode editar os próprios cursos
        curso = get_object_or_404(Curso, pk=pk, cadastro__user_account=request.user) # Ajuste para user_account
        
        if request.method == 'GET':
            # Retorna os dados do curso para preencher o modal de edição
            curso_data = {
                'id': curso.id,
                'curso': curso.curso,
                'data_publicacao': curso.data_publicacao.strftime('%Y-%m-%d'),
                'bol_publicacao': curso.bol_publicacao,
                'observacoes': curso.observacoes or '',
            }
            return JsonResponse({'success': True, 'curso': curso_data})

        elif request.method == 'POST':
            # Validação e atualização do curso
            curso_tipo = request.POST.get('curso')
            data_publicacao_str = request.POST.get('data_publicacao')
            bol_publicacao = request.POST.get('bol_publicacao')
            observacoes = request.POST.get('observacoes', '').strip()

            # Validação básica dos campos
            if not all([curso_tipo, data_publicacao_str, bol_publicacao]):
                return JsonResponse({
                    'success': False, 
                    'error': 'Por favor, preencha todos os campos obrigatórios.'
                }, status=400)

            try:
                data_publicacao = datetime.strptime(data_publicacao_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'success': False, 
                    'error': 'Formato de data inválido. Use AAAA-MM-DD.'
                }, status=400)

            with transaction.atomic():
                curso.curso = curso_tipo
                curso.data_publicacao = data_publicacao
                curso.bol_publicacao = bol_publicacao
                curso.observacoes = observacoes
                curso.usuario_alteracao = request.user
                curso.save()

            return JsonResponse({
                'success': True, 
                'message': 'Curso atualizado com sucesso!'
            })

    except Http404:
        return JsonResponse({
            'success': False, 
            'error': 'Curso não encontrado ou não pertence ao usuário.'
        }, status=404)
    except Exception as e:
        logger.error(f"Erro inesperado ao atualizar curso {pk}: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False, 
            'error': 'Erro interno do servidor ao atualizar o curso.'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def user_curso_delete(request, pk):
    """
    Permite ao usuário logado excluir um de seus cursos.
    Retorna uma resposta JSON indicando sucesso ou falha.
    """
    try:
        # Garante que só pode excluir os próprios cursos
        curso = get_object_or_404(Curso, pk=pk, cadastro__user_account=request.user) # Ajuste para user_account
        
        with transaction.atomic():
            curso.delete()
            
        return JsonResponse({
            'success': True, 
            'message': 'Curso excluído com sucesso!'
        })
        
    except Http404:
        return JsonResponse({
            'success': False, 
            'error': 'Curso não encontrado ou não pertence ao usuário.'
        }, status=404)
    except ProtectedError:
        logger.warning(f"Tentativa de excluir curso {pk} protegido por FKs.")
        return JsonResponse({
            'success': False, 
            'error': 'Este curso não pode ser excluído devido a dependências.'
        }, status=400)
    except Exception as e:
        logger.error(f"Erro ao excluir curso {pk}: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False, 
            'error': 'Erro interno do servidor ao excluir o curso.'
        }, status=500)


# --- Views para Medalhas do Usuário Logado ---

@login_required
def user_medalha_list(request):
    """
    Lista as medalhas associadas ao perfil do usuário logado.
    """
    try:
        # Acessa o cadastro diretamente do usuário logado
        if not hasattr(request.user, 'cadastro') or not request.user.cadastro:
            messages.error(request, 'Seu perfil não está vinculado a um cadastro militar.',
                           extra_tags='error_message')
            return redirect('core:index') 
        
        cadastro = request.user.cadastro
        medalhas_do_militar = Medalha.objects.filter(cadastro=cadastro).order_by('-data_publicacao_lp')

        # Carrega dados adicionais do militar para o template (promocoes, detalhes_situacao)
        detalhes = cadastro.detalhes_situacao.order_by('-apresentacao_na_unidade').first()
        promocao = cadastro.promocoes.order_by('-data_alteracao').first()
        promocoes = cadastro.promocoes.order_by('-data_alteracao') # Para listar todas as promoções

        context = {
            'cadastro': cadastro,
            'medalhas_do_militar': medalhas_do_militar,
            'honraria_choices': Medalha.HONRARIA_CHOICES, # Para o modal de edição/criação
            'title': 'Minhas Medalhas',
            'detalhes': detalhes,
            'promocao': promocao,
            'promocoes': promocoes,
            'today': timezone.now().date(),
            # Adicione as choices dos modelos para os selects no template
            'situacao_choices': DetalhesSituacao.situacao_choices,
            'sgb_choices': DetalhesSituacao.sgb_choices,
            'posto_secao_choices': DetalhesSituacao.posto_secao_choices,
            'esta_adido_choices': DetalhesSituacao.esta_adido_choices,
            'funcao_choices': DetalhesSituacao.funcao_choices,
            'prontidao_choices': DetalhesSituacao.prontidao_choices,
            'posto_grad_choices': Promocao.posto_grad_choices,
            'quadro_choices': Promocao.quadro_choices,
            'grupo_choices': Promocao.grupo_choices,
            'genero_choices': Cadastro.genero_choices,
            'alteracao_choices': Cadastro.alteracao_choices,
        }
        return render(request, 'cursos/usuario_medalha.html', context)

    except Exception as e:
        logger.error(f"Erro inesperado ao carregar lista de medalhas do usuário: {str(e)}", exc_info=True)
        messages.error(request, f'Erro inesperado ao carregar suas medalhas: {str(e)}', extra_tags='error_message')
        return redirect('core:index')

@login_required
@require_http_methods(["GET", "POST"])
def user_medalha_create(request):
    """
    Permite ao usuário logado cadastrar novas medalhas para seu próprio perfil.
    GET: Exibe o formulário de cadastro de medalhas.
    POST: Processa o envio do formulário, permitindo o cadastro de múltiplas medalhas.
    """
    try:
        # Acessa o cadastro diretamente do usuário logado
        if not hasattr(request.user, 'cadastro') or not request.user.cadastro:
            # Para requisições GET, redireciona com mensagem de erro
            if request.method == 'GET':
                messages.error(request, 'Seu perfil não está vinculado a um cadastro militar.', extra_tags='error_message')
                return redirect('core:index')
            # Para requisições POST (AJAX), retorna JSON
            return JsonResponse({'success': False, 'error': 'Seu perfil não está vinculado a um cadastro militar.'}, status=400)

        cadastro = request.user.cadastro # O cadastro do usuário logado
    except Exception as e:
        logger.error(f"Erro inesperado ao carregar cadastro para criação de medalhas: {str(e)}", exc_info=True)
        if request.method == 'GET':
            messages.error(request, f'Erro inesperado ao carregar dados do perfil: {str(e)}', extra_tags='error_message')
            return redirect('core:index')
        return JsonResponse({'success': False, 'error': f'Erro inesperado ao carregar dados do perfil: {str(e)}'}, status=500)

    # Dados a serem passados para o template, independentemente do método (GET/POST)
    today = timezone.now().date()
    detalhes = cadastro.detalhes_situacao.order_by('-apresentacao_na_unidade').first()
    promocao = cadastro.promocoes.order_by('-data_alteracao').first()
    promocoes = cadastro.promocoes.order_by('-data_alteracao')
    
    if request.method == 'POST':
        num_medalhas = int(request.POST.get('num_medalhas', 0))
        medalhas_salvas_count = 0 # Corrigido: 'medalhas_salvos_count' para 'medalhas_salvas_count'
        errors = []
        
        with transaction.atomic(): # Garante que todas as medalhas são salvas ou nenhuma
            for i in range(num_medalhas):
                honraria = request.POST.get(f'honraria_{i}')
                data_publicacao_lp_str = request.POST.get(f'data_publicacao_lp_{i}')
                bol_g_pm_lp = request.POST.get(f'bol_g_pm_lp_{i}', '').strip()
                observacoes = request.POST.get(f'observacoes_{i}', '').strip()

                # Validação dos campos obrigatórios
                if not honraria:
                    errors.append(f'Medalha #{i+1}: Honraria é obrigatória.')
                    continue
                if not data_publicacao_lp_str:
                    errors.append(f'Medalha #{i+1}: Data de Publicação LP é obrigatória.')
                    continue

                data_publicacao_lp = None
                if data_publicacao_lp_str:
                    try:
                        data_publicacao_lp = datetime.strptime(data_publicacao_lp_str, '%Y-%m-%d').date()
                    except ValueError:
                        errors.append(f'Medalha #{i+1}: Formato de data inválido. Use AAAA-MM-DD.')
                        continue
                
                try:
                    Medalha.objects.create(
                        cadastro=cadastro,
                        honraria=honraria,
                        data_publicacao_lp=data_publicacao_lp,
                        bol_g_pm_lp=bol_g_pm_lp,
                        observacoes=observacoes,
                        usuario_alteracao=request.user
                    )
                    medalhas_salvas_count += 1
                except Exception as e:
                    logger.error(f"Erro ao salvar medalha #{i+1}: {str(e)}", exc_info=True)
                    errors.append(f'Medalha #{i+1}: Erro ao salvar - {str(e)}')
        
        if errors:
            return JsonResponse({'success': False, 'error': 'Alguns erros ocorreram: ' + '; '.join(errors)}, status=400)
        elif medalhas_salvas_count > 0:
            # Removido messages.success para evitar possível conflito com JsonResponse
            return JsonResponse({'success': True, 'message': f'{medalhas_salvas_count} medalha(s) cadastrada(s) com sucesso!'})
        else:
            return JsonResponse({'success': False, 'error': 'Nenhuma medalha foi cadastrada. Verifique os dados e tente novamente.'}, status=400)

    # Se for GET, renderiza o template (o mesmo que user_medalha_list pode usar)
    # Certifique-se de que este GET path está correto no seu urls.py
    medalhas_do_militar = Medalha.objects.filter(cadastro=cadastro).order_by('-data_publicacao_lp')
    cursos_do_militar = Curso.objects.filter(cadastro=cadastro).order_by('-data_publicacao')

    context = {
        'cadastro': cadastro,
        'title': 'Cadastrar Nova Medalha',
        'medalhas_do_militar': medalhas_do_militar,
        'cursos_do_militar': cursos_do_militar,
        'honraria_choices': Medalha.HONRARIA_CHOICES,

        'detalhes': detalhes,
        'promocao': promocao,
        'today': today,
        'promocoes': promocoes,
        
        # Adicione as choices dos modelos para os selects no template
        'situacao_choices': DetalhesSituacao.situacao_choices,
        'sgb_choices': DetalhesSituacao.sgb_choices,
        'posto_secao_choices': DetalhesSituacao.posto_secao_choices,
        'esta_adido_choices': DetalhesSituacao.esta_adido_choices,
        'funcao_choices': DetalhesSituacao.funcao_choices,
        'prontidao_choices': DetalhesSituacao.prontidao_choices,
        'posto_grad_choices': Promocao.posto_grad_choices,
        'quadro_choices': Promocao.quadro_choices,
        'grupo_choices': Promocao.grupo_choices,
        'genero_choices': Cadastro.genero_choices,
        'alteracao_choices': Cadastro.alteracao_choices,
    }
    return render(request, 'cursos/usuario_medalha.html', context)

@login_required
@require_http_methods(["GET", "POST"])
def user_medalha_edit(request, pk):
    """
    Permite ao usuário logado editar uma de suas medalhas.
    GET: Retorna os dados da medalha em formato JSON para preencher o modal.
    POST: Atualiza os dados da medalha no banco de dados.
    """
    try:
        # Garante que só pode editar as próprias medalhas
        medalha = get_object_or_404(Medalha, pk=pk, cadastro__user_account=request.user) # Ajuste para user_account
        
        if request.method == 'GET':
            return JsonResponse({
                'success': True,
                'medalha': {
                    'id': medalha.pk,
                    'honraria': medalha.honraria,
                    'bol_g_pm_lp': medalha.bol_g_pm_lp or '',
                    'data_publicacao_lp': medalha.data_publicacao_lp.strftime('%Y-%m-%d') if medalha.data_publicacao_lp else '',
                    'observacoes': medalha.observacoes or ''
                }
            })

        elif request.method == 'POST':
            try:
                with transaction.atomic():
                    honraria = request.POST.get('honraria')
                    bol_g_pm_lp = request.POST.get('bol_g_pm_lp', '').strip() or None
                    data_publicacao_lp_str = request.POST.get('data_publicacao_lp') or None
                    observacoes = request.POST.get('observacoes', '').strip() or None

                    if not honraria:
                        raise ValueError("A honraria é obrigatória.")

                    data_publicacao_lp = None
                    if data_publicacao_lp_str:
                        try:
                            data_publicacao_lp = datetime.strptime(data_publicacao_lp_str, '%Y-%m-%d').date()
                        except ValueError:
                            raise ValueError("Formato de data de publicação inválido. Use AAAA-MM-DD.")

                    medalha.honraria = honraria
                    medalha.bol_g_pm_lp = bol_g_pm_lp
                    medalha.data_publicacao_lp = data_publicacao_lp
                    medalha.observacoes = observacoes
                    medalha.usuario_alteracao = request.user
                    medalha.save()

                # Removido messages.success para evitar conflito com JsonResponse
                return JsonResponse({'success': True, 'message': 'Medalha atualizada com sucesso!'})
            except ValueError as e:
                logger.error(f"Erro de validação ao atualizar medalha {pk}: {str(e)}", exc_info=True)
                return JsonResponse({'success': False, 'error': str(e)}, status=400)
            except Exception as e:
                logger.error(f"Erro inesperado ao atualizar medalha {pk}: {str(e)}", exc_info=True)
                return JsonResponse({'success': False, 'error': 'Erro interno do servidor ao atualizar a medalha.'}, status=500)
    except Http404:
        return JsonResponse({
            'success': False, 
            'error': 'Medalha não encontrada ou não pertence ao usuário.'
        }, status=404)
    except Exception as e:
        logger.error(f"Erro geral ao editar medalha {pk}: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False, 
            'error': 'Erro interno do servidor ao processar a requisição.'
        }, status=500)

@login_required
@require_http_methods(["POST"])
def user_medalha_delete(request, pk):
    """
    Permite ao usuário logado excluir uma de suas medalhas.
    Retorna uma resposta JSON indicando sucesso ou falha.
    """
    try:
        # Garante que só pode excluir as próprias medalhas
        medalha = get_object_or_404(Medalha, pk=pk, cadastro__user_account=request.user) # Ajuste para user_account
        with transaction.atomic():
            medalha.delete()
        # Removido messages.success para evitar conflito com JsonResponse
        return JsonResponse({'success': True, 'message': 'Medalha excluída com sucesso!'})
    except Http404:
        return JsonResponse({
            'success': False, 
            'error': 'Medalha não encontrada ou não pertence ao usuário.'
        }, status=404)
    except ProtectedError:
        logger.warning(f"Tentativa de excluir medalha {pk} protegida por FKs.")
        # Removido messages.error para evitar conflito com JsonResponse
        return JsonResponse({
            'success': False, 
            'error': 'Esta medalha não pode ser excluída devido a dependências.'
        }, status=400)
    except Exception as e:
        logger.error(f"Erro ao excluir medalha {pk}: {str(e)}", exc_info=True)
        # Removido messages.error para evitar conflito com JsonResponse
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

