# backend/faisca/services.py
import json
from django.apps import apps
from langchain_groq import ChatGroq
from langchain.agents import Tool
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from .models import SystemAgentInteraction

class SistemaAgent:
    def __init__(self, user):
        self.user = user
        self.llm = ChatGroq(
            model='llama-3.2-90b-vision-preview',
            temperature=0.3
        )
        self.tools = self._carregar_ferramentas()
        
    def _carregar_ferramentas(self):
        return [
            Tool(
                name="pesquisar_dados",
                func=self._pesquisar_dados,
                description="Busca dados em qualquer modelo do sistema"
            ),
            Tool(
                name="gerar_relatorio",
                func=self._gerar_relatorio,
                description="Gera relatórios estruturados com dados do sistema"
            )
        ]

    def _pesquisar_dados(self, query):
        """Pesquisa síncrona em todos os modelos instalados"""
        try:
            app_models = {
                'crm': ['Cliente', 'Interacao'],
                'efetivo': ['Militar', 'Lotacao'],
                'faisca': ['Evento'],
                # Adicione outros modelos
            }
            
            resultados = {}
            for app, models in app_models.items():
                for model_name in models:
                    Model = apps.get_model(f'backend.{app}', model_name)
                    resultados[f'{app}_{model_name}'] = list(
                        Model.objects.filter(**self._parse_query(query))[:20].values()
                    )
            return json.dumps(resultados, default=str)
        
        except Exception as e:
            return f"Erro na pesquisa: {str(e)}"

    def _parse_query(self, query):
        """Converte consulta natural para filtros Django ORM"""
        # Implementação básica - pode ser expandida
        filters = {}
        if 'última semana' in query:
            filters['data__gte'] = timezone.now() - timezone.timedelta(days=7)
        if 'alto risco' in query:
            filters['risco__gte'] = 7
        return filters

    def _gerar_relatorio(self, query):
        """Geração síncrona de relatórios"""
        prompt = PromptTemplate(
            input_variables=['dados'],
            template="""
            Gere um relatório em markdown com os seguintes dados:
            {dados}
            
            Formato requerido:
            # Relatório
            ## Seção Principal
            - Análise
            - Estatísticas
            ## Recomendações
            """
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        dados = self._pesquisar_dados(query)
        return chain.run(dados=dados)

    def executar_comando(self, comando):
        """Fluxo principal de execução síncrona"""
        try:
            # Registrar interação
            interacao = SystemAgentInteraction.objects.create(
                user=self.user,
                comando=comando,
                tipo_acao=self._determinar_tipo_acao(comando)
            )
            
            # Executar comando
            resultado = self._processar_comando(comando)
            
            # Atualizar registro
            interacao.resposta = resultado[:5000]
            interacao.executado_com_sucesso = True
            interacao.save()
            
            return resultado
        
        except Exception as e:
            interacao.resposta = f"Erro: {str(e)}"
            interacao.save()
            return str(e)

    def _determinar_tipo_acao(self, comando):
        if 'relatório' in comando.lower():
            return 'RELATORIO'
        if 'analisar' in comando.lower():
            return 'ANALISE'
        return 'PESQUISA'

    def _processar_comando(self, comando):
        # Lógica de roteamento de comandos
        if 'relatório' in comando.lower():
            return self._gerar_relatorio(comando)
        return self._pesquisar_dados(comando)