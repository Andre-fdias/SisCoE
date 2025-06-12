
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
from django.db.models import Q # Adicione esta linha

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
# from django.views.generic import ListView
# from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch
from backend.cursos.models import Medalha,Curso
import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password

logger = logging.getLogger(__name__)

# --- View para listar militares com status "Efetivo" ---
# ... (imports e outras partes da views.py) ...

# --- View para listar militares com status "Efetivo" ---
@login_required
def listar_militar(request):
    if request.method == "GET":
        latest_detalhe_situacao = DetalhesSituacao.objects.filter(
            cadastro=OuterRef('pk')
        ).order_by('-data_alteracao', '-id')

        cadastros = Cadastro.objects.annotate(
            latest_status=Subquery(latest_detalhe_situacao.values('situacao')[:1]),
            latest_sgb=Subquery(latest_detalhe_situacao.values('sgb')[:1]),
            latest_posto_secao=Subquery(latest_detalhe_situacao.values('posto_secao')[:1]),
            latest_prontidao=Subquery(latest_detalhe_situacao.values('prontidao')[:1]),
            latest_saida_da_unidade=Subquery(latest_detalhe_situacao.values('saida_da_unidade')[:1]) # NOVO CAMPO AQUI
        ).filter(
            latest_status='Efetivo'
        ).prefetch_related(
            Prefetch(
                'categorias_efetivo',
                queryset=CatEfetivo.objects.filter(ativo=True),
                to_attr='categorias_ativas'
            ),
            'imagens',
            'promocoes',
        ).annotate(
            latest_posto_grad=Subquery(
                Promocao.objects.filter(
                    cadastro=OuterRef('pk')
                ).order_by('-ultima_promocao').values('posto_grad')[:1]
            )
        ).order_by('latest_posto_grad', 'nome_de_guerra')

        context = {
            'cadastros': cadastros,
            'current_date': timezone.now().date()
        }
        
        return render(request, 'listar_militar.html', context)

# --- Nova View para listar militares com "Outros Status" ---
@login_required
def listar_outros_status_militar(request):
    if request.method == "GET":
        latest_detalhe_situacao = DetalhesSituacao.objects.filter(
            cadastro=OuterRef('pk')
        ).order_by('-data_alteracao', '-id')

        cadastros = Cadastro.objects.annotate(
            latest_status=Subquery(latest_detalhe_situacao.values('situacao')[:1]),
            latest_sgb=Subquery(latest_detalhe_situacao.values('sgb')[:1]),
            latest_posto_secao=Subquery(latest_detalhe_situacao.values('posto_secao')[:1]),
            latest_prontidao=Subquery(latest_detalhe_situacao.values('prontidao')[:1]),
            latest_saida_da_unidade=Subquery(latest_detalhe_situacao.values('saida_da_unidade')[:1]) # NOVO CAMPO AQUI
        ).exclude(
            latest_status='Efetivo'
        ).filter(
            latest_status__isnull=False
        ).prefetch_related(
            Prefetch(
                'categorias_efetivo',
                queryset=CatEfetivo.objects.filter(ativo=True),
                to_attr='categorias_ativas'
            ),
            'imagens',
            'promocoes',
        ).annotate(
            latest_posto_grad=Subquery(
                Promocao.objects.filter(
                    cadastro=OuterRef('pk')
                ).order_by('-ultima_promocao').values('posto_grad')[:1]
            )
        ).order_by('latest_posto_grad', 'nome_de_guerra')

        context = {
            'cadastros': cadastros,
            'current_date': timezone.now().date()
        }
        
        return render(request, 'listar_outros_status.html', context)



        
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
            'BS': 'Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.',
            'CI': 'Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.',
            'DV': 'Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.',
            'EF': 'Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio. As OPM estabelecerão plano de exercícios físicos compatíveis.',
            'FO': 'Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.',
            'IS': 'Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.',
            'LP': 'Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.',
            'MA': 'Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.',
            'MC': 'Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.',
            'MG': 'Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.',
            'OU': 'Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.',
            'PO': 'Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.',
            'PQ': 'Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.',
            'SA': 'Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.',
            'SE': 'Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.',
            'SH': 'Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.',
            'SM': 'Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.',
            'SP': 'Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.',
            'AU': 'Deverá ser empregado somente em atividades administrativas.',
            'EP': 'Deverá ser empregado somente em atividades administrativas.',
            'ES': 'Deverá ser empregado somente em atividades administrativas.',
            'LR': 'Deverá ser empregado somente em atividades administrativas.',
            'PT': 'Deverá ser empregado somente em atividades administrativas.',
            'VP': 'Deverá ser empregado somente em atividades administrativas.',
            'SN': 'Deverá ser escalado para trabalhar durante o dia em qualquer atividade.',
            'SG': 'Deverá ser empregado, preferencialmente, na atividade de policiamento ostensivo, ou, caso não seja possível, em atividades administrativas e de apoio.',
            'UA': 'Deverá ser desarmado e empregado em atividades administrativas. Pode requerer processo administrativo para verificar condições de permanência no serviço ativo.',
            'UU': 'Deverá ser escalado em atividades administrativas ou de apoio, com uniforme de treinamento físico (B-5.1), sem atendimento ao público.',
            'CC': 'Deverá ser escalado em atividades administrativas ou de apoio, com uniforme de treinamento físico (B-5.1), sem atendimento ao público. Cabelos penteados com gel/rede obrigatoriamente.',
            'CB': 'Deverá ser escalado em atividades administrativas ou de apoio, com uniforme de treinamento físico (B-5.1), sem atendimento ao público.',
            'UB': 'Deverá calçar sandálias de borracha na cor preta, sem estampas, e ser escalado em atividades administrativas ou de apoio.',
            'UC': 'Deverá calçar sandálias de borracha na cor preta, sem estampas, e ser escalado em atividades administrativas ou de apoio.',
            'US': 'Deverá calçar sandálias de borracha na cor preta, sem estampas, e ser escalado em atividades administrativas ou de apoio.',
            'DG': 'Deverá ser empregado no policiamento ostensivo.',
            'EM': 'Deverá ser empregado no policiamento ostensivo.',
            'LS': 'Deverá ser empregado no policiamento ostensivo.',
            'MP': 'Deverá ser empregado no policiamento ostensivo.',
            'SB': 'Deverá ser empregado no policiamento ostensivo.',
            'SI': 'Deverá ser empregado no policiamento ostensivo.',
            'ST': 'Deverá ser empregado no policiamento ostensivo.'
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
        

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import (
    Cadastro, 
    DetalhesSituacao, 
    HistoricoDetalhesSituacao,
    CatEfetivo,
    HistoricoCatEfetivo
)
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------
# VIEWS PARA FLUXO DE SITUAÇÃO FUNCIONAL
# ---------------------------------------------------------------
@login_required
def editar_situacao_funcional(request, id):
    cadastro = get_object_or_404(Cadastro, id=id)

    # Get the latest (most current) DetalhesSituacao for the current cadastro
    # Based on your Meta.ordering in DetalhesSituacao, .first() will give the latest.
    current_situacao_obj = DetalhesSituacao.objects.filter(cadastro=cadastro).first()

    if not current_situacao_obj:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Não há situação funcional ativa para editar.'}, status=404)
        messages.error(request, 'Não há situação funcional ativa para editar para este militar.')
        return redirect('efetivo:ver_militar', id=cadastro.id)

    if request.method == 'POST':
        try:
            nova_situacao = request.POST.get('situacao')
            saida_da_unidade_str = request.POST.get('saida_da_unidade') # This is the end date for the *current* situation

            # Basic validation
            if not nova_situacao:
                return JsonResponse({'success': False, 'message': 'Selecione a nova situação.'}, status=400)
            if not saida_da_unidade_str:
                return JsonResponse({'success': False, 'message': 'A Data de Saída é obrigatória.'}, status=400)

            try:
                # Convert the date string to a Python date object
                saida_da_unidade_date = timezone.datetime.strptime(saida_da_unidade_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Formato de data inválido. Use AAAA-MM-DD.'}, status=400)

            # --- Step 1: Archive the CURRENT DetalhesSituacao record ---
            # Create a history entry with the *details of the current situation*
            HistoricoDetalhesSituacao.objects.create(
                cadastro=cadastro,
                situacao=current_situacao_obj.situacao,
                sgb=current_situacao_obj.sgb,
                posto_secao=current_situacao_obj.posto_secao,
                esta_adido=current_situacao_obj.esta_adido,
                funcao=current_situacao_obj.funcao,
                op_adm=current_situacao_obj.op_adm,
                prontidao=current_situacao_obj.prontidao,
                cat_efetivo=current_situacao_obj.cat_efetivo, # Ensure this field exists in DetalhesSituacao
                apresentacao_na_unidade=current_situacao_obj.apresentacao_na_unidade,
                saida_da_unidade=saida_da_unidade_date, # This is the date the archived situation ended
                usuario_alteracao=request.user,
                # data_alteracao will be auto_now_add
            )

            # --- Step 2: Delete the current DetalhesSituacao record (or mark it inactive if preferred) ---
            # Deleting the current record and creating a new one is cleaner for 'active' situations.
            current_situacao_obj.delete() 
            # If you prefer marking inactive: current_situacao_obj.is_active = False; current_situacao_obj.save()
            # Then adjust queries to filter for is_active=True

            # --- Step 3: Create a NEW DetalhesSituacao record with the updated info ---
            DetalhesSituacao.objects.create(
                cadastro=cadastro,
                situacao=nova_situacao, # The new situation
                sgb=current_situacao_obj.sgb,  # Copy SGB from previous situation
                posto_secao=current_situacao_obj.posto_secao,  # Copy Posto/Seção from previous situation
                esta_adido=current_situacao_obj.esta_adido, # Copy from previous
                funcao=current_situacao_obj.funcao,  # Copy Função from previous situation
                op_adm=current_situacao_obj.op_adm, # Copy from previous
                prontidao=current_situacao_obj.prontidao,  # Copy Prontidão from previous situation
                apresentacao_na_unidade=saida_da_unidade_date, # The new presentation date is when the previous situation ended
                saida_da_unidade=None, # The new situation doesn't have an end date yet
                usuario_alteracao=request.user,
                # data_alteracao will be auto_now_add for the new record
            )

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Situação funcional atualizada e arquivada com sucesso!'})
            
            messages.success(request, 'Situação funcional atualizada e arquivada com sucesso!')
            return redirect('efetivo:ver_militar', id=cadastro.id)

        except Exception as e:
            logger.error(f"Erro ao editar situação funcional do militar {id}: {e}", exc_info=True)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': f'Erro ao salvar: {str(e)}'}, status=500)
            messages.error(request, f'Erro ao salvar alterações: {str(e)}')
            return redirect('efetivo:ver_militar', id=cadastro.id)

    # GET request - render the modal with current data
    context = {
        'cadastro': cadastro,
        'detalhes': current_situacao_obj, # Pass the current object for displaying current data
        'situacao_choices': situacao_choices, # Pass choices to populate the select field
    }
    return render(request, 'modals/editar_situacao_funcional.html', context)


    

@login_required
def confirmar_arquivamento(request, id):
    """
    View para o Passo 2 - Modal de confirmação após arquivamento
    """
    cadastro = get_object_or_404(Cadastro, id=id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'cadastrar_nova':
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('efetivo:cadastrar_nova_situacao', args=[cadastro.id])
            })
        else:
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('efetivo:ver_militar', args=[cadastro.id])
            })

    # GET request - mostrar modal
    return render(request, 'modals/confirmar_arquivamento.html', {
        'cadastro': cadastro
    })

@login_required
def cadastrar_nova_situacao(request, id):
    """
    View para o Passo 3 - Modal para cadastrar nova situação funcional
    """
    cadastro = get_object_or_404(Cadastro, id=id)

    if request.method == 'POST':
        try:
            # Criar nova situação funcional
            nova_situacao = DetalhesSituacao(
                cadastro=cadastro,
                situacao=request.POST.get('situacao', 'ATIVO'),
                sgb=request.POST['sgb'],
                posto_secao=request.POST['posto_secao'],
                funcao=request.POST['funcao'],
                prontidao=request.POST['prontidao'],
                apresentacao_na_unidade=request.POST['apresentacao_na_unidade'],
                usuario_alteracao=request.user
            )
            nova_situacao.save()

            # Atualizar categoria de efetivo
            categoria_atual = CatEfetivo.objects.filter(cadastro=cadastro, ativo=True).first()
            if categoria_atual:
                categoria_atual.ativo = False
                categoria_atual.data_termino = timezone.now().date()
                categoria_atual.save()

                # Registrar no histórico
                HistoricoCatEfetivo.objects.create(
                    cat_efetivo=categoria_atual,
                    tipo=categoria_atual.tipo,
                    data_inicio=categoria_atual.data_inicio,
                    data_termino=timezone.now().date(),
                    ativo=False,
                    usuario_alteracao=request.user
                )

            # Criar nova categoria (padrão ATIVO)
            nova_categoria = CatEfetivo(
                cadastro=cadastro,
                tipo=request.POST.get('cat_efetivo', 'ATIVO'),
                data_inicio=request.POST['apresentacao_na_unidade'],
                usuario_cadastro=request.user,
                ativo=True
            )
            nova_categoria.save()

            return JsonResponse({
                'success': True,
                'redirect_url': reverse('efetivo:ver_militar', args=[cadastro.id])
            })

        except Exception as e:
            logger.error(f"Erro ao cadastrar nova situação: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': f'Erro ao processar: {str(e)}'
            }, status=500)

    # GET request - mostrar modal
    context = {
        'cadastro': cadastro,
        'sgb_choices': DetalhesSituacao.SGB_CHOICES,
        'posto_secao_choices': DetalhesSituacao.POSTO_SECAO_CHOICES,
        'funcao_choices': DetalhesSituacao.FUNCAO_CHOICES,
        'prontidao_choices': DetalhesSituacao.PRONTIDAO_CHOICES,
        'cat_efetivo_choices': CatEfetivo.TIPO_CHOICES,
    }
    return render(request, 'modals/cadastrar_nova_situacao.html', context)




from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import Cadastro

@login_required
def editar_dados_pessoais_contatos(request, id):
    cadastro = get_object_or_404(Cadastro, id=id)
    
    if request.method == "POST":
        try:
            # Atualizar os campos do cadastro com os dados do formulário
            cadastro.nome = request.POST.get('nome')
            cadastro.nome_de_guerra = request.POST.get('nome_de_guerra')
            cadastro.re = request.POST.get('re')
            cadastro.dig = request.POST.get('dig')
            cadastro.genero = request.POST.get('genero')
            cadastro.nasc = request.POST.get('nasc')
            cadastro.matricula = request.POST.get('matricula')
            cadastro.admissao = request.POST.get('admissao')
            cadastro.previsao_de_inatividade = request.POST.get('previsao_de_inatividade')
            cadastro.cpf = request.POST.get('cpf')
            cadastro.rg = request.POST.get('rg')
            cadastro.telefone = request.POST.get('telefone')
            cadastro.email = request.POST.get('email')
            cadastro.tempo_para_averbar_militar = request.POST.get('tempo_para_averbar_militar', 0)
            cadastro.tempo_para_averbar_inss = request.POST.get('tempo_para_averbar_inss', 0)
            cadastro.alteracao = request.POST.get('alteracao')
            
            # Validar e salvar
            cadastro.full_clean()  # Validação do modelo
            cadastro.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Dados atualizados com sucesso!'
                })
            
            messages.success(request, 'Dados atualizados com sucesso!')
            return redirect('efetivo:ver_militar', id=cadastro.id)
            
        except ValidationError as e:
            error_message = '; '.join([f"{k}: {', '.join(v)}" for k, v in e.message_dict.items()])
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': error_message
                }, status=400)
            
            messages.error(request, f'Erro de validação: {error_message}')
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': str(e)
                }, status=400)
            
            messages.error(request, f'Erro ao atualizar dados: {str(e)}')
    
    context = {
        'cadastro': cadastro,
    }
    return render(request, 'modals/editar_dados_pessoais.html', context)



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
# backend/efetivo/views.py
from django.views import View
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import CatEfetivo
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

# ... existing code ...

# Consider adding @login_required to the dispatch method if authentication is needed
@method_decorator(csrf_exempt, name='dispatch') # Only if you're not using CSRF tokens, which is NOT recommended for production.
                                                # Better to handle CSRF token in the HTML.
class SalvarEdicaoCategoriaView(View):
    def post(self, request, categoria_id, *args, **kwargs):
        categoria = get_object_or_404(CatEfetivo, id=categoria_id)

        try:
            # Assuming data is sent as JSON via fetch API
            data = json.loads(request.body)
            novo_tipo = data.get('tipo')
            novo_periodo = data.get('periodo')
            novas_restricoes = data.get('restricoes')

            # Update the category fields
            categoria.tipo = novo_tipo
            categoria.periodo = novo_periodo
            categoria.restricoes = novas_restricoes
            categoria.save()

            return JsonResponse({'success': True, 'message': 'Categoria atualizada com sucesso!'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

# ... rest of your views.py

# views.py (Atualização Final)

@login_required
def editar_categoria_modal(request, categoria_id):
    categoria = get_object_or_404(CatEfetivo, id=categoria_id)
    if request.method == 'GET':
        context = {
            'categoria': categoria,
            'categoria_choices': CatEfetivo.TIPO_CHOICES, # Assuming you have choices for categories
        }
        return render(request, 'seu_template_de_modal_edicao.html', context)
    # You might also handle POST here if it's a direct form submission,
    # or have a separate view for POST, as you have with SalvarEdicaoCategoriaView.
    # This example focuses on GET for modal rendering.

    
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404

@require_http_methods(["GET"])
def editar_categoria_efetivo(request, categoria_id):
    try:
        categoria = get_object_or_404(CategoriaEfetivo, id=categoria_id)
        
        if not categoria.ativo:
            return JsonResponse({'error': 'Esta categoria não está ativa e não pode ser editada'}, status=400)
        
        restricoes_data = []
        if categoria.tipo == 'RESTRICAO':
            restricoes = Restricao.objects.all()
            for restricao in restricoes:
                field_name = f'restricao_{restricao.id}'
                restricoes_data.append({
                    'id': restricao.id,
                    'name': field_name,
                    'verbose_name': restricao.nome,
                    'value': getattr(categoria, field_name, False)
                })
        
        html = render_to_string('efetivo/modals/modal_edicao_categoria_efetivo.html', {
            'id': categoria.id,
            'tipo': categoria.tipo,
            'tipo_display': categoria.get_tipo_display(),
            'data_inicio': categoria.data_inicio.strftime('%Y-%m-%d') if categoria.data_inicio else '',
            'data_termino': categoria.data_termino.strftime('%Y-%m-%d') if categoria.data_termino else '',
            'observacao': categoria.observacao or '',
            'restricoes': restricoes_data,
        })
        
        return JsonResponse({'html': html})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
def salvar_edicao_categoria(request, categoria_id):
    try:
        categoria = CategoriaEfetivo.objects.get(id=categoria_id)
        
        # Verifica se a categoria está ativa (pode ser editada)
        if not categoria.ativo:
            return JsonResponse({'error': 'Esta categoria não está ativa e não pode ser editada'}, status=400)
        
        data = request.POST
        
        # Atualiza os campos básicos
        if 'data_inicio' in data:
            categoria.data_inicio = data['data_inicio'] or None
        if 'data_termino' in data:
            categoria.data_termino = data['data_termino'] or None
        if 'observacao' in data:
            categoria.observacao = data['observacao']
        
        # Atualiza restrições se for do tipo RESTRICAO
        if categoria.tipo == 'RESTRICAO':
            restricoes = Restricao.objects.all()
            for restricao in restricoes:
                field_name = f'restricao_{restricao.id}'
                setattr(categoria, field_name, field_name in data)
        
        categoria.save()
        
        return JsonResponse({'success': True})
    
    except CategoriaEfetivo.DoesNotExist:
        return JsonResponse({'error': 'Categoria não encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)      



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
        afastamento_types = [choice[0] for choice in CatEfetivo.TIPO_CHOICES]
        grupo_ativo = self.request.GET.get('grupo')
        subgrupo_ativo = self.request.GET.get('subgrupo')

        # Calculate counts for all groups and subgroups
        contagens_por_grupo = {}
        for grupo_key, _ in grupos:
            contagens_por_grupo[grupo_key] = self.calcular_contagens(
                self.subgrupos_estrutura.get(grupo_key, [])
            )

        # Calculate total counts per group
        agrupamento_counts = {}
        for grupo_key, _ in grupos:
            agrupamento_counts[grupo_key] = Cadastro.objects.filter(
                detalhes_situacao__sgb=grupo_key
            ).distinct().count()

        context.update({
            'contagens_por_grupo': contagens_por_grupo,
            'afastamento_types': afastamento_types,
            'agrupamento_counts': agrupamento_counts,
            'grupos': grupos,
            'grupo_ativo': grupo_ativo,
            'subgrupo_ativo': subgrupo_ativo,
            'grupo_ativo_nome': dict(grupos).get(grupo_ativo, ""),
            'subgrupo_ativo_nome': self.get_subgrupo_nome(grupo_ativo, subgrupo_ativo),
            'subgrupos_estrutura': self.subgrupos_estrutura,
            'current_date': timezone.now().date()
        })
        return context

    def calcular_contagens(self, estrutura):
        contagens = {}
        for item in estrutura:
            count = Cadastro.objects.filter(
                detalhes_situacao__posto_secao=item['codigo']
            ).distinct().count()
            
            contagens[item['codigo']] = count
            
            if item['filhos']:
                contagens.update(self.calcular_contagens(item['filhos']))
        return contagens

    def get_subgrupo_nome(self, grupo_key, subgrupo_codigo):
        if not subgrupo_codigo:
            return ""
            
        for subgrupo in self.subgrupos_estrutura.get(grupo_key, []):
            if subgrupo['codigo'] == subgrupo_codigo:
                return subgrupo['nome']
            if subgrupo.get('filhos'):
                for filho in subgrupo['filhos']:
                    if filho['codigo'] == subgrupo_codigo:
                        return filho['nome']
        return ""

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus.doctemplate import PageTemplate
from django.contrib.staticfiles import finders
import os

def get_image_path(file):
    path = finders.find(f'img/{file}')
    if not path or not os.path.exists(path):
        raise FileNotFoundError(f"Arquivo estático img/{file} não encontrado!")
    return path

def pagina_buscar_militar(request):
    return render(request, 'buscar_militar.html')

def gerar_etiqueta_pdf(request):
    if request.method == 'GET':
        return render(request, 'buscar_militar.html')
    
    re_param = request.POST.get('re', '').strip()
    context = {'re_value': re_param}

    if not re_param:
        context['error_message'] = "Por favor, digite o RE do militar."
        return render(request, 'buscar_militar.html', context, status=400)

    try:
        cadastro = get_object_or_404(Cadastro, re=re_param)
    except Exception as e:
        context['error_message'] = f"Militar com RE {re_param} não encontrado."
        return render(request, 'buscar_militar.html', context, status=404)

    try:
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="etiqueta_militar_{re_param}.pdf"'

        # --- Dimensões da Etiqueta ---
        ETIQUETA_WIDTH = 130 * mm
        ETIQUETA_HEIGHT = 60 * mm
        page_width, page_height = A4
        
        # Margens
        margin_page = 10 * mm
        x_pos = margin_page
        y_pos = page_height - margin_page - ETIQUETA_HEIGHT

        doc = SimpleDocTemplate(
            response,
            pagesize=A4,
            rightMargin=0,
            leftMargin=0,
            topMargin=0,
            bottomMargin=0
        )
        
        styles = getSampleStyleSheet()
        
        # --- Estilos Personalizados ---
        styles.add(ParagraphStyle(
            name='HeaderText',
            fontSize=11,
            leading=12,
            textColor=colors.HexColor('#1a365d'),
            alignment=1,
            fontName='Helvetica-Bold',
            spaceAfter=6*mm
        ))

        styles.add(ParagraphStyle(
            name='MilitaryName',
            fontSize=14,
            leading=15,
            textColor=colors.black,
            alignment=1,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='MilitaryRankWarName',
            fontSize=11,
            leading=12,
            textColor=colors.HexColor('#1a365d'),
            alignment=1,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='MilitaryRE',
            fontSize=13, 
            leading=11,
            textColor=colors.HexColor('#9c4221'),
            alignment=1,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='MilitaryDetail',
            fontSize=9,
            leading=10,
            textColor=colors.black,
            alignment=1,
            spaceAfter=0.5*mm
        ))

        # --- Carregar imagens ---
 # --- Carregar imagens ---
        try:
            # Logo como marca d'água central (3x4 ocupando toda altura)
            logo_img = Image('backend/core/static/img/logo.png', 
                           width=(3/4)*ETIQUETA_HEIGHT,
                           height=ETIQUETA_HEIGHT)
            
            # Brasão no canto superior esquerdo (15x15mm)
            brasao_img = Image('backend/core/static/img/brasao.png', 
                              width=15*mm, 
                              height=15*mm)
            
            # Brasão PM no canto superior direito (15x15mm)
            brasao_pm_img = Image('backend/core/static/img/brasaopm.png', 
                                 width=15*mm, 
                                 height=15*mm)
            
        except Exception as e:
            context['error_message'] = f"Erro ao carregar imagens: {str(e)}"
            return render(request, 'buscar_militar.html', context, status=500)

        # --- Elementos da etiqueta ---
        elements = []

        # Cabeçalho com brasões e texto
        header_data = [
            [brasao_img, Paragraph("15º GRUPAMENTO DE BOMBEIROS", styles['HeaderText']), brasao_pm_img]
        ]
        
        header_table = Table(header_data, 
                           colWidths=[20*mm, ETIQUETA_WIDTH-40*mm, 20*mm],
                           rowHeights=[15*mm])
        
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (0,0), 'LEFT'),
            ('ALIGN', (2,0), (2,0), 'RIGHT'),
            ('ALIGN', (1,0), (1,0), 'CENTER'),
            ('LEFTPADDING', (1,0), (1,0), 0),
            ('RIGHTPADDING', (1,0), (1,0), 0),
        ]))
        
        elements.append(header_table)


        # Conteúdo principal
        elements.append(Paragraph(cadastro.nome.upper() if cadastro.nome else '', styles['MilitaryName']))
        elements.append(Spacer(1, 1*mm))

        last_promotion = cadastro.promocoes.order_by('-data_alteracao').first()
        if last_promotion and last_promotion.posto_grad:
            rank_war_name = f"{last_promotion.posto_grad.upper()} {cadastro.nome_de_guerra.upper() if cadastro.nome_de_guerra else ''}"
        else:
            rank_war_name = cadastro.nome_de_guerra.upper() if cadastro.nome_de_guerra else ''
        
        elements.append(Paragraph(rank_war_name.strip(), styles['MilitaryRankWarName']))
        elements.append(Spacer(1, 1*mm))

        re_text = f"{cadastro.re or ''}-{cadastro.dig or ''}" if cadastro.dig else f"{cadastro.re or ''}"
        elements.append(Paragraph(re_text, styles['MilitaryRE']))
        elements.append(Spacer(1, 3*mm))

        last_situacao = cadastro.detalhes_situacao.order_by('-data_alteracao').first()
        if last_situacao:
            if last_situacao.funcao:
                elements.append(Paragraph(last_situacao.funcao.upper(), styles['MilitaryDetail']))
            if last_situacao.sgb:
                elements.append(Paragraph(last_situacao.sgb.upper(), styles['MilitaryDetail']))
            if last_situacao.posto_secao:
                elements.append(Paragraph(last_situacao.posto_secao.upper(), styles['MilitaryDetail']))

        # --- Função para desenhar o layout completo ---
        def draw_page(canvas, doc):
            # Marca d'água
            canvas.saveState()
            canvas.setFillAlpha(0.1)
            logo_img.drawOn(canvas, 
                          x_pos + (ETIQUETA_WIDTH - logo_img.drawWidth)/2, 
                          y_pos + (ETIQUETA_HEIGHT - logo_img.drawHeight)/2)
            canvas.restoreState()
            
            # Bordas estilizadas
            canvas.saveState()
            
            AZUL_ESCURO = colors.HexColor('#1a365d')
            DOURADO = colors.HexColor('#d4af37')
            
            # Borda externa
            canvas.setStrokeColor(AZUL_ESCURO)
            canvas.setLineWidth(1.2*mm)
            canvas.rect(
                x_pos - 0.6*mm,
                y_pos - 0.6*mm,
                ETIQUETA_WIDTH + 1.2*mm,
                ETIQUETA_HEIGHT + 1.2*mm
            )
            
            # Filete dourado
            canvas.setStrokeColor(DOURADO)
            canvas.setLineWidth(0.6*mm)
            canvas.rect(
                x_pos + 2*mm,
                y_pos + 2*mm,
                ETIQUETA_WIDTH - 4*mm,
                ETIQUETA_HEIGHT - 4*mm
            )
            
            # Linha intermediária
            canvas.setStrokeColor(AZUL_ESCURO)
            canvas.setLineWidth(0.3*mm)
            canvas.rect(
                x_pos + 1*mm,
                y_pos + 1*mm,
                ETIQUETA_WIDTH - 2*mm,
                ETIQUETA_HEIGHT - 2*mm
            )
            
            # Cantos decorados
            TAMANHO_CANTO = 5*mm
            # (código dos cantos mantido igual)
            
            canvas.restoreState()

        # Frame e construção do PDF
        frame = Frame(x_pos, y_pos, ETIQUETA_WIDTH, ETIQUETA_HEIGHT,
                     leftPadding=5*mm, bottomPadding=5*mm,
                     rightPadding=5*mm, topPadding=5*mm,
                     showBoundary=0)
        
        doc.addPageTemplates([PageTemplate(id='EtiquetaPage', frames=frame, onPage=draw_page)])
        doc.build(elements)
        
        return response

    except Exception as e:
        context['error_message'] = f"Erro ao gerar etiqueta: {str(e)}"
        return render(request, 'buscar_militar.html', context, status=500)