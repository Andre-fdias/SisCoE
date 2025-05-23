# backend/cursos/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import ProtectedError
from datetime import datetime as dt


# If you use these models in 'buscar_militar_medalha', uncomment and ensure they exist
# from .models import DetalhesSituacao, Imagem, Promocao, MilitarMedalha 


# --- List View ---
@login_required
def medalha_list(request):
    """
    Exibe a lista de todas as medalhas cadastradas.
    """
    medalhas = Medalha.objects.all().order_by('-id') # Ordena da mais recente para a mais antiga
    context = {
        'medalhas': medalhas,
        'title': "Lista de Medalhas"
    }
    # Corrigido o caminho do template para 'cursos/medalha_list.html'
    return render(request, 'cursos/medalha_list.html', context)



from django.db import transaction  # Importação necessária
from datetime import datetime  # Importe datetime para conversão de datas

@login_required
def medalha_create(request):
    """
    Permite o cadastro de múltiplas medalhas para um militar.
    """
    if request.method == 'POST':
        try:
            with transaction.atomic():  # Agora transaction está definido
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

                    # Processar data
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

                messages.success(request, f"{num_medalhas} medalha(s) cadastrada(s)!")
                return redirect('cursos:medalha_list')

        except Cadastro.DoesNotExist:
            messages.error(request, "Militar não encontrado.")
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f"Erro: {str(e)}")
    
    return redirect('cursos:buscar_militar_medalha')

# --- Update View ---
@login_required
def medalha_edit(request, pk):
    """
    Permite a edição de uma medalha existente.
    """
    medalha = get_object_or_404(Medalha, pk=pk) # Obtém a medalha ou retorna 404
    cadastros = Cadastro.objects.all().order_by('nome')
    honraria_choices = Medalha.HONRARIA_CHOICES

    # Inicializa 'errors' e 'submitted_data'
    errors = {}
    submitted_data = None # Será preenchido com request.POST se houver erros, ou com o objeto medalha em GET

    if request.method == 'POST':
        cadastro_id = request.POST.get('cadastro')
        honraria = request.POST.get('honraria')
        bol_g_pm_lp = request.POST.get('bol_g_pm_lp')
        data_publicacao_lp_str = request.POST.get('data_publicacao_lp')
        observacoes = request.POST.get('observacoes')

        submitted_data = request.POST # Captura os dados submetidos para repopular

        # Validação (similar à create view)
        if not cadastro_id:
            errors['cadastro'] = "O militar é obrigatório."
        else:
            try:
                cadastro_obj = Cadastro.objects.get(pk=cadastro_id)
            except Cadastro.DoesNotExist:
                errors['cadastro'] = "Militar inválido."

        if not honraria:
            errors['honraria'] = "A honraria é obrigatória."
        elif honraria not in [choice[0] for choice in honraria_choices]:
            errors['honraria'] = "Honraria selecionada inválida."

        data_publicacao_lp = None
        if data_publicacao_lp_str:
            try:
                data_publicacao_lp = datetime.datetime.strptime(data_publicacao_lp_str, '%Y-%m-%d').date()
            except ValueError:
                errors['data_publicacao_lp'] = "Formato de data inválido. Use AAAA-MM-DD."

        if not errors:
            try:
                # Atualiza os campos do objeto medalha
                medalha.cadastro = cadastro_obj
                medalha.honraria = honraria
                medalha.bol_g_pm_lp = bol_g_pm_lp if bol_g_pm_lp else None
                medalha.data_publicacao_lp = data_publicacao_lp
                medalha.observacoes = observacoes if observacoes else None
                medalha.usuario_alteracao = request.user
                medalha.save() # Salva as alterações
                messages.success(request, "Medalha atualizada com sucesso!")
                return redirect('cursos:medalha_list')
            except Exception as e:
                messages.error(request, f"Erro ao atualizar medalha: {e}")
        else:
            messages.error(request, "Por favor, corrija os erros no formulário.")

    context = {
        'medalha': medalha,  # Passa o objeto medalha existente para preencher os valores iniciais
        'cadastros': cadastros,
        'honraria_choices': honraria_choices,
        'title': "Editar Medalha",
        'errors': errors,
        'submitted_data': submitted_data, # Usado para repopular o form em caso de erro no POST
    }
    # Corrigido o caminho do template para 'cursos/medalha_form.html'
    return render(request, 'cursos/medalha_form.html', context)

# --- Delete View ---
@login_required
def medalha_delete(request, pk):
    """
    Permite a exclusão de uma medalha.
    """
    medalha = get_object_or_404(Medalha, pk=pk) # Obtém a medalha ou retorna 404

    if request.method == 'POST':
        try:
            medalha.delete()
            messages.success(request, "Medalha excluída com sucesso!")
            return redirect('cursos:medalha_list')
        except ProtectedError:
            # Captura erro se o objeto estiver relacionado a outros que impedem a exclusão
            messages.error(request, "Não é possível excluir esta medalha, pois ela está protegida por relacionamentos.")
        except Exception as e:
            messages.error(request, f"Erro ao excluir medalha: {e}")

    context = {
        'medalha': medalha, # Passa o objeto para o template para mensagem de confirmação
        'title': "Confirmar Exclusão"
    }
    # Corrigido o caminho do template para 'cursos/medalha_confirm_delete.html'
    return render(request, 'cursos/medalha_confirm_delete.html', context)



from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.messages import constants
from django.contrib.auth.decorators import login_required
from backend.efetivo.models import Cadastro, DetalhesSituacao, Promocao, Imagem


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
                constants.WARNING,
                'Por favor, informe o RE para buscar.', 
                extra_tags='bg-yellow-500 text-white p-4 rounded'
            )
            return render(request, template_name, {
                'honraria_choices': Medalha.HONRARIA_CHOICES,
            })

        try:
            # Busca o cadastro principal
            cadastro = Cadastro.objects.get(re=re)

            # Busca os dados relacionados usando as relações reversas
            promocao = Promocao.objects.filter(cadastro=cadastro).order_by('-id').first()
            detalhes = DetalhesSituacao.objects.filter(cadastro=cadastro).order_by('-id').first()
            imagem = Imagem.objects.filter(cadastro=cadastro).order_by('-id').first()

            # Prepara os dados essenciais com fallback para "Não informado"
            posto_grad = promocao.posto_grad if promocao else "Não informado"
            sgb = detalhes.sgb if detalhes else "Não informado"
            posto_secao = detalhes.posto_secao if detalhes else "Não informado"

            # Adiciona mensagens informativas se dados importantes não forem encontrados
            if not detalhes:
                messages.info(
                    request, 
                    'Atenção: Dados de SGB e Posto/Seção não encontrados.', 
                    extra_tags='bg-blue-500 text-white p-4 rounded'
                )
            if not promocao:
                messages.info(
                    request, 
                    'Atenção: Dados de Posto/Graduação não encontrados.', 
                    extra_tags='bg-blue-500 text-white p-4 rounded'
                )
            if not imagem:
                messages.info(
                    request, 
                    'Atenção: Foto de perfil não encontrada.', 
                    extra_tags='bg-blue-500 text-white p-4 rounded'
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
                constants.ERROR, 
                f'Militar com RE {re} não encontrado.', 
                extra_tags='bg-red-500 text-white p-4 rounded'
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
                extra_tags='bg-red-500 text-white p-4 rounded'
            )
            return render(request, template_name, {
                'honraria_choices': Medalha.HONRARIA_CHOICES,
            })

    # GET request - Mostra formulário vazio
    return render(request, template_name, {
        'honraria_choices': Medalha.HONRARIA_CHOICES,
    })




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
    context = {
        'cursos': cursos,
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

@login_required
def curso_update(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    cadastro = curso.militar # Get the associated Cadastro object

    detalhes_obj = DetalhesSituacao.objects.filter(militar=cadastro).first()
    promocao_obj = Promocao.objects.filter(militar=cadastro).first()
    imagem_obj = Imagem.objects.filter(militar=cadastro).first()

    context = {
        'curso': curso,
        'cadastro': cadastro,
        'detalhes': {
            'sgb': detalhes_obj.sgb if detalhes_obj else "Não informado",
            'posto_secao': detalhes_obj.posto_secao if detalhes_obj else "Não informado"
        },
        'promocao': {
            'posto_grad': promocao_obj.posto_grad if promocao_obj else "Não informado"
        },
        'imagem': imagem_obj,
        'curso_choices': CURSO_CHOICES, # Pass choices for the select field
    }

    if request.method == 'POST':
        # Assuming you're manually handling form fields, but a Django Form is highly recommended
        curso_type = request.POST.get('curso')
        data_publicacao = request.POST.get('data_publicacao')
        bol_publicacao = request.POST.get('bol_publicacao')
        observacoes = request.POST.get('observacoes')

        errors = {}
        if not curso_type:
            errors['curso'] = ['Este campo é obrigatório.']
        if not data_publicacao:
            errors['data_publicacao'] = ['Este campo é obrigatório.']
        if not bol_publicacao:
            errors['bol_publicacao'] = ['Este campo é obrigatório.']

        if errors:
            context['errors'] = errors
            # To re-populate fields in case of error
            context['curso'].curso = curso_type
            context['curso'].data_publicacao = data_publicacao
            context['curso'].bol_publicacao = bol_publicacao
            context['curso'].observacoes = observacoes

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                html_form = render_to_string('cursos/_curso_edit_form_partial.html', context, request=request)
                return JsonResponse({'status': 'error', 'message': 'Erro de validação.', 'html_form': html_form})
            else:
                messages.error(request, 'Erro ao atualizar o curso. Verifique os campos.')
                return render(request, 'cursos/curso_form.html', context) # Fallback for non-AJAX

        # If validation passes
        curso.curso = curso_type
        curso.data_publicacao = data_publicacao
        curso.bol_publicacao = bol_publicacao
        curso.observacoes = observacoes
        curso.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': 'Curso atualizado com sucesso!'})
        messages.success(request, 'Curso atualizado com sucesso!')
        return redirect('cursos:curso_list')

    else: # GET request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # This is an AJAX request from the modal, render only the partial content
            return render(request, 'cursos/_curso_edit_form_partial.html', context)
        else:
            # This is a regular GET request (e.g., direct navigation), render the full page
            return render(request, 'cursos/curso_form.html', context)

@login_required
def curso_delete(request, pk):
    curso = get_object_or_404(Curso, pk=pk)

    if request.method == 'POST':
        try:
            curso.delete()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success', 'message': 'Curso excluído com sucesso!'})
            messages.success(request, 'Curso excluído com sucesso!')
            return redirect('cursos:curso_list')
        except ProtectedError:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'Não é possível excluir este curso pois existem outras entidades que dependem dele.'})
            messages.error(request, 'Não é possível excluir este curso pois existem outras entidades que dependem dele.')
            return redirect('cursos:curso_list') # Or wherever you want to redirect
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': f'Erro ao excluir o curso: {str(e)}'})
            messages.error(request, f'Erro ao excluir o curso: {str(e)}')
            return redirect('cursos:curso_list') # Or wherever you want to redirect
    else:
        # For GET requests, you might want to show a confirmation page
        # For this modal approach, we expect POST from the JS confirmation
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
             return JsonResponse({'status': 'error', 'message': 'Requisição inválida. Use POST para exclusão.'}, status=405)
        else:
            # You might want to render a simple confirmation page here
            return render(request, 'cursos/curso_confirm_delete.html', {'curso': curso})


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