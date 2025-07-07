# backend/core/search.py
from django.apps import apps
from django.db.models import Q
from django.urls import reverse
from django.utils.text import Truncator

class GlobalSearch:
    SEARCHABLE_MODELS = {
        # Accounts
        'user': {
            'app': 'accounts',
            'model': 'SearchableUser',
            'fields': ['email', 'first_name', 'last_name'],  # Removido username
            'url': lambda obj: reverse('user_detail', args=[obj.pk])
        },
        'useractionlog': {
            'app': 'accounts',
            'model': 'SearchableUserActionLog',
            'fields': ['action', 'ip_address', 'computer_name'],
            'url': lambda obj: reverse('user_action_log_detail', args=[obj.pk])
        },

        # Adicional
        'cadastro_adicional': {
            'app': 'adicional',
            'model': 'Cadastro_adicional',
            'fields': ['numero_adicional', 'bol_g_pm_adicional', 'situacao_adicional'],
            'url': lambda obj: reverse('adicional:cadastro_adicional_detail', args=[obj.pk])
        },
        'historicocadastro': {
            'app': 'adicional',
            'model': 'HistoricoCadastro',
            'fields': ['numero_adicional', 'situacao_adicional'],
            'url': lambda obj: reverse('adicional:historico_detail', args=[obj.pk])
        },

        # Agenda
        'lembrete': {
            'app': 'agenda',
            'model': 'Lembrete',
            'fields': ['titulo', 'descricao'],
            'url': lambda obj: reverse('agenda:lembrete_detail', args=[obj.pk])
        },
        'tarefa': {
            'app': 'agenda',
            'model': 'Tarefa',
            'fields': ['titulo', 'descricao'],
            'url': lambda obj: reverse('agenda:tarefa_detail', args=[obj.pk])
        },

        # BM
        'cadastro_bm': {
            'app': 'bm',
            'model': 'Cadastro_bm',
            'fields': ['nome', 'nome_de_guerra', 'cpf', 'email', 'telefone', 'situacao', 'sgb', 'posto_secao'],
            'url': lambda obj: reverse('bm:cadastro_bm_detail', args=[obj.pk])
        },
        'imagem_bm': {
            'app': 'bm',
            'model': 'Imagem_bm',
            'fields': [],
            'url': lambda obj: reverse('bm:imagem_detail', args=[obj.pk])
        },

        # Calculadora
        'calculo_militar': {
            'app': 'calculadora',
            'model': 'CalculoMilitar',
            'fields': [],
            'url': lambda obj: reverse('calculadora:calculo_detail', args=[obj.pk])
        },

        # Cursos
        'medalha': {
            'app': 'cursos',
            'model': 'Medalha',
            'fields': ['honraria', 'bol_g_pm_lp'],
            'url': lambda obj: reverse('cursos:medalha_detail', args=[obj.pk])
        },
        'curso': {
            'app': 'cursos',
            'model': 'Curso',
            'fields': ['curso', 'bol_publicacao'],
            'url': lambda obj: reverse('cursos:curso_detail', args=[obj.pk])
        },

        # Documentos
        'documento': {
            'app': 'documentos',
            'model': 'Documento',
            'fields': ['numero_documento', 'assunto', 'descricao', 'assinada_por'],
            'url': lambda obj: reverse('documentos:documento_detail', args=[obj.pk])
        },
        'arquivo': {
            'app': 'documentos',
            'model': 'Arquivo',
            'fields': ['tipo'],
            'url': lambda obj: reverse('documentos:arquivo_detail', args=[obj.pk])
        },

        # Efetivo
        'cadastro': {
            'app': 'efetivo',
            'model': 'Cadastro',
            'fields': ['re', 'dig', 'nome', 'nome_de_guerra', 'cpf', 'email', 'telefone'],
            'url': lambda obj: reverse('efetivo:militar_detail', args=[obj.pk])
        },
        'detalhes_situacao': {
            'app': 'efetivo',
            'model': 'DetalhesSituacao',
            'fields': ['situacao', 'sgb', 'posto_secao', 'funcao'],
            'url': lambda obj: reverse('efetivo:detalhesituacao_detail', args=[obj.pk])
        },
        'promocao': {
            'app': 'efetivo',
            'model': 'Promocao',
            'fields': ['posto_grad', 'quadro', 'grupo'],
            'url': lambda obj: reverse('efetivo:promocao_detail', args=[obj.pk])
        },
        'catefetivo': {
            'app': 'efetivo',
            'model': 'CatEfetivo',
            'fields': ['tipo', 'observacao'],
            'url': lambda obj: reverse('efetivo:catefetivo_detail', args=[obj.pk])
        },
        'historicocatefetivo': {
            'app': 'efetivo',
            'model': 'HistoricoCatEfetivo',
            'fields': ['tipo', 'observacao'],
            'url': lambda obj: reverse('efetivo:historicocatefetivo_detail', args=[obj.pk])
        },

        # LP
        'lp': {
            'app': 'lp',
            'model': 'LP',
            'fields': ['numero_lp', 'bol_g_pm_lp', 'observacoes'],
            'url': lambda obj: reverse('lp:lp_detail', args=[obj.pk])
        },
        'lp_fruicao': {
            'app': 'lp',
            'model': 'LP_fruicao',
            'fields': ['bol_int', 'observacoes'],
            'url': lambda obj: reverse('lp:lp_fruicao_detail', args=[obj.pk])
        },

        # Municipios
        'posto': {
            'app': 'municipios',
            'model': 'Posto',
            'fields': ['posto_secao', 'posto_atendimento', 'cidade_posto'],
            'url': lambda obj: reverse('municipios:posto_detail', args=[obj.pk])
        },
        'contato': {
            'app': 'municipios',
            'model': 'Contato',
            'fields': ['telefone', 'rua', 'bairro', 'cidade'],
            'url': lambda obj: reverse('municipios:contato_detail', args=[obj.pk])
        },
        'cidade': {
            'app': 'municipios',
            'model': 'Cidade',
            'fields': ['municipio', 'descricao'],
            'url': lambda obj: reverse('municipios:cidade_detail', args=[obj.pk])
        },
        'pessoal': {
            'app': 'municipios',
            'model': 'Pessoal',
            'fields': [],
            'url': lambda obj: reverse('municipios:pessoal_detail', args=[obj.pk])
        },

        # RPT
        'cadastro_rpt': {
            'app': 'rpt',
            'model': 'Cadastro_rpt',
            'fields': ['status', 'sgb_destino', 'posto_secao_destino', 'doc_solicitacao'],
            'url': lambda obj: reverse('rpt:cadastro_rpt_detail', args=[obj.pk])
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
                continue
            
            # Tenta converter query para número se possível
            query_num = None
            if query.isdigit():
                query_num = int(query)
            
            q_objects = Q()
            
            # Busca por campos textuais
            if config['fields']:
                for field in config['fields']:
                    q_objects |= Q(**{f'{field}__icontains': query})
            
            # Busca por ID se query for numérica
            if query_num is not None:
                q_objects |= Q(id=query_num)
            
            # Executa a consulta
            try:
                for obj in model.objects.filter(q_objects).distinct()[:5]:
                    results.append(cls.format_result(config, obj))
            except Exception as e:
                print(f"Erro ao buscar em {config['model']}: {str(e)}")
        
        return results

    @classmethod
    def format_result(cls, config, obj):
        result = {
            'app': config['app'],
            'model': config['model'],
            'object': obj,
            'url': config['url'](obj),
        }
        
        # Usa método personalizado se disponível
        if hasattr(obj, 'get_search_result'):
            result_data = obj.get_search_result()
            result['title'] = result_data.get('title', str(obj))
            result['fields'] = result_data.get('fields', {})
        else:
            result['title'] = str(obj)
            result['fields'] = {}
        
        return result