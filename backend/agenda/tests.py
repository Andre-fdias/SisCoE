from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Lembrete, Tarefa
from .forms import LembreteForm, TarefaForm

User = get_user_model()


class AgendaModelsTest(TestCase):
    def setUp(self):
        """Configuração inicial para os testes"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.lembrete_data = {
            'titulo': 'Lembrete Teste',
            'descricao': 'Descrição do lembrete teste',
            'data': timezone.now() + timedelta(days=1),
            'cor': '#FF0000',
            'user': self.user
        }
        
        self.tarefa_data = {
            'titulo': 'Tarefa Teste',
            'descricao': 'Descrição da tarefa teste',
            'data_inicio': timezone.now(),
            'data_fim': timezone.now() + timedelta(days=2),
            'cor': '#00FF00',
            'user': self.user
        }

    def test_criar_lembrete(self):
        """Testa a criação de um lembrete"""
        lembrete = Lembrete.objects.create(**self.lembrete_data)
        
        self.assertEqual(lembrete.titulo, 'Lembrete Teste')
        self.assertEqual(lembrete.descricao, 'Descrição do lembrete teste')
        self.assertEqual(lembrete.tipo, 'Lembrete')
        self.assertEqual(lembrete.cor, '#FF0000')
        self.assertEqual(lembrete.user, self.user)
        self.assertEqual(str(lembrete), 'Lembrete Teste')

    def test_criar_tarefa(self):
        """Testa a criação de uma tarefa"""
        tarefa = Tarefa.objects.create(**self.tarefa_data)
        
        self.assertEqual(tarefa.titulo, 'Tarefa Teste')
        self.assertEqual(tarefa.descricao, 'Descrição da tarefa teste')
        self.assertEqual(tarefa.tipo, 'Tarefa')
        self.assertEqual(tarefa.cor, '#00FF00')
        self.assertEqual(tarefa.user, self.user)
        self.assertEqual(str(tarefa), 'Tarefa Teste')

    def test_validacao_tarefa_data_invalida(self):
        """Testa a validação de tarefa com data de término anterior à data de início"""
        from django.core.exceptions import ValidationError
        
        tarefa = Tarefa(
            titulo='Tarefa Data Inválida',
            descricao='Descrição',
            data_inicio=timezone.now() + timedelta(days=2),
            data_fim=timezone.now(),
            user=self.user
        )
        
        with self.assertRaises(ValidationError):
            tarefa.full_clean()

    def test_get_search_result_lembrete(self):
        """Testa o método get_search_result do Lembrete"""
        lembrete = Lembrete.objects.create(**self.lembrete_data)
        search_result = lembrete.get_search_result()
        
        self.assertEqual(search_result['title'], 'Lembrete Teste')
        self.assertIn('Descrição', search_result['fields'])
        self.assertIn('Data', search_result['fields'])
        # Verifica se a descrição foi truncada
        self.assertLessEqual(len(search_result['fields']['Descrição']), 100)

    def test_get_search_result_tarefa(self):
        """Testa o método get_search_result da Tarefa"""
        tarefa = Tarefa.objects.create(**self.tarefa_data)
        search_result = tarefa.get_search_result()
        
        self.assertEqual(search_result['title'], 'Tarefa Teste')
        self.assertIn('Descrição', search_result['fields'])
        self.assertIn('Início', search_result['fields'])
        self.assertIn('Fim', search_result['fields'])
        # Verifica se a descrição foi truncada
        self.assertLessEqual(len(search_result['fields']['Descrição']), 100)


class AgendaFormsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    def test_lembrete_form_valido(self):
        """Testa LembreteForm com dados válidos"""
        form_data = {
            'titulo': 'Lembrete Form Test',
            'descricao': 'Descrição do lembrete',
            'data': timezone.now() + timedelta(days=1),
            'cor': '#0000FF'
        }
        form = LembreteForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_lembrete_form_invalido(self):
        """Testa LembreteForm com dados inválidos"""
        form_data = {
            'titulo': '',  # Campo obrigatório vazio
            'descricao': 'Descrição',
            'data': timezone.now() + timedelta(days=1),
            'cor': '#0000FF'
        }
        form = LembreteForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('titulo', form.errors)

    def test_tarefa_form_valido(self):
        """Testa TarefaForm com dados válidos"""
        form_data = {
            'titulo': 'Tarefa Form Test',
            'descricao': 'Descrição da tarefa',
            'data_inicio': timezone.now() + timedelta(days=1),
            'data_fim': timezone.now() + timedelta(days=2),
            'cor': '#00FF00'
        }
        form = TarefaForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_tarefa_form_data_invalida(self):
        """Testa TarefaForm com data de término anterior à data de início"""
        form_data = {
            'titulo': 'Tarefa Data Inválida',
            'descricao': 'Descrição',
            'data_inicio': timezone.now() + timedelta(days=2),
            'data_fim': timezone.now() + timedelta(days=1),  # Data fim anterior
            'cor': '#00FF00'
        }
        form = TarefaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_tarefa_form_datas_obrigatorias(self):
        """Testa TarefaForm com datas faltando"""
        form_data = {
            'titulo': 'Tarefa Sem Data',
            'descricao': 'Descrição',
            'cor': '#00FF00'
            # datas_inicio e data_fim faltando
        }
        form = TarefaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('data_inicio', form.errors)
        self.assertIn('data_fim', form.errors)


class AgendaViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.lembrete = Lembrete.objects.create(
            titulo='Lembrete Existente',
            descricao='Descrição do lembrete existente para teste de visualização no calendário e outras funcionalidades do sistema.',
            data=timezone.now() + timedelta(days=1),
            user=self.user
        )
        
        self.tarefa = Tarefa.objects.create(
            titulo='Tarefa Existente',
            descricao='Descrição da tarefa existente para teste de visualização no calendário e outras funcionalidades do sistema.',
            data_inicio=timezone.now(),
            data_fim=timezone.now() + timedelta(days=2),
            user=self.user
        )

    def test_calendario_view_autenticado(self):
        """Testa acesso à view calendario com usuário autenticado"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('agenda:calendario'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calendario.html')
        self.assertContains(response, 'Lembrete Existente')
        self.assertContains(response, 'Tarefa Existente')

    def test_calendario_view_nao_autenticado(self):
        """Testa acesso à view calendario sem autenticação (deve redirecionar)"""
        response = self.client.get(reverse('agenda:calendario'))
        self.assertEqual(response.status_code, 302)  # Redirecionamento para login

    def test_criar_lembrete_view(self):
        """Testa a criação de lembrete via view"""
        self.client.login(email='test@example.com', password='testpass123')
        
        data = {
            'titulo': 'Novo Lembrete',
            'descricao': 'Descrição novo lembrete',
            'data': (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
            'cor': '#FF0000'
        }
        
        response = self.client.post(
            reverse('agenda:lembrete_novo'),
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertEqual(Lembrete.objects.count(), 2)

    def test_criar_lembrete_view_invalido(self):
        """Testa a criação de lembrete inválido via view"""
        self.client.login(email='test@example.com', password='testpass123')
        
        data = {
            'titulo': '',  # Título vazio - inválido
            'descricao': 'Descrição',
            'data': (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
            'cor': '#FF0000'
        }
        
        response = self.client.post(
            reverse('agenda:lembrete_novo'),
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertIn('errors', response_data)

    def test_criar_tarefa_view(self):
        """Testa a criação de tarefa via view"""
        self.client.login(email='test@example.com', password='testpass123')
        
        data = {
            'titulo': 'Nova Tarefa',
            'descricao': 'Descrição nova tarefa',
            'data_inicio': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_fim': (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
            'cor': '#00FF00'
        }
        
        response = self.client.post(
            reverse('agenda:tarefa_nova'),
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertEqual(Tarefa.objects.count(), 2)

    def test_excluir_lembrete_view(self):
        """Testa a exclusão de lembrete via view"""
        self.client.login(email='test@example.com', password='testpass123')
        
        response = self.client.post(
            reverse('agenda:excluir_lembrete', args=[self.lembrete.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertEqual(Lembrete.objects.count(), 0)

    def test_excluir_tarefa_view(self):
        """Testa a exclusão de tarefa via view"""
        self.client.login(email='test@example.com', password='testpass123')
        
        response = self.client.post(
            reverse('agenda:excluir_tarefa', args=[self.tarefa.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertEqual(Tarefa.objects.count(), 0)

    def test_eventos_proximos_view(self):
        """Testa a view de eventos próximos"""
        self.client.login(email='test@example.com', password='testpass123')
        
        response = self.client.get(reverse('agenda:eventos_proximos'))
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('eventos', response_data)
        
        # Deve retornar os eventos criados no setUp
        self.assertEqual(len(response_data['eventos']), 2)

    def test_editar_lembrete_view(self):
        """Testa a edição de lembrete"""
        self.client.login(email='test@example.com', password='testpass123')
        
        url = reverse('agenda:lembrete_editar', args=[self.lembrete.pk])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lembrete_form.html')

    def test_protecao_usuario_lembrete(self):
        """Testa que usuário não pode acessar lembretes de outros usuários"""
        outro_user = User.objects.create_user(
            email='outro@example.com',
            password='outropass123'
        )
        
        self.client.login(email='outro@example.com', password='outropass123')
        
        # Tentativa de excluir lembrete de outro usuário
        response = self.client.post(
            reverse('agenda:excluir_lembrete', args=[self.lembrete.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertEqual(Lembrete.objects.count(), 1)  # Lembrete não foi excluído


class AgendaIntegrationTest(TestCase):
    """Testes de integração para fluxos completos"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(email='test@example.com', password='testpass123')

    def test_fluxo_completo_lembrete(self):
        """Testa o fluxo completo: criar → listar → excluir lembrete"""
        # Criar lembrete
        data = {
            'titulo': 'Lembrete Integração',
            'descricao': 'Descrição integração',
            'data': (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
            'cor': '#123456'
        }
        
        response = self.client.post(
            reverse('agenda:lembrete_novo'),
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertTrue(response.json()['success'])
        
        # Verificar se aparece no calendário
        response = self.client.get(reverse('agenda:calendario'))
        self.assertContains(response, 'Lembrete Integração')
        
        # Excluir lembrete
        lembrete = Lembrete.objects.get(titulo='Lembrete Integração')
        response = self.client.post(
            reverse('agenda:excluir_lembrete', args=[lembrete.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertTrue(response.json()['success'])
        self.assertEqual(Lembrete.objects.count(), 0)

    def test_fluxo_completo_tarefa(self):
        """Testa o fluxo completo: criar → listar → excluir tarefa"""
        # Criar tarefa
        data = {
            'titulo': 'Tarefa Integração',
            'descricao': 'Descrição integração',
            'data_inicio': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_fim': (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
            'cor': '#654321'
        }
        
        response = self.client.post(
            reverse('agenda:tarefa_nova'),
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertTrue(response.json()['success'])
        
        # Verificar se aparece no calendário
        response = self.client.get(reverse('agenda:calendario'))
        self.assertContains(response, 'Tarefa Integração')
        
        # Excluir tarefa
        tarefa = Tarefa.objects.get(titulo='Tarefa Integração')
        response = self.client.post(
            reverse('agenda:excluir_tarefa', args=[tarefa.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertTrue(response.json()['success'])
        self.assertEqual(Tarefa.objects.count(), 0)