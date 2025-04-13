# backend/faisca/faisca_agent.py
from django.apps import apps
from django.conf import settings
from django.core.exceptions import FieldError
import json

class FaiscaAgent:
    def __init__(self, user):
        self.user = user
        self.allowed_apps = settings.FAISCA_ALLOWED_APPS
        self.app_models = self._get_available_models()
        self.model_keywords = self._create_model_keywords()

    def _get_available_models(self):
        """Lista todos os modelos disponíveis no sistema"""
        models_info = {}
        for app in self.allowed_apps:
            try:
                app_config = apps.get_app_config(app)
                models_info[app] = {
                    'verbose_name': app_config.verbose_name,
                    'models': []
                }
                for model in app_config.get_models():
                    models_info[app]['models'].append({
                        'name': model.__name__,
                        'verbose_name': model._meta.verbose_name,
                        'fields': [f.name for f in model._meta.fields]
                    })
            except Exception as e:
                print(f"Erro ao carregar app {app}: {str(e)}")
                continue
        return models_info

    def _create_model_keywords(self):
        """Cria um dicionário de palavras-chave para modelos"""
        keywords = {}
        for app, info in self.app_models.items():
            for model_info in info['models']:
                keywords[model_info['name'].lower()] = {
                    'app': app,
                    'model': model_info['name'],
                    'verbose_name': f"{info['verbose_name']} - {model_info['verbose_name']}"
                }
        return keywords

    def search_data(self, query):
        """Pesquisa segura nos modelos do sistema"""
        try:
            target_model = self._identify_target_model(query)
            if not target_model:
                return "Não consegui identificar qual dado do sistema você quer consultar."
            Model = apps.get_model(target_model['app'], target_model['model'])
            filters = self._build_filters(query, Model)
            results = Model.objects.filter(**filters)[:20]  # Limita a 20 resultados
            if not results.exists():
                return f"Nenhum resultado encontrado para '{query}' no modelo {target_model['verbose_name']}"
            data = [self._format_result(result) for result in results]
            analysis = self._analyze_data(data, query)
            return {
                'model': target_model['verbose_name'],
                'count': results.count(),
                'analysis': analysis,
                'sample_data': data[:3]  # Mostra apenas 3 amostras
            }
        except FieldError as e:
            return f"Erro na consulta: campo inválido - {str(e)}"
        except Exception as e:
            return f"Erro ao processar a consulta: {str(e)}"

    def _identify_target_model(self, query):
        """Identifica qual modelo o usuário está se referindo"""
        for keyword, model_info in self.model_keywords.items():
            if keyword in query.lower():
                return model_info
        return None

    def _build_filters(self, query, model):
        """Converte a query em filtros ORM básicos"""
        filters = {}
        if 'últimos' in query and 'dias' in query:
            try:
                days = int(query.split('últimos')[1].split('dias')[0].strip())
                if hasattr(model, 'created_at'):
                    filters['created_at__gte'] = timezone.now() - timezone.timedelta(days=days)
            except:
                pass
        return filters

    def _format_result(self, instance):
        """Formata uma instância do modelo para exibição"""
        data = {}
        for field in instance._meta.fields:
            if field.name in ['password', 'token']:
                continue
            value = getattr(instance, field.name)
            if hasattr(value, 'strftime'):
                value = value.strftime('%d/%m/%Y %H:%M')
            elif hasattr(value, 'all'):
                value = [str(item) for item in value.all()[:3]]
            data[field.verbose_name] = value
        return data

    def _analyze_data(self, data, query):
        """Gera uma análise dos dados encontrados"""
        prompt = f"""
        Analise os seguintes dados do sistema com base na pergunta do usuário:
        Pergunta original: "{query}"
        Dados encontrados (amostra):
        {json.dumps(data, indent=2)}
        Forneça:
        1. Um resumo dos dados encontrados
        2. Padrões ou insights relevantes
        3. Resposta direta à pergunta do usuário, se possível
        Formato de resposta (use markdown):
        ### Resumo
        - [resumo aqui]
        ### Insights
        - [insights aqui]
        ### Resposta
        [resposta direta aqui]
        """
        return self.llm.invoke(prompt).content

    def generate_report(self, query):
        """Gera um relatório completo com análise de dados"""
        data = self.search_data(query)
        if isinstance(data, str):
            return data
        prompt = f"""
        Com base nos dados abaixo, gere um relatório completo em markdown:
        Pergunta original: "{query}"
        Modelo consultado: {data['model']}
        Total de registros: {data['count']}
        Dados (amostra):
        {json.dumps(data['sample_data'], indent=2)}
        Análise preliminar:
        {data['analysis']}
        Estrutura do relatório:
        1. Título com a pergunta
        2. Metodologia (como os dados foram obtidos)
        3. Principais achados
        4. Análise detalhada
        5. Recomendações (se aplicável)
        6. Limitações
        """
        return self.llm.invoke(prompt).content