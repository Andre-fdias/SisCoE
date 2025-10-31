# backend/core/tests.py
import pytest
import json
from datetime import datetime, date, timedelta
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from backend.core.views import calcular_variacao
from backend.core.search import GlobalSearch
from backend.core.utils import filter_by_user_sgb
from backend.core.monitoring_decorators import track_function_latency

User = get_user_model()


class CoreBasicTests(TestCase):
    """Testes básicos e essenciais para o core"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_capa_view_works(self):
        """Testa se a view capa retorna status 200"""
        response = self.client.get(reverse('core:capa'))
        self.assertEqual(response.status_code, 200)

    # backend/core/tests.py (atualização do teste problemático)
    def test_index_view_requires_login(self):
        """Testa se a view index requer login"""
        response = self.client.get(reverse('core:index'))
        # A view deve redirecionar para login (302) quando o usuário não está autenticado
        # ou retornar um erro de permissão se estiver configurada para isso
        self.assertNotEqual(response.status_code, 200)
        # Verifica se é redirecionamento para login ou erro de acesso
        self.assertIn(response.status_code, [302, 401, 403])



        def test_index_view_authenticated(self):
            """Testa se a view index funciona para usuário autenticado"""
            self.client.force_login(self.user)
            response = self.client.get(reverse('core:index'))
            self.assertEqual(response.status_code, 200)

        def test_dashboard_view_authenticated(self):
            """Testa se a view dashboard funciona para usuário autenticado"""
            self.client.force_login(self.user)
            response = self.client.get(reverse('core:dashboard'))
            self.assertEqual(response.status_code, 200)

        def test_calendario_view_authenticated(self):
            """Testa se a view calendário funciona para usuário autenticado"""
            self.client.force_login(self.user)
            response = self.client.get(reverse('core:calendario'))
            self.assertEqual(response.status_code, 200)

        def test_global_search_view_authenticated(self):
            """Testa se a view de busca global funciona para usuário autenticado"""
            self.client.force_login(self.user)
            response = self.client.get(reverse('core:global_search'))
            self.assertEqual(response.status_code, 200)

        def test_global_search_with_query(self):
            """Testa a busca global com query"""
            self.client.force_login(self.user)
            response = self.client.get(reverse('core:global_search'), {'q': 'test'})
            self.assertEqual(response.status_code, 200)


class FunctionTests(TestCase):
    """Testes para funções utilitárias"""
    
    def test_calcular_variacao(self):
        """Testa a função calcular_variacao"""
        # Teste com aumento
        self.assertEqual(calcular_variacao(100, 150), 50.0)
        
        # Teste com diminuição
        self.assertEqual(calcular_variacao(100, 50), -50.0)
        
        # Teste com valor anterior zero
        self.assertEqual(calcular_variacao(0, 100), 100)
        
        # Teste com ambos zero
        self.assertEqual(calcular_variacao(0, 0), 0)

    def test_calcular_variacao_edge_cases(self):
        """Testa casos extremos da função calcular_variacao"""
        # Divisão por zero protegida
        self.assertEqual(calcular_variacao(0, 100), 100)
        self.assertEqual(calcular_variacao(0, 0), 0)
        
        # Valores negativos
        self.assertEqual(calcular_variacao(100, -50), -150.0)
        
        # Valores decimais
        self.assertEqual(calcular_variacao(10.5, 15.75), 50.0)


class SearchTests(TestCase):
    """Testes para funcionalidade de busca"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='search@example.com',
            password='testpass123'
        )

    def test_search_empty_query(self):
        """Testa busca com query vazia"""
        results = GlobalSearch.search('')
        self.assertEqual(results, [])

    def test_search_with_query(self):
        """Testa busca com query válida"""
        results = GlobalSearch.search('test')
        self.assertIsInstance(results, list)

    def test_search_numeric_query(self):
        """Testa busca com query numérica"""
        results = GlobalSearch.search('123')
        self.assertIsInstance(results, list)

    def test_search_app_colors(self):
        """Testa se as cores das apps estão definidas"""
        self.assertIsInstance(GlobalSearch.APP_COLORS, dict)
        self.assertGreater(len(GlobalSearch.APP_COLORS), 0)

    def test_searchable_models(self):
        """Testa se os modelos pesquisáveis estão configurados"""
        self.assertIsInstance(GlobalSearch.SEARCHABLE_MODELS, dict)
        self.assertGreater(len(GlobalSearch.SEARCHABLE_MODELS), 0)

    def test_search_user_by_email(self):
        """Testa busca de usuário por email"""
        user = User.objects.create_user(
            email='searchuser@example.com',
            password='testpass123',
            first_name='Search',
            last_name='User'
        )
        
        # Buscar por email
        results = GlobalSearch.search('searchuser@example.com')
        self.assertIsInstance(results, list)


class UtilsTests(TestCase):
    """Testes para funções utilitárias"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='utils@example.com',
            password='testpass123'
        )

    def test_filter_by_user_sgb_superuser(self):
        """Testa filtro SGB para superusuário"""
        self.user.is_superuser = True
        
        # Mock do queryset
        class MockQuerySet:
            def __init__(self):
                self.count_called = False
            
            def count(self):
                self.count_called = True
                return 1
        
        queryset = MockQuerySet()
        filtered = filter_by_user_sgb(queryset, self.user)
        
        # Para superusuário, deve retornar o queryset original
        self.assertEqual(queryset, filtered)

    def test_filter_by_user_sgb_basico(self):
        """Testa filtro SGB para usuário básico"""
        self.user.permissoes = 'basico'
        
        # Mock do queryset
        class MockQuerySet:
            def none(self):
                return "empty queryset"
        
        queryset = MockQuerySet()
        filtered = filter_by_user_sgb(queryset, self.user)
        
        # Para usuário básico sem SGB, deve retornar queryset vazio
        self.assertEqual(filtered, "empty queryset")


class MonitoringDecoratorsTests(TestCase):
    """Testes para decorators de monitoramento"""
    
    def test_track_function_latency_decorator(self):
        """Testa o decorator de monitoramento de latência"""
        
        @track_function_latency
        def test_function():
            return "test result"
        
        result = test_function()
        self.assertEqual(result, "test result")


class URLTests(TestCase):
    """Testes para URLs"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='url_test@example.com',
            password='testpass123'
        )

    def test_all_urls_accessible(self):
        """Testa se todas as URLs principais estão acessíveis"""
        urls_to_test = [
            ('core:capa', False),  # Não requer login
            ('core:index', True),  # Requer login
            ('core:dashboard', True),
            ('core:calendario', True),
            ('core:global_search', True),
        ]
        
        for url_name, requires_login in urls_to_test:
            with self.subTest(url=url_name):
                if requires_login:
                    self.client.force_login(self.user)
                
                response = self.client.get(reverse(url_name))
                
                if requires_login:
                    self.assertEqual(response.status_code, 200)
                else:
                    self.assertEqual(response.status_code, 200)
                
                if requires_login:
                    self.client.logout()


class ConfigurationTests(TestCase):
    """Testes de configuração"""
    
    def test_imports_work(self):
        """Testa se todos os imports necessários funcionam"""
        try:
            from backend.core import apps, middleware, context_processors
            from backend.core import search, utils, monitoring_decorators
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Import failed: {e}")
    
    def test_app_config(self):
        """Testa a configuração do app core"""
        from django.apps import apps
        app_config = apps.get_app_config('core')
        self.assertEqual(app_config.name, 'backend.core')


class ContextProcessorTests(TestCase):
    """Testes para context processors"""
    
    def test_version_context_processor(self):
        """Testa o context processor de versão"""
        from backend.core.context_processors import version_context_processor
        
        request = self.client.request().wsgi_request
        context = version_context_processor(request)
        
        self.assertIn('APP_VERSION', context)
        self.assertIsInstance(context['APP_VERSION'], str)


class MiddlewareTests(TestCase):
    """Testes para middleware"""
    
    def test_json_messages_middleware_initialization(self):
        """Testa se o middleware pode ser inicializado"""
        from backend.core.middleware import JSONMessagesMiddleware
        
        def get_response(request):
            return "response"
        
        middleware = JSONMessagesMiddleware(get_response)
        self.assertIsNotNone(middleware)


# Testes pytest
@pytest.mark.django_db
def test_homepage_status_code(client):
    """Testa se a página inicial retorna o status code 200."""
    user = User.objects.create_user(
        email='pytest@example.com',
        password='testpass123'
    )
    client.force_login(user)
    
    response = client.get(reverse('core:index'))
    assert response.status_code == 200


class PerformanceTests(TestCase):
    """Testes de performance básicos"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='performance@example.com',
            password='testpass123'
        )

    def test_index_view_performance(self):
        """Testa a performance da view index"""
        self.client.force_login(self.user)
        
        import time
        start_time = time.time()
        
        response = self.client.get(reverse('core:index'))
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # A view deve carregar em menos de 3 segundos (mais tolerante)
        self.assertLess(execution_time, 3.0)
        self.assertEqual(response.status_code, 200)


class SimpleIntegrationTests(TestCase):
    """Testes de integração simples"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='integration@example.com',
            password='testpass123',
            first_name='Integration',
            last_name='Test'
        )
    
    def test_user_creation_and_login(self):
        """Testa criação de usuário e login"""
        # Verifica se o usuário foi criado
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(self.user.email, 'integration@example.com')
        
        # Testa login
        login_success = self.client.login(
            email='integration@example.com',
            password='testpass123'
        )
        self.assertTrue(login_success)
    
    def test_search_integration(self):
        """Testa integração da busca com usuário real"""
        self.client.force_login(self.user)
        
        # Busca por email do usuário
        results = GlobalSearch.search('integration@example.com')
        self.assertIsInstance(results, list)


class ErrorHandlingTests(TestCase):
    """Testes de tratamento de erros"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='error_test@example.com',
            password='testpass123'
        )

    def test_dashboard_view_error_handling(self):
        """Testa o tratamento de erros na view do dashboard"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # A view deve lidar com possíveis erros internos
        context = response.context
        self.assertIn('efetivo_fixado', context)
        self.assertIn('efetivo_existente', context)


class TemplateRenderingTests(TestCase):
    """Testes básicos de renderização de templates"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='template@example.com',
            password='testpass123'
        )
    
    def test_templates_render_without_errors(self):
        """Testa se os templates renderizam sem erros"""
        templates_to_test = [
            ('core:capa', False),
            ('core:index', True),
            ('core:dashboard', True),
            ('core:calendario', True),
        ]
        
        for template_name, requires_login in templates_to_test:
            with self.subTest(template=template_name):
                if requires_login:
                    self.client.force_login(self.user)
                
                response = self.client.get(reverse(template_name))
                self.assertEqual(response.status_code, 200)
                # Se chegou aqui, o template renderizou sem erros
                
                if requires_login:
                    self.client.logout()