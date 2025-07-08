# backend/core/search.py
from django.apps import apps
from django.db.models import Q
from django.urls import reverse
from django.utils.text import Truncator

class GlobalSearch:

    APP_COLORS = {
        'accounts': '#FF5733',      # Laranja
        'adicional': '#33FF57',     # Verde
        'agenda': '#3357FF',        # Azul
        'bm': '#F033FF',            # Magenta
        'calculadora': '#FF3333',   # Vermelho
        'cursos': '#33FFF3',        # Ciano
        'documentos': '#F3FF33',    # Amarelo
        'efetivo': '#8A33FF',       # Roxo
        'lp': '#33FF8A',            # Verde água
        'municipios': '#FF8A33',    # Laranja claro
        'rpt': '#338AFF',           # Azul claro
    }



    SEARCHABLE_MODELS = {
        # Accounts
        'user': {
            'app': 'accounts',
            'model': 'User', # Assumindo que 'User' é o modelo User padrão ou um proxy SearchableUser
            'fields': ['email', 'first_name', 'last_name'],
            'url': lambda obj: reverse('user_detail', args=[obj.pk]) # Verifique se 'user_detail' existe
        },
        'useractionlog': {
            'app': 'accounts',
            'model': 'UserActionLog', # Assumindo que 'UserActionLog' é o modelo correto
            'fields': ['action', 'ip_address', 'computer_name'],
            'url': lambda obj: reverse('user_action_log_detail', args=[obj.pk]) # Verifique se 'user_action_log_detail' existe
        },

        # Adicional
        'cadastro_adicional': {
            'app': 'adicional',
            'model': 'Cadastro_adicional',
            'fields': [
                'numero_adicional', 'bol_g_pm_adicional', 'situacao_adicional',
                'cadastro__re' # Busca pelo RE do Cadastro relacionado
            ],
            'url': lambda obj: reverse('adicional:ver_adicional', args=[obj.pk])
        },
        'historicocadastro': {
            'app': 'adicional',
            'model': 'HistoricoCadastro',
            'fields': [
                'numero_adicional', 'situacao_adicional',
                'cadastro_adicional__cadastro__re' # Busca pelo RE do Cadastro através do Cadastro_adicional
            ],
            'url': lambda obj: reverse('adicional:historico_adicional', args=[obj.cadastro_adicional.id]) # Assumindo URL de histórico
        },


        # Agenda
        'lembrete': {
            'app': 'agenda',
            'model': 'Lembrete',
            'fields': ['titulo', 'descricao'],
            'url': lambda obj: reverse('agenda:lembrete_detail', args=[obj.pk]) # Verifique se 'lembrete_detail' existe
        },
        'tarefa': {
            'app': 'agenda',
            'model': 'Tarefa',
            'fields': ['titulo', 'descricao'],
            'url': lambda obj: reverse('agenda:tarefa_detail', args=[obj.pk]) # Verifique se 'tarefa_detail' existe
        },

        # BM
        'cadastro_bm': {
            'app': 'bm',
            'model': 'Cadastro_bm',
            'fields': [
                'nome', 'nome_de_guerra', 'situacao', 'sgb', 'posto_secao', 'cpf',
                'rg', 'cnh', 'cat_cnh', 'esb', 'ovb', 'email', 'telefone', 'funcao',
                'genero'
            ],
            'url': lambda obj: reverse('bm:ver_bm', args=[obj.pk])
        },
        'imagem_bm': {
            'app': 'bm',
            'model': 'Imagem_bm',
            'fields': [], # Imagens geralmente não têm campos textuais para busca direta
            'url': lambda obj: reverse('bm:ver_bm', args=[obj.cadastro.pk]) # Link para o cadastro BM principal
        },

        # Calculadora
        'calculo_militar': {
            'app': 'calculadora',
            'model': 'CalculoMilitar',
            'fields': [], # Adicione campos se houver texto relevante para busca
            'url': lambda obj: reverse('calculadora:calculo_detail', args=[obj.pk]) # Verifique se 'calculo_detail' existe
        },

        # Cursos
        'medalha': {
            'app': 'cursos',
            'model': 'Medalha',
            'fields': ['honraria', 'bol_g_pm_lp'],
            'url': lambda obj: reverse('cursos:medalha_detail', args=[obj.pk]) # Verifique se 'medalha_detail' existe
        },
        'curso': {
            'app': 'cursos',
            'model': 'Curso',
            'fields': ['curso', 'bol_publicacao'],
            'url': lambda obj: reverse('cursos:curso_detail', args=[obj.pk]) # Verifique se 'curso_detail' existe
        },

        # Documentos
        'documento': {
            'app': 'documentos',
            'model': 'Documento',
            'fields': ['numero_documento', 'assunto', 'descricao', 'assinada_por'],
            'url': lambda obj: reverse('documentos:documento_detail', args=[obj.pk]) # Verifique se 'documento_detail' existe
        },
        'arquivo': {
            'app': 'documentos',
            'model': 'Arquivo',
            'fields': ['tipo'],
            'url': lambda obj: reverse('documentos:documento_detail', args=[obj.documento.pk]) # Link para o documento principal
        },

        # Efetivo
        'cadastro': {
            'app': 'efetivo',
            'model': 'Cadastro',
            'fields': [
                're', 'nome', 'nome_de_guerra', 'genero', 'cpf', 'email', 'telefone'
            ],
            'url': lambda obj: reverse('efetivo:ver_militar', args=[obj.pk])
        },
        'detalhes_situacao': {
            'app': 'efetivo',
            'model': 'DetalhesSituacao',
            'fields': [
                'situacao', 'sgb', 'posto_secao', 'funcao', 'esta_adido', 'op_adm', 'prontidao',
                'cadastro__re' # Busca pelo RE do Cadastro relacionado
            ],
            'url': lambda obj: reverse('efetivo:historico_movimentacoes', args=[obj.cadastro.id])
        },
        'promocao': {
            'app': 'efetivo',
            'model': 'Promocao',
            'fields': [
                'posto_grad', 'quadro', 'grupo',
                'cadastro__re' # Busca pelo RE do Cadastro relacionado
            ],
            'url': lambda obj: reverse('efetivo:historico_movimentacoes', args=[obj.cadastro.id])
        },
        'catefetivo': { # Mantido, mas verifique se existe uma URL de detalhe ou se deve linkar ao Cadastro
            'app': 'efetivo',
            'model': 'CatEfetivo',
            'fields': ['tipo', 'observacao', 'cadastro__re'], # Adicionado 'cadastro__re'
            'url': lambda obj: reverse('efetivo:ver_militar', args=[obj.cadastro.id]) # Link para o militar
        },
        'historicocatefetivo': {
            'app': 'efetivo',
            'model': 'HistoricoCatEfetivo',
            'fields': [
                'tipo', 'observacao',
                'cat_efetivo__cadastro__re' # Caminho encadeado para buscar RE
            ],
            'url': lambda obj: reverse('efetivo:historico_categorias', args=[obj.cat_efetivo.cadastro.id]) # Corrigido para usar o ID do militar
        },

        # LP
        'lp': {
            'app': 'lp',
            'model': 'LP',
            'fields': [
                'numero_lp', 'data_ultimo_lp', 'numero_prox_lp', 'proximo_lp',
                'mes_proximo_lp', 'ano_proximo_lp', 'dias_desconto_lp',
                'bol_g_pm_lp', 'data_publicacao_lp', 'data_concessao_lp',
                'lancamento_sipa', 'observacoes', 'situacao_lp', 'status_lp',
                'cadastro__re' # Busca pelo RE do Cadastro relacionado
            ],
            'url': lambda obj: reverse('lp:ver_lp', args=[obj.pk])
        },
        'historicolp': {
            'app': 'lp',
            'model': 'HistoricoLP',
            'fields': [
                'situacao_lp', 'status_lp', 'numero_lp', 'bol_g_pm_lp',
                'observacoes_historico',
                'lp__cadastro__re' # Busca pelo RE do Cadastro através da LP
            ],
            'url': lambda obj: reverse('lp:ver_lp', args=[obj.lp.pk]) # Link para a LP principal
        },
        'lp_fruicao': {
            'app': 'lp',
            'model': 'LP_fruicao',
            'fields': [
                'numero_lp', 'data_concessao_lp', 'bol_g_pm_lp',
                'data_publicacao_lp', 'tipo_periodo_afastamento', 'tipo_choice',
                'dias_disponiveis', 'dias_utilizados', 'bol_int',
                'cadastro__re' # Busca pelo RE do Cadastro relacionado
            ],
            'url': lambda obj: reverse('lp:detalhar_fruicao', args=[obj.pk])
        },

        # Municipios
        'posto': {
            'app': 'municipios',
            'model': 'Posto',
            'fields': [
                'sgb', 'posto_secao', 'posto_atendimento', 'cidade_posto',
                'tipo_cidade', 'op_adm'
            ],
            'url': lambda obj: reverse('municipios:posto_detail', args=[obj.pk])
        },
        'contato': {
            'app': 'municipios',
            'model': 'Contato',
            'fields': [
                'telefone', 'rua', 'numero', 'complemento', 'bairro',
                'cidade', 'cep', 'email'
            ],
            'url': lambda obj: reverse('municipios:contato_detail', args=[obj.pk])
        },
        'pessoal': {
            'app': 'municipios',
            'model': 'Pessoal',
            'fields': [
                'cel', 'ten_cel', 'maj', 'cap', 'tenqo', 'tenqa', 'asp',
                'st_sgt', 'cb_sd'
            ],
            'url': lambda obj: reverse('municipios:editar_pessoal', args=[obj.posto.pk])
        },
        'cidade': {
            'app': 'municipios',
            'model': 'Cidade',
            'fields': [
                'municipio', 'descricao'
            ],
            'url': lambda obj: reverse('municipios:municipio_detail', args=[obj.pk])
        },

        # RPT
        'cadastro_rpt': {
            'app': 'rpt',
            'model': 'Cadastro_rpt',
            'fields': [
                'data_pedido', 'data_movimentacao', 'data_alteracao', 'status',
                'sgb_destino', 'posto_secao_destino', 'doc_solicitacao',
                'doc_alteracao', 'doc_movimentacao', 'alteracao',
                'cadastro__re' # Busca pelo RE do Cadastro relacionado
            ],
            'url': lambda obj: reverse('rpt:ver_rpt', args=[obj.pk])
        },
        'historico_rpt': {
            'app': 'rpt',
            'model': 'HistoricoRpt',
            'fields': [
                'data_pedido', 'data_movimentacao', 'data_alteracao', 'status',
                'sgb_destino', 'posto_secao_destino', 'doc_solicitacao',
                'doc_alteracao', 'doc_movimentacao', 'alteracao',
                'cadastro__cadastro__re' # Busca pelo RE do Cadastro através do Cadastro_rpt
            ],
            'url': lambda obj: reverse('rpt:historico_rpt', args=[obj.cadastro.pk])
        },
    }

    @classmethod
    def search(cls, query):
        results = []
        query = query.strip().lower()
        
        if not query:
            return results
        
        for key, config in cls.SEARCHABLE_MODELS.items():
            try:
                model = apps.get_model(config['app'], config['model'])
            except LookupError:
                print(f"Erro: Modelo '{config['model']}' no app '{config['app']}' não encontrado. Verifique INSTALLED_APPS e o nome do modelo.")
                continue
            
            # Tenta converter query para número se possível (útil para REs numéricos ou IDs)
            query_num = None
            if query.isdigit():
                query_num = int(query)
            
            q_objects = Q()
            
            # Busca por campos textuais (incluindo relacionamentos como 'cadastro__re')
            if config['fields']:
                for field in config['fields']:
                    # Para campos diretos ou relacionamentos que não são numéricos
                    if '__' in field or not hasattr(model._meta.get_field(field), 'get_internal_type') or model._meta.get_field(field).get_internal_type() not in ['IntegerField', 'PositiveSmallIntegerField', 'FloatField']:
                        try:
                            # Tenta adicionar a cláusula Q. Se o campo não existir ou o path for inválido, uma exceção será levantada e tratada.
                            q_objects |= Q(**{f'{field}__icontains': query})
                        except Exception as e:
                            print(f"Aviso: Não foi possível criar a cláusula de busca para o campo '{field}' no modelo '{config['model']}' do app '{config['app']}'. Erro: {e}")
                    # Para campos numéricos diretos que podem ser buscados por valor exato se a query for numérica
                    elif query_num is not None and hasattr(model, field):
                         q_objects |= Q(**{field: query_num})


            # Busca por ID do objeto se query for numérica e o modelo tiver campo 'id'
            if query_num is not None:
                if hasattr(model, 'id'):
                    q_objects |= Q(id=query_num)
            
            # Executa a consulta apenas se houver Q objects válidos
            if q_objects:
                try:
                    for obj in model.objects.filter(q_objects).distinct()[:5]: # Limita a 5 resultados por modelo
                        results.append(cls.format_result(config, obj))
                except Exception as e:
                    # Captura erros específicos de FieldError ou outros problemas de consulta
                    print(f"Erro ao buscar em {config['model']} (app: {config['app']}): {str(e)}")
        
        return results


    @classmethod
    def format_result(cls, config, obj):
        """
        Formata o resultado da busca para exibição no template.
        Adiciona cor específica do app ao resultado.
        """
        # Determina a cor do app (adicionado)
        app_color = cls.APP_COLORS.get(config['app'], '#CCCCCC')  # Cinza padrão se não encontrado
        
        result = {
            'app': config['app'],
            'model': config['model'],
            'object': obj,
            'url': config['url'](obj),
            'app_color': app_color,  # Nova chave adicionada
        }
        
        # Usa método personalizado get_search_result se disponível no objeto
        if hasattr(obj, 'get_search_result'):
            try:
                result_data = obj.get_search_result()
                result['title'] = result_data.get('title', str(obj))
                result['fields'] = result_data.get('fields', {})
            except Exception as e:
                # Fallback se get_search_result() falhar
                print(f"Aviso: Erro ao chamar get_search_result() para {obj} ({config['model']}). Usando fallback. Erro: {e}")
                result['title'] = str(obj)
                result['fields'] = {}
        else:
            # Fallback padrão se get_search_result() não existir
            result['title'] = str(obj)
            result['fields'] = {}
        
        return result
