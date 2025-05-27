
from django.shortcuts import render, redirect, get_object_or_404
from .models import Cadastro, DetalhesSituacao, Promocao, Imagem, HistoricoDetalhesSituacao, HistoricoPromocao, CatEfetivo, HistoricoCatEfetivo
from django.contrib import messages
from django.contrib.messages import constants
from django.contrib.auth.decorators import login_required
from django.db.models import OuterRef, Subquery, Count
from django.utils import timezone
from django.db import IntegrityError
from django.db import transaction
from backend.rpt.models import Cadastro_rpt
from django.http import HttpResponseForbidden
from django.db.models import F, Window
from django.db.models.functions import RowNumber
from backend.municipios.models import Posto
import sys
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin # Added this import
from django.db.models import Prefetch
from backend.cursos.models import Medalha,Curso
import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password

logger = logging.getLogger(__name__)


@login_required
def cadastrar_militar(request):
    if request.method == "GET":
        context = {
            'posto_grad': Promocao.posto_grad_choices,
            'quadro': Promocao.quadro_choices,
            'grupo': Promocao.grupo_choices,
            'sgb': DetalhesSituacao.sgb_choices,
            'posto_secao': DetalhesSituacao.posto_secao_choices,
            'esta_adido': DetalhesSituacao.esta_adido_choices,
            'funcao': DetalhesSituacao.funcao_choices,
            'op_adm': DetalhesSituacao.op_adm_choices,
            'prontidao': DetalhesSituacao.prontidao_choices,
            'genero': Cadastro.genero_choices,
            'situacao': DetalhesSituacao.situacao_choices,
            'alteracao': Cadastro.alteracao_choices,
        }
        return render(request, 'cadastrar_militar.html', context)

    elif request.method == "POST":
        cpf = request.POST.get('cpf')
        if Cadastro.objects.filter(cpf=cpf).exists():
            messages.error(request, 'Erro: CPF já cadastrado.', extra_tags='bg-red-500 text-white p-4 rounded')
            return redirect('/efetivo/cadastrar_militar')

        try:
            with transaction.atomic():
                # Criar cadastro básico
                cadastro = Cadastro(
                    re=request.POST.get('re'),
                    dig=request.POST.get('dig'),
                    nome=request.POST.get('nome'),
                    nome_de_guerra=request.POST.get('nome_de_guerra'),
                    genero=request.POST.get('genero'),
                    nasc=request.POST.get('nasc'),
                    matricula=request.POST.get('matricula'),
                    admissao=request.POST.get('admissao'),
                    previsao_de_inatividade=request.POST.get('previsao_de_inatividade'),
                    cpf=cpf,
                    rg=request.POST.get('rg'),
                    tempo_para_averbar_inss=request.POST.get('tempo_para_averbar_inss'),
                    tempo_para_averbar_militar=request.POST.get('tempo_para_averbar_militar'),
                    email=request.POST.get('email'),
                    telefone=request.POST.get('telefone'),
                    alteracao=request.POST.get('alteracao'),
                    user=request.user,
                )
                cadastro.save()
                print(f"Cadastro básico salvo com sucesso - ID: {cadastro.id}")

                # Salvar imagem se existir
                if request.FILES.get('image'):
                    imagem = Imagem.objects.create(
                        cadastro=cadastro,
                        image=request.FILES.get('image'),
                        user=request.user
                    )
                    print(f"Imagem salva com sucesso - ID: {imagem.id}")

                # Criar situação funcional
                apresentacao_na_unidade = request.POST.get('apresentacao_na_unidade')
                detalhes = DetalhesSituacao(
                    cadastro=cadastro,
                    situacao=request.POST.get('situacao', 'Efetivo'),
                    sgb=request.POST.get('sgb'),
                    posto_secao=request.POST.get('posto_secao'),
                    esta_adido=request.POST.get('esta_adido'),
                    funcao=request.POST.get('funcao'),
                    op_adm=request.POST.get('op_adm'),
                    prontidao=request.POST.get('prontidao'),
                    apresentacao_na_unidade=apresentacao_na_unidade,
                    saida_da_unidade=request.POST.get('saida_da_unidade'),
                    usuario_alteracao=request.user
                )
                detalhes.save()
                print(f"DetalhesSituacao salvo com sucesso - ID: {detalhes.id}")

                # Criar promoção
                promocao = Promocao(
                    cadastro=cadastro,
                    posto_grad=request.POST.get('posto_grad'),
                    quadro=request.POST.get('quadro'),
                    grupo=request.POST.get('grupo'),
                    ultima_promocao=request.POST.get('ultima_promocao'),
                    usuario_alteracao=request.user
                )
                promocao.save()
                print(f"Promoção salva com sucesso - ID: {promocao.id}")

                # Criar categoria de efetivo
                cat_efetivo = CatEfetivo.objects.create(
                    cadastro=cadastro,
                    tipo="ATIVO",  # Sempre ATIVO no cadastro inicial
                    data_inicio=apresentacao_na_unidade,
                    usuario_cadastro=request.user,
                    ativo=True
                )
                print(f"CatEfetivo salvo com sucesso - ID: {cat_efetivo.id}")

                messages.success(request, 'Militar cadastrado com sucesso', extra_tags='bg-green-500 text-white p-4 rounded')
                return redirect('/efetivo/cadastrar_militar')

        except IntegrityError as e:
            print(f"Erro de integridade: {str(e)}", file=sys.stderr)
            messages.error(request, f'Erro: Dados inválidos ou duplicados. Detalhes: {str(e)}', extra_tags='bg-red-500 text-white p-4 rounded')
        except Exception as e:
            print(f"Erro geral: {str(e)}", file=sys.stderr)
            messages.error(request, f'Erro ao cadastrar militar: {str(e)}', extra_tags='bg-red-500 text-white p-4 rounded')

        return redirect('/efetivo/cadastrar_militar')

@login_required
def listar_militar(request):
    if request.method == "GET":
        # Otimização das queries com prefetch_related
        cadastros = Cadastro.objects.prefetch_related(
            Prefetch(
                'categorias_efetivo',
                queryset=CatEfetivo.objects.filter(ativo=True),
                to_attr='categorias_ativas'
            ),
            'imagens',
            'promocoes',
            'detalhes_situacao'
        ).annotate(
            latest_posto_grad=Subquery(
                Promocao.objects.filter(
                    cadastro=OuterRef('pk')
                ).order_by('-ultima_promocao').values('posto_grad')[:1]
            )
        ).order_by('latest_posto_grad')

        context = {
            'cadastros': cadastros,
            'current_date': timezone.now().date()  # Adiciona data atual ao contexto
        }
        
        return render(request, 'listar_militar.html', context)
    

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F, Window
from django.db.models.functions import RowNumber
from django.utils import timezone
from backend.efetivo.models import Cadastro, DetalhesSituacao, Promocao, CatEfetivo

class RestricaoHelper:
    @staticmethod
    def get_regra_principal(sigla):
        regras_map = {
            # Grupo 5.2.1
            'BS': '5.2.1', 'CI': '5.2.1', 'DV': '5.2.1', 'EF': '5.2.1',
            'FO': '5.2.1', 'IS': '5.2.1', 'LP': '5.2.1', 'MA': '5.2.1',
            'MC': '5.2.1', 'MG': '5.2.1', 'OU': '5.2.1', 'PO': '5.2.1',
            'PQ': '5.2.1', 'SA': '5.2.1', 'SE': '5.2.1', 'SH': '5.2.1',
            'SM': '5.2.1', 'SP': '5.2.1',
            # Grupo 5.2.2
            'AU': '5.2.2', 'EP': '5.2.2', 'ES': '5.2.2',
            'LR': '5.2.2', 'PT': '5.2.2', 'VP': '5.2.2',
            # Demais grupos
            'SN': '5.2.3',
            'SG': '5.2.4',
            'UA': '5.2.5',
            'UU': '5.2.6', 'CC': '5.2.6', 'CB': '5.2.6',
            'UB': '5.2.7', 'UC': '5.2.7', 'US': '5.2.7',
            'DG': '5.2.8', 'EM': '5.2.8', 'LS': '5.2.8',
            'MP': '5.2.8', 'SB': '5.2.8', 'SI': '5.2.8', 'ST': '5.2.8'
        }
        return regras_map.get(sigla, '')
    
from backend.cursos.models import Medalha,Curso


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from backend.efetivo.models import Cadastro, DetalhesSituacao, CatEfetivo, Promocao
from backend.cursos.models import Curso, Medalha
import logging

logger = logging.getLogger(__name__)

@login_required
def ver_militar(request, id):
    try:
        if not id:
            messages.error(request, 'ID inválido', extra_tags='bg-red-500 text-white p-4 rounded')
            return redirect('efetivo:listar_militar')

        # Obter o cadastro principal com related objects
        cadastro = Cadastro.objects.select_related(
            'user'
        ).prefetch_related(
            'imagens',
            'promocoes',
            'detalhes_situacao',
            'categorias_efetivo',
            'cadastro_rpt'
        ).get(id=id)

        today = timezone.now().date()
        detalhes = cadastro.detalhes_situacao.last()
        promocao = cadastro.promocoes.last()
        categoria_atual = cadastro.categorias_efetivo.filter(ativo=True).first()

        # Processar Restrições
        MENSAGENS_RESTRICOES = {
            # ... (mantenha o dicionário de restrições original)
        }

        restricoes_aplicaveis = []
        if categoria_atual and categoria_atual.tipo == 'RESTRICAO':
            for field in CatEfetivo._meta.get_fields():
                if field.name.startswith('restricao_') and getattr(categoria_atual, field.name):
                    sigla = field.name.split('_')[-1].upper()
                    if sigla in MENSAGENS_RESTRICOES:
                        restricoes_aplicaveis.append({
                            'sigla': sigla,
                            'nome': field.verbose_name,
                            'mensagem': MENSAGENS_RESTRICOES[sigla],
                            'regra': RestricaoHelper.get_regra_principal(sigla)
                        })

        # Status da Categoria
        categoria_status = {}
        if categoria_atual:
            if categoria_atual.tipo != 'ATIVO' and categoria_atual.data_termino and categoria_atual.data_termino < today:
                categoria_status = {
                    'texto': f"{categoria_atual.get_tipo_display()} (Expirado)",
                    'classe': 'bg-red-100 text-red-800',
                    'icone': 'fa-exclamation-triangle'
                }
            elif categoria_atual.tipo != 'ATIVO':
                categoria_status = {
                    'texto': f"{categoria_atual.get_tipo_display()} (Até {categoria_atual.data_termino.strftime('%d/%m/%Y') if categoria_atual.data_termino else 'Indefinido'})",
                    'classe': 'bg-yellow-100 text-yellow-800',
                    'icone': 'fa-info-circle'
                }
            else:
                categoria_status = {
                    'texto': categoria_atual.get_tipo_display(),
                    'classe': 'bg-green-100 text-green-800',
                    'icone': 'fa-check-circle'
                }
            categoria_atual.status_display = categoria_status

        # Lógica para cursos especiais
        cursos_especiais = []
        if detalhes and detalhes.op_adm:
            tag_desejada = 'Administrativo' if detalhes.op_adm == 'Administrativo' else 'Operacional'
            
            # Filtra os cursos usando o mapeamento de tags
            cursos_filtrados = []
            for curso in Curso.objects.filter(cadastro=cadastro):
                if Curso.CURSOS_TAGS.get(curso.curso) == tag_desejada:
                    cursos_filtrados.append(curso.get_curso_display())
            
            # Remove duplicatas mantendo a ordem
            cursos_especiais = list(dict.fromkeys(cursos_filtrados))

        # Dados relacionados
        medalhas_do_militar = Medalha.objects.filter(cadastro=cadastro).order_by('-data_publicacao_lp')
        cursos_do_militar = Curso.objects.filter(cadastro=cadastro).order_by('-data_publicacao')
        
        # Dados RPT
        cadastro_rpt = cadastro.cadastro_rpt.first()
        count_in_section = Cadastro_rpt.objects.filter(
            posto_secao_destino=cadastro_rpt.posto_secao_destino,
            status='Aguardando'
        ).count() if cadastro_rpt else 0

        context = {
            'cadastro': cadastro,
            'detalhes': detalhes,
            'promocao': promocao,
            'today': today,
            'categoria_atual': categoria_atual,
            'restricoes_aplicaveis': restricoes_aplicaveis,
            'medalhas_do_militar': medalhas_do_militar,
            'cursos_do_militar': cursos_do_militar,
            'cadastro_rpt': cadastro_rpt,
            'count_in_section': count_in_section,
            'cursos_especiais': cursos_especiais,
            # Choices
            'situacao_choices': DetalhesSituacao.situacao_choices,
            'sgb_choices': DetalhesSituacao.sgb_choices,
            'posto_secao_choices': DetalhesSituacao.posto_secao_choices,
            'esta_adido_choices': DetalhesSituacao.esta_adido_choices,
            'funcao_choices': DetalhesSituacao.funcao_choices,
            'op_adm_choices': DetalhesSituacao.op_adm_choices,
            'prontidao_choices': DetalhesSituacao.prontidao_choices,
            'posto_grad_choices': Promocao.posto_grad_choices,
            'quadro_choices': Promocao.quadro_choices,
            'grupo_choices': Promocao.grupo_choices,
            'genero_choices': Cadastro.genero_choices,
            'alteracao_choices': Cadastro.alteracao_choices,
            'categoria_choices': CatEfetivo.TIPO_CHOICES,
        }

        return render(request, 'ver_militar.html', context)

    except Cadastro.DoesNotExist:
        messages.error(request, 'Militar não encontrado', extra_tags='bg-red-500 text-white p-4 rounded')
        return redirect('efetivo:listar_militar')
        
    except Exception as e:
        logger.error(f"Erro ao acessar militar ID {id}: {str(e)}")
        messages.error(request, 'Erro interno ao carregar os dados', extra_tags='bg-red-500 text-white p-4 rounded')
        return redirect('efetivo:listar_militar')
    

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password

@login_required
def excluir_militar(request, id):
    if request.method == 'POST':
        try:
            # Obter objetos relevantes
            cadastro = Cadastro.objects.get(id=id)
            current_user = request.user
            
            # Verificar senha
            password = request.POST.get('password', '')
            if not check_password(password, current_user.password):
                messages.add_message(request, constants.ERROR, 'Senha incorreta! Operação cancelada.', 
                                  extra_tags='bg-red-500 text-white p-4 rounded delete_error')  # Adicione 'delete_error'
                return redirect('efetivo:ver_militar', id=id)
            
            # Realizar exclusão
            cadastro.delete()
            messages.add_message(request, constants.SUCCESS, 'Cadastro excluído com sucesso.', 
                              extra_tags='bg-green-500 text-white p-4 rounded')
            return redirect('efetivo:listar_militar')
            
        except Cadastro.DoesNotExist:
            messages.add_message(request, constants.ERROR, 'Militar não encontrado!.', 
                              extra_tags='bg-red-500 text-white p-4 rounded')
            return redirect('efetivo:listar_militar')
        except Exception as e:
            messages.add_message(request, constants.ERROR, f'Erro ao excluir: {str(e)}', 
                              extra_tags='bg-red-500 text-white p-4 rounded delete_error')  # Adicione 'delete_error'
            return redirect('efetivo:ver_militar', id=id)
    
    return redirect('efetivo:listar_militar')


# responsável pela edição da model promoções
@login_required
def editar_posto_graduacao(request, id):
    cadastro = get_object_or_404(Cadastro, id=id)
    promocao_atual = cadastro.promocoes.last()

    if request.method == "GET":
        return render(request, 'editar_posto_graduacao.html', {
            'cadastro': cadastro,
            'promocao': promocao_atual,
            'posto_grad': Promocao.posto_grad_choices,
            'quadro': Promocao.quadro_choices,
            'grupo': Promocao.grupo_choices,
        })

    elif request.method == "POST":
        ultima_promocao = request.POST.get('ultima_promocao')
        posto_grad = request.POST.get('posto_grad')
        quadro = request.POST.get('quadro')
        grupo = request.POST.get('grupo')

        if not ultima_promocao:
         return redirect('editar_posto_graduacao', id=cadastro.id)

        if promocao_atual:
            HistoricoPromocao.objects.create(
                cadastro=cadastro,
                posto_grad=promocao_atual.posto_grad,
                quadro=promocao_atual.quadro,
                grupo=promocao_atual.grupo,
                ultima_promocao=promocao_atual.ultima_promocao,
                usuario_alteracao=request.user,
                data_alteracao=timezone.now()
            )

        nova_promocao = Promocao(
        cadastro=cadastro,
        posto_grad=posto_grad,
        quadro=quadro,
        grupo=grupo,
        ultima_promocao=ultima_promocao,
        usuario_alteracao=request.user
    )
    nova_promocao.save()
    messages.add_message(request, constants.SUCCESS, 'Dados de Posto e Graduação atualizados com sucesso.', extra_tags='bg-green-500 text-white p-4 rounded')
    return redirect('efetivo:ver_militar', id=cadastro.id)
        

from django.http import JsonResponse

@login_required
def editar_situacao_atual(request, id):
    if request.method == 'POST':
        cadastro = get_object_or_404(Cadastro, id=id)
        
        try:
            # Atualizar categoria existente ou criar nova
            categoria = CatEfetivo.objects.filter(cadastro=cadastro, ativo=True).first()
            
            if categoria:
                # Desativar categoria atual
                categoria.ativo = False
                categoria.save()
                
                # Criar registro no histórico
                HistoricoCatEfetivo.objects.create(
                    cat_efetivo=categoria,
                    tipo=categoria.tipo,
                    data_inicio=categoria.data_inicio,
                    data_termino=timezone.now().date(),
                    ativo=False,
                    observacao=categoria.observacao,
                    usuario_alteracao=request.user
                )
            
            # Criar nova categoria
            nova_categoria = CatEfetivo(
                cadastro=cadastro,
                tipo=request.POST['cat_efetivo'],
                data_inicio=timezone.now().date(),
                usuario_cadastro=request.user,
                ativo=True
            )
            nova_categoria.save()
            
            return JsonResponse({'success': True})

        except Exception as e:
            print(f"Erro ao salvar a situação atual: {e}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método de requisição inválido.'})

@login_required
def cadastrar_nova_situacao(request, id):
    if request.method == 'POST':
        cadastro = get_object_or_404(Cadastro, id=id)
        
        try:
            # Criar Nova Situação
            nova_situacao = DetalhesSituacao(
                cadastro=cadastro,
                situacao=request.POST['situacao'],
                sgb=request.POST['sgb'],
                posto_secao=request.POST['posto_secao'],
                esta_adido=request.POST['esta_adido'],
                funcao=request.POST['funcao'],
                op_adm=request.POST['op_adm'],
                prontidao=request.POST.get('prontidao'),
                apresentacao_na_unidade=request.POST['apresentacao_na_unidade'],
                saida_da_unidade=request.POST.get('saida_da_unidade', None),
                usuario_alteracao=request.user,
            )
            nova_situacao.save()
            
            # Criar/Atualizar categoria
            categoria = CatEfetivo.objects.filter(cadastro=cadastro, ativo=True).first()
            if categoria:
                categoria.ativo = False
                categoria.save()
                
                HistoricoCatEfetivo.objects.create(
                    cat_efetivo=categoria,
                    tipo=categoria.tipo,
                    data_inicio=categoria.data_inicio,
                    data_termino=timezone.now().date(),
                    ativo=False,
                    usuario_alteracao=request.user
                )
            
            nova_categoria = CatEfetivo(
                cadastro=cadastro,
                tipo=request.POST.get('cat_efetivo', 'ATIVO'),
                data_inicio=request.POST['apresentacao_na_unidade'],
                usuario_cadastro=request.user,
                ativo=True
            )
            nova_categoria.save()
            
            # Atualizar o Histórico de Detalhes da Situação
            HistoricoDetalhesSituacao.objects.create(
                cadastro=cadastro,
                situacao=nova_situacao.situacao,
                sgb=nova_situacao.sgb,
                posto_secao=nova_situacao.posto_secao,
                esta_adido=nova_situacao.esta_adido,
                funcao=nova_situacao.funcao,
                op_adm=nova_situacao.op_adm,
                prontidao= nova_situacao.prontidao,
                apresentacao_na_unidade=nova_situacao.apresentacao_na_unidade,
                saida_da_unidade=nova_situacao.saida_da_unidade,
                data_alteracao=nova_situacao.data_alteracao,
                usuario_alteracao=request.user,
                cat_efetivo=nova_situacao.cat_efetivo,
            )
         
            messages.add_message(request, constants.SUCCESS, 'Criada Nova Situação Funcional com sucesso.', 
            extra_tags='bg-green-500 text-white p-4 rounded')
            return redirect('efetivo:ver_militar', id=cadastro.id)

        except Exception as e:
            print(f"Erro ao cadastrar a nova situação: {e}")
            messages.add_message(request, constants.ERROR, 'Erro ao cadastrar nova situação.', 
                              extra_tags='bg-red-500 text-white p-4 rounded')  # SEM 'delete_error'
            return redirect('efetivo:ver_militar', id=cadastro.id)
    
    messages.add_message(request, constants.ERROR, 'Método de Requisição errado.', 
                      extra_tags='bg-red-500 text-white p-4 rounded')  # SEM 'delete_error'
    return redirect('efetivo:ver_militar', id=id)



from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import Cadastro, HistoricoPromocao, HistoricoDetalhesSituacao

@login_required
def editar_dados_pessoais_contatos(request, id):
    cadastro = get_object_or_404(Cadastro, id=id)

    # Carrega as choices diretamente do modelo
    genero_choices = Cadastro.genero_choices
    alteracao_choices = Cadastro.alteracao_choices

    if request.method == "POST":
        try:
            # Atualiza campos básicos
            campos = [
                're', 'dig', 'nome', 'nome_de_guerra', 'genero', 'nasc',
                'matricula', 'admissao', 'previsao_de_inatividade', 'cpf',
                'rg', 'tempo_para_averbar_inss', 'tempo_para_averbar_militar',
                'email', 'telefone', 'alteracao'
            ]

            for campo in campos:
                setattr(cadastro, campo, request.POST.get(campo))

            # Valida e salva
            cadastro.full_clean()
            cadastro.save()

            messages.success(request, 'Dados atualizados com sucesso!')
            return redirect('efetivo:ver_militar', id=cadastro.id)

        except ValidationError as e:
            messages.error(request, f'Erro de validação: {e}')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar dados: {str(e)}')

    # Carrega dados para o template
    context = {
        'cadastro': cadastro,
        'genero': genero_choices,
        'alteracao': alteracao_choices,
        'historico_promocoes': HistoricoPromocao.objects.filter(cadastro=cadastro).order_by('-data_alteracao'),
        'historico_detalhes_situacao': HistoricoDetalhesSituacao.objects.filter(cadastro=cadastro).order_by('-data_alteracao'),
    }

    print("Context being passed to the template:", context)  # Debugging line

    return render(request, 'editar_dados_pessoais_contatos.html', context)


@login_required
def editar_imagem(request, id):
    
    cadastro = get_object_or_404(Cadastro, id=id)

    if request.method == "POST":
        if request.FILES.get('image'):
            nova_imagem = Imagem(
                cadastro=cadastro,
                image=request.FILES.get('image'),
                user=request.user
            )
            nova_imagem.save()
            messages.add_message(request, constants.SUCCESS, 'Imagem atualizada com sucesso', extra_tags='bg-green-500 text-white p-4 rounded')
        else:
            messages.add_message(request, constants.ERROR, 'Por favor, envie uma imagem válida.', extra_tags='bg-red-500 text-white p-4 rounded')

        return redirect('efetivo:ver_militar', id=cadastro.id)

    return render(request, 'editar_imagem.html', {
        'cadastro': cadastro,
        'imagem': cadastro.imagens.last()
    })


# responsável por armazenar os dados de movimentação
@login_required
def historico_movimentacoes(request, id):
    cadastro = get_object_or_404(Cadastro, id=id)
    promocoes = Promocao.objects.filter(cadastro=cadastro).order_by('-data_alteracao')
    historico_detalhes_situacao = HistoricoDetalhesSituacao.objects.filter(cadastro=cadastro).order_by('-data_alteracao')

    return render(request, 'historico_movimentacoes.html', {
        'cadastro': cadastro,
        'promocoes': promocoes,
        'historico_detalhes_situacao': historico_detalhes_situacao,
    })


# responsável pela edição da model De
@login_required
def editar_situacao_funcional(request, id):
    cadastro = get_object_or_404(Cadastro, id=id)
    
    if request.method == 'POST':
        try:
            # Atualizar a Situação Atual
            cadastro.situacao = request.POST['situacao_atual']
            cadastro.save()
            
            # Criar Nova Situação
            nova_situacao = DetalhesSituacao(
                cadastro=cadastro,
                situacao=request.POST['situacao'],
                sgb=request.POST['sgb'],
                posto_secao=request.POST['posto_secao'],
                esta_adido=request.POST['esta_adido'],
                funcao=request.POST['funcao'],
                op_adm=request.POST['op_adm'],
                apresentacao_na_unidade=request.POST['apresentacao_na_unidade'],
                saida_da_unidade=request.POST.get('saida_da_unidade', None),
                cat_efetivo=request.POST('cat_efetivo'),
            )
            nova_situacao.save()
            
            # Atualizar o Histórico de Detalhes da Situação
            HistoricoDetalhesSituacao.objects.create(
                cadastro=cadastro,
                situacao=nova_situacao.situacao,
                sgb=nova_situacao.sgb,
                posto_secao=nova_situacao.posto_secao,
                esta_adido=nova_situacao.esta_adido,
                funcao=nova_situacao.funcao,
                op_adm=nova_situacao.op_adm,
                apresentacao_na_unidade=nova_situacao.apresentacao_na_unidade,
                saida_da_unidade=nova_situacao.saida_da_unidade,
                data_alteracao=nova_situacao.data_alteracao,
                usuario_alteracao=request.user,
                cat_efetivo=nova_situacao.cat_efetivo,
            )
            messages.add_message(request, constants.SUCCESS, 'Situação funcional atualizada com sucesso!', extra_tags='bg-green-500 text-white p-4 rounded')

        except Exception as e:
            messages.add_message(request, constants.SUCCESS, 'Dados de Posto e Graduação atualizados com sucesso.', extra_tags='bg-green-500 text-white p-4 rounded')
            messages.error(request, f'Ocorreu um erro ao atualizar a situação funcional: {e}', extra_tags='bg-red-500 text-white p-4 rounded')

          # Permanecer na mesma URL após salvar
        return redirect('editar_situacao_funcional', id=id)
        
    # Renderizar o formulário de edição com os dados atuais
    return render(request, 'editar_situacao_funcional.html', {
        'cadastro': cadastro,
        'situacao': DetalhesSituacao.objects.all(),
        'sgb_choices': DetalhesSituacao._meta.get_field('sgb').choices,
        'posto_secao_choices': DetalhesSituacao._meta.get_field('posto_secao').choices,
        'esta_adido_choices': DetalhesSituacao._meta.get_field('esta_adido').choices,
        'funcao_choices': DetalhesSituacao._meta.get_field('funcao').choices,
        'op_adm_choices': DetalhesSituacao._meta.get_field('op_adm').choices,
        'cat_efetivo': DetalhesSituacao._meta.get_field('cat_efetivo').choices,
        'detalhes': cadastro.detalhes_situacao.last()
    })


from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from backend.rpt.models import Cadastro_rpt
from backend.efetivo.models import Cadastro

@login_required
def check_rpt(request, id):
    cadastro = get_object_or_404(Cadastro, id=id)
    exists = Cadastro_rpt.objects.filter(cadastro=cadastro).exists()
    return JsonResponse({'exists': exists})

# backend/efetivo/views.py
# backend/efetivo/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Q
from .models import Cadastro, Imagem, Promocao, DetalhesSituacao
from backend.municipios.models import Posto
from datetime import datetime

@login_required
def detalhar_efetivo(request, posto_id):
    posto = get_object_or_404(Posto, pk=posto_id)
    
    # Ordem hierárquica dos postos/grads
    ORDEM_POSTOS = [
        "Cel PM", "Ten Cel PM", "Maj PM", "CAP PM",
        "1º Ten PM", "1º Ten QAPM", "2º Ten PM", "2º Ten QAPM", "Asp OF PM",
        "Subten PM", "1º Sgt PM", "2º Sgt PM", "3º Sgt PM",
        "Cb PM", "Sd PM", "Sd PM 2ºCL"
    ]
    
    # Obtém o prefixo do posto_secao (7 primeiros dígitos)
    posto_secao_prefixo = posto.posto_secao[:7]
    
    # Otimizando as consultas
    militares_queryset = Cadastro.objects.filter(
        Q(detalhes_situacao__posto_secao=posto.posto_secao) |
        Q(detalhes_situacao__funcao="CMT_PB", detalhes_situacao__posto_secao__startswith=posto_secao_prefixo)
    ).select_related(
        'user'
    ).prefetch_related(
        Prefetch('imagens', queryset=Imagem.objects.all().order_by('-create_at')),
        Prefetch('promocoes', queryset=Promocao.objects.all().order_by('-ultima_promocao')),
        Prefetch('detalhes_situacao', queryset=DetalhesSituacao.objects.all().order_by('-data_alteracao')),
        Prefetch('categorias_efetivo', queryset=CatEfetivo.objects.filter(ativo=True))
    ).distinct()
    
    # Converter QuerySet para lista para poder ordenar
    militares = list(militares_queryset)
    
    # Função para ordenação
    def get_ordenacao(militar):
        ultima_promocao = militar.promocoes.first()
        if ultima_promocao:
            posto_grad = ultima_promocao.posto_grad
            try:
                ordem_posto = ORDEM_POSTOS.index(posto_grad)
            except ValueError:
                ordem_posto = len(ORDEM_POSTOS)
            data_promocao = ultima_promocao.ultima_promocao or datetime.min.date()
        else:
            ordem_posto = len(ORDEM_POSTOS)
            data_promocao = datetime.min.date()
        
        return (ordem_posto, -data_promocao.toordinal())
    
    # Ordenar os militares
    militares.sort(key=get_ordenacao)
    
    # Obtém o comandante separadamente
    comandante = next(
        (m for m in militares if any(
            d.funcao == "CMT_PB" and d.posto_secao.startswith(posto_secao_prefixo)
            for d in m.detalhes_situacao.all()
        )),
        None
    )
    
    # Remover o comandante da lista de militares (se existir)
    if comandante:
        militares = [m for m in militares if m.id != comandante.id]
    
    # Adicionar categoria atual a cada militar
    for militar in militares:
        militar.categoria_atual = next(
            (c for c in militar.categorias_efetivo.all() if c.ativo), 
            None
        )
    
    if comandante:
        comandante.categoria_atual = next(
            (c for c in comandante.categorias_efetivo.all() if c.ativo), 
            None
        )

    context = {
        'posto': posto,
        'militares': militares,
        'comandante': comandante,
        'unidade_nome': posto.posto_secao,
        'posto_secao_prefixo': posto_secao_prefixo,
        'categoria_choices': CatEfetivo.TIPO_CHOICES,
    }
    return render(request, 'detalhes_efetivo.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Window, F
from django.db.models.functions import RowNumber
from django.db import transaction
from datetime import date
from .models import   Cadastro, DetalhesSituacao, Promocao,  CatEfetivo, HistoricoCatEfetivo

from django.utils import timezone


def historico_categorias(request, militar_id):
    militar = get_object_or_404(Cadastro, id=militar_id)
    historicos = HistoricoCatEfetivo.objects.filter(
        cat_efetivo__cadastro=militar
    ).select_related('cat_efetivo', 'usuario_alteracao').order_by('-data_registro')
    
    return render(request, 'historico_categorias.html', {
        'militar': militar,
        'historicos': historicos,
        'today': timezone.now().date(),
    })

# views.py
from django.utils import timezone
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from datetime import datetime


def parse_date(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None


def criar_historico(categoria, usuario):
    historico_data = {
        'cat_efetivo': categoria,
        'tipo': categoria.tipo,
        'data_inicio': categoria.data_inicio,
        'data_termino': categoria.data_termino,
        'observacao': categoria.observacao,
        'boletim_concessao_lsv': categoria.boletim_concessao_lsv,
        'data_boletim_lsv': categoria.data_boletim_lsv,
        'usuario_alteracao': usuario,
        'ativo': categoria.ativo
    }
    
    if categoria.tipo == 'RESTRICAO':
        campos_restricao = [f.name for f in CatEfetivo._meta.fields if f.name.startswith('restricao_')]
        historico_data.update({campo: getattr(categoria, campo) for campo in campos_restricao})
    
    HistoricoCatEfetivo.objects.create(**historico_data)


@login_required
def adicionar_categoria_efetivo(request, militar_id):
    militar = get_object_or_404(Cadastro, id=militar_id)
    today = timezone.now().date()

    if request.method == 'POST':
        form_data = request.POST.copy()
        tipo = form_data.get('tipo')

        if not tipo:
            messages.error(request, 'Tipo de categoria é obrigatório!')
            return redirect('efetivo:ver_militar', id=militar_id)

        try:
            with transaction.atomic():
                # Converter strings para date quando necessário
                data_inicio_str = form_data.get('data_inicio')
                data_termino_str = form_data.get('data_termino')
                data_boletim_lsv_str = form_data.get('data_boletim_lsv')

                data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date() if data_inicio_str else None
                data_termino = datetime.strptime(data_termino_str, '%Y-%m-%d').date() if data_termino_str else None
                data_boletim_lsv = datetime.strptime(data_boletim_lsv_str, '%Y-%m-%d').date() if data_boletim_lsv_str else None

                # Verificar se a data de término é anterior à data atual
                if data_termino and data_termino < today:
                    messages.warning(request, 'Data de término já expirada. Categoria será marcada como inativa.')
                    ativo = False
                else:
                    ativo = True

                # Criar nova categoria
                nova_categoria = CatEfetivo(
                    cadastro=militar,
                    tipo=tipo,
                    data_inicio=data_inicio,
                    data_termino=data_termino,
                    usuario_cadastro=request.user,
                    ativo=ativo,
                    observacao=form_data.get('observacao', '')
                )

                # Campos específicos para LSV
                if tipo == 'LSV':
                    nova_categoria.boletim_concessao_lsv = form_data.get('boletim_concessao_lsv', '')
                    nova_categoria.data_boletim_lsv = data_boletim_lsv

                # Campos de restrição (só aplica se for RESTRICAO)
                if tipo == 'RESTRICAO':
                    campos_restricao = [field.name for field in CatEfetivo._meta.get_fields() 
                                      if field.name.startswith('restricao_')]
                    for campo in campos_restricao:
                        setattr(nova_categoria, campo, campo in form_data)

                nova_categoria.save()

                # Criar registro no histórico
                historico_data = {
                    'cat_efetivo': nova_categoria,
                    'tipo': nova_categoria.tipo,
                    'data_inicio': nova_categoria.data_inicio,
                    'data_termino': nova_categoria.data_termino,
                    'observacao': nova_categoria.observacao,
                    'boletim_concessao_lsv': nova_categoria.boletim_concessao_lsv,
                    'data_boletim_lsv': nova_categoria.data_boletim_lsv,
                    'usuario_alteracao': request.user,
                    'ativo': nova_categoria.ativo
                }

                # Adiciona campos de restrição ao histórico se for do tipo RESTRICAO
                if tipo == 'RESTRICAO':
                    historico_data.update({campo: getattr(nova_categoria, campo) for campo in campos_restricao})

                HistoricoCatEfetivo.objects.create(**historico_data)

                messages.success(request, 'Categoria adicionada com sucesso!')
                return redirect('efetivo:ver_militar', id=militar_id)

        except Exception as e:
            messages.error(request, f'Erro ao adicionar categoria: {str(e)}')
            return redirect('efetivo:ver_militar', id=militar_id)

    # Se não for POST, redireciona para a página do militar
    return redirect('efetivo:ver_militar',id=militar_id)
  
  
  # views.py


# views.py (Atualização Final)


from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import transaction
from django.contrib import messages
from backend.efetivo.models import CatEfetivo, HistoricoCatEfetivo  # Certifique-se de que o caminho para seus modelos está correto

@login_required
@require_http_methods(["GET", "POST"])
def editar_categoria_efetivo(request, categoria_id):
    categoria = get_object_or_404(
        CatEfetivo.objects.select_related('cadastro'),
        id=categoria_id
    )
    eh_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        # ... (seu código POST existente) ...
        pass
    else:  # GET request
        # Criar um dicionário serializável com os dados necessários
        dados_categoria = {
            'id': categoria.id,
            'tipo': categoria.tipo,
            'tipo_display': categoria.get_tipo_display(),
            'data_inicio': categoria.data_inicio.strftime('%Y-%m-%d') if categoria.data_inicio else None,
            'data_termino': categoria.data_termino.strftime('%Y-%m-%d') if categoria.data_termino else None,
            'observacao': categoria.observacao,
            'restricoes': []
        }

        if categoria.tipo == 'RESTRICAO':
            dados_categoria['restricoes'] = [
                {
                    'name': f.name,
                    'verbose_name': f.verbose_name,
                    'value': getattr(categoria, f.name)
                }
                for f in CatEfetivo._meta.fields 
                if f.name.startswith('restricao_')
            ]

        if eh_ajax:
            return JsonResponse(dados_categoria)
        else:
            return redirect('efetivo:historico_categorias', militar_id=categoria.cadastro.id)


            

@login_required
def excluir_categoria_efetivo(request, categoria_id):
    categoria = get_object_or_404(CatEfetivo, id=categoria_id)
    militar_id = categoria.cadastro.id
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Remove categoria e histórico relacionado
                HistoricoCatEfetivo.objects.filter(cat_efetivo=categoria).delete()
                categoria.delete()
                messages.success(request, 'Registro e histórico excluídos permanentemente!')
        except Exception as e:
            messages.error(request, f'Erro na exclusão: {str(e)}')
            
    return redirect('efetivo:historico_categorias', militar_id=militar_id)

# views.py
@login_required
def excluir_historico_categoria(request, historico_id):
    historico = get_object_or_404(HistoricoCatEfetivo, id=historico_id)
    militar_id = historico.cat_efetivo.cadastro.id
    
    if request.method == 'POST':
        historico.delete()
        messages.success(request, 'Histórico excluído permanentemente.')
    
    return redirect('efetivo:historico_categorias', militar_id=militar_id)


# backend/efetivo/views.py
from django.db.models import Count
from django.views.generic import ListView
from .models import Cadastro, DetalhesSituacao, Promocao # Confirm these imports are correct
from django.utils import timezone # Certifique-se de que está importado
# ... other imports you might have

class ListaMilitaresView(ListView):
    model = Cadastro
    template_name = 'lista_militares.html'
    context_object_name = 'militares'

    # Define your subgrupos_estrutura as a class attribute
    subgrupos_estrutura = {
        "EM": [
            {"codigo": "703150000", "nome": "CMT", "filhos": []},
            {"codigo": "703159000", "nome": "SUB CMT", "filhos": []},
            {"codigo": "703159100", "nome": "SEC ADM", "filhos": []},
            {"codigo": "703159110", "nome": "B/1 E B/5", "filhos": [
                {"codigo": "703159110-1", "nome": "B/5", "filhos": []}
            ]},
            {"codigo": "703159120", "nome": "AA", "filhos": []},
            {"codigo": "703159130", "nome": "B/3 E MOTOMEC", "filhos": [
                {"codigo": "703159130-1", "nome": "MOTOMEC", "filhos": []}
            ]},
            {"codigo": "703159131", "nome": "COBOM", "filhos": []},
            {"codigo": "703159140", "nome": "B/4", "filhos": []},
            {"codigo": "703159150", "nome": "ST UGE", "filhos": []},
            {"codigo": "703159160", "nome": "ST PJMD", "filhos": []},
            {"codigo": "703159200", "nome": "SEC ATIV TEC", "filhos": []}
        ],
        "1ºSGB": [
            {"codigo": "703151000", "nome": "CMT 1º SGB", "filhos": []},
            {"codigo": "703151100", "nome": "ADM PB CERRADO", "filhos": []},
            {"codigo": "703151101", "nome": "EB CERRADO", "filhos": []},
            {"codigo": "703151102", "nome": "EB ZONA NORTE", "filhos": []},
            {"codigo": "703151200", "nome": "ADM PB SANTA ROSÁLIA", "filhos": []},
            {"codigo": "703151201", "nome": "EB SANTA ROSÁLIA", "filhos": []},
            {"codigo": "703151202", "nome": "EB ÉDEM", "filhos": []},
            {"codigo": "703151300", "nome": "ADM PB VOTORANTIM", "filhos": []},
            {"codigo": "703151301", "nome": "EB VOTORANTIM", "filhos": []},
            {"codigo": "703151302", "nome": "EB PIEDADE", "filhos": []},
            {"codigo": "703151800", "nome": "ADM 1º SGB", "filhos": []}
        ],
        "2ºSGB": [
            {"codigo": "703152000", "nome": "CMT 2º SGB", "filhos": []},
            {"codigo": "703152100", "nome": "ADM PB ITU", "filhos": []},
            {"codigo": "703152101", "nome": "EB ITU", "filhos": []},
            {"codigo": "703152102", "nome": "EB PORTO FELIZ", "filhos": []},
            {"codigo": "703152200", "nome": "ADM PB SALTO", "filhos": []},
            {"codigo": "703152201", "nome": "EB SALTO", "filhos": []},
            {"codigo": "703152300", "nome": "ADM PB SÃO ROQUE", "filhos": []},
            {"codigo": "703152301", "nome": "EB SÃO ROQUE", "filhos": []},
            {"codigo": "703152302", "nome": "EB IBIÚNA", "filhos": []},
            {"codigo": "703152800", "nome": "ADM 2º SGB", "filhos": []},
            {"codigo": "703152900", "nome": "NUCL ATIV TEC 2º SGB", "filhos": []}
        ],
        "3ºSGB": [
            {"codigo": "703153000", "nome": "CMT 3º SGB", "filhos": []},
            {"codigo": "703153100", "nome": "ADM PB ITAPEVA", "filhos": []},
            {"codigo": "703153101", "nome": "EB ITAPEVA", "filhos": []},
            {"codigo": "703153102", "nome": "EB APIAÍ", "filhos": []},
            {"codigo": "703153103", "nome": "EB ITARARÉ", "filhos": []},
            {"codigo": "703153104", "nome": "EB CAPÃO BONITO", "filhos": []},
            {"codigo": "703153800", "nome": "ADM 3º SGB", "filhos": []},
            {"codigo": "703153900", "nome": "NUCL ATIV TEC 3º SGB", "filhos": []}
        ],
        "4ºSGB": [
            {"codigo": "703154000", "nome": "CMT 4º SGB", "filhos": []},
            {"codigo": "703154100", "nome": "ADM PB ITAPETININGA", "filhos": []},
            {"codigo": "703154101", "nome": "EB ITAPETININGA", "filhos": []},
            {"codigo": "703154102", "nome": "EB BOITUVA", "filhos": []},
            {"codigo": "703154103", "nome": "EB ANGATUBA", "filhos": []},
            {"codigo": "703154200", "nome": "ADM PB TATUÍ", "filhos": []},
            {"codigo": "703154201", "nome": "EB TATUÍ", "filhos": []},
            {"codigo": "703154202", "nome": "EB TIETÊ", "filhos": []},
            {"codigo": "703154203", "nome": "EB LARANJAL PAULISTA", "filhos": []},
            {"codigo": "703154800", "nome": "ADM 4º SGB", "filhos": []},
            {"codigo": "703154900", "nome": "NUCL ATIV TEC 4º SGB", "filhos": []}
        ],
        "5ºSGB": [
            {"codigo": "703155000", "nome": "CMT 5º SGB", "filhos": []},
            {"codigo": "703155100", "nome": "ADM PB BOTUCATU", "filhos": []},
            {"codigo": "703155101", "nome": "EB BOTUCATU", "filhos": []},
            {"codigo": "703155102", "nome": "EB ITATINGA", "filhos": []},
            {"codigo": "703155200", "nome": "ADM PB AVARÉ", "filhos": []},
            {"codigo": "703155201", "nome": "EB AVARÉ", "filhos": []},
            {"codigo": "703155202", "nome": "EB PIRAJU", "filhos": []},
            {"codigo": "703155203", "nome": "EB ITAÍ", "filhos": []},
            {"codigo": "703155800", "nome": "ADM 5º SGB", "filhos": []},
            {"codigo": "703155900", "nome": "NUCL ATIV TEC 5º SGB", "filhos": []}
        ]
    }


    def get_queryset(self):
        queryset = super().get_queryset()
        grupo_ativo = self.request.GET.get('grupo')
        subgrupo_ativo = self.request.GET.get('subgrupo')

        print(f"\n--- DEBUG get_queryset ---")
        print(f"Initial queryset count (before any filters): {queryset.count()}")
        print(f"Request: grupo_ativo={grupo_ativo}, subgrupo_ativo={subgrupo_ativo}")

        if subgrupo_ativo:
            queryset = queryset.filter(
                detalhes_situacao__posto_secao__startswith=subgrupo_ativo
            )
            print(f"Filtered by posto_secao (using __startswith with code): '{subgrupo_ativo}'")

        elif grupo_ativo:
            queryset = queryset.filter(
                detalhes_situacao__sgb=grupo_ativo
            )
            print(f"Filtered by grupo (SGB): '{grupo_ativo}'")
        else:
            print("No group or subgroup filter applied. Showing all.")


        queryset = queryset.distinct().prefetch_related(
            'detalhes_situacao',
            'imagens',
            'promocoes',
            'categorias_efetivo'
        ).order_by('re')

        print(f"Final queryset count (after filters and distinct): {queryset.count()}")
        print(f"--- END DEBUG get_queryset ---\n")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grupos = [
            ("EM", "Estado Maior"),
            ("1ºSGB", "1º Subgrupamento"),
            ("2ºSGB", "2º Subgrupamento"),
            ("3ºSGB", "3º Subgrupamento"),
            ("4ºSGB", "4º Subgrupamento"),
            ("5ºSGB", "5º Subgrupamento")
        ]

        grupo_ativo = self.request.GET.get('grupo')
        subgrupo_ativo = self.request.GET.get('subgrupo')

        # Função para calcular contagens recursivamente
        def calcular_contagens(estrutura):
            contagens = {}
            for item in estrutura:
                count = Cadastro.objects.filter(
                    detalhes_situacao__posto_secao=item['codigo']
                ).distinct().count()
                
                contagens[item['codigo']] = count
                
                if item['filhos']:
                    contagens.update(calcular_contagens(item['filhos']))
            return contagens

        # Calcular contagens para todos os grupos
        contagens_por_grupo = {}
        for grupo_key, _ in grupos:
            contagens_por_grupo[grupo_key] = calcular_contagens(
                self.subgrupos_estrutura.get(grupo_key, [])
            )


        context['contagens_por_grupo'] = contagens_por_grupo
        context['grupos'] = grupos
        

        grupo_ativo = self.request.GET.get('grupo')
        subgrupo_ativo = self.request.GET.get('subgrupo')

        # Find the name for the active group
        grupo_ativo_nome = dict(grupos).get(grupo_ativo, "")

        # Find the name for the active subgroup
        subgrupo_ativo_nome = ""
        if subgrupo_ativo:
            # Recursive function to find the name in the hierarchical structure
            def find_subgrupo_name(subgrups_list, target_code):
                for subgrup_data in subgrups_list:
                    if subgrup_data['codigo'] == target_code:
                        return subgrup_data['nome']
                    if subgrup_data.get('filhos'):
                        found_in_children = find_subgrupo_name(subgrup_data['filhos'], target_code)
                        if found_in_children:
                            return found_in_children
                return ""

            subgrupo_ativo_nome = find_subgrupo_name(self.subgrupos_estrutura.get(grupo_ativo, []), subgrupo_ativo)


        context['grupos'] = grupos
        context['grupo_ativo'] = grupo_ativo
        context['subgrupo_ativo'] = subgrupo_ativo
        context['grupo_ativo_nome'] = grupo_ativo_nome # Pass the name
        context['subgrupo_ativo_nome'] = subgrupo_ativo_nome # Pass the name
        context['subgrupos_estrutura'] = self.subgrupos_estrutura
        context['subgrupos_do_grupo_ativo'] = self.subgrupos_estrutura.get(grupo_ativo, [])
        context['current_date'] = timezone.now().date() # Ensure current_date is passed

        return context
    
     