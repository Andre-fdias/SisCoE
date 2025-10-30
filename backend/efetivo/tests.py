# backend/efetivo/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, date, timedelta
import json

from .models import (
    Cadastro, DetalhesSituacao, Promocao, Imagem, 
    CatEfetivo, HistoricoCatEfetivo, HistoricoDetalhesSituacao,
    HistoricoPromocao
)

User = get_user_model()


class BaseTestCase(TestCase):
    """Classe base para configuração comum dos testes"""
    
    def setUp(self):
        """Configuração inicial para todos os testes"""
        # Criar usuário de teste com permissões
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Adicionar permissões necessárias para o usuário
        self.user.permissoes = {
            'nivel_acesso': 'gestor',
            'sgb_permitidos': ['EM', '1ºSGB', '2ºSGB', '3ºSGB', '4ºSGB', '5ºSGB']
        }
        self.user.save()
        
        # Criar superusuário para testes que requerem permissões elevadas
        self.superuser = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        
        # Criar cadastro militar de teste com todos os campos obrigatórios
        self.cadastro = Cadastro.objects.create(
            re='123456',
            dig='7',
            nome='João da Silva',
            nome_de_guerra='Silva',
            genero='Masculino',
            nasc=date(1990, 1, 1),
            matricula=date(2010, 1, 1),
            admissao=date(2010, 1, 1),
            previsao_de_inatividade=date(2040, 1, 1),
            cpf='123.456.789-00',
            rg='123456789',
            tempo_para_averbar_inss=5,
            tempo_para_averbar_militar=3,
            email='joao.silva@policiamilitar.sp.gov.br',
            telefone='(11) 99999-9999',
            alteracao='Inclusão',
            user=self.user
        )
        
        # Criar situação funcional
        self.detalhes_situacao = DetalhesSituacao.objects.create(
            cadastro=self.cadastro,
            situacao='Efetivo',
            sgb='EM',
            posto_secao='703150000 - CMT',
            funcao='CMT',
            op_adm='Administrativo',
            prontidao='VERDE',
            apresentacao_na_unidade=date(2020, 1, 1),
            usuario_alteracao=self.user
        )
        
        # Criar promoção
        self.promocao = Promocao.objects.create(
            cadastro=self.cadastro,
            posto_grad='Cap PM',
            quadro='Oficiais',
            grupo='Cap',
            ultima_promocao=date(2023, 1, 1),
            usuario_alteracao=self.user
        )
        
        # Criar categoria de efetivo
        self.categoria_efetivo = CatEfetivo.objects.create(
            cadastro=self.cadastro,
            tipo='ATIVO',
            data_inicio=date(2020, 1, 1),
            usuario_cadastro=self.user,
            ativo=True
        )
        
        self.client = Client()


class SimpleModelTests(TestCase):
    """Testes simples de modelos"""
    
    def test_user_creation(self):
        """Testa criação básica de usuário"""
        user = User.objects.create_user(
            email='simple@test.com',
            password='testpass123'
        )
        self.assertEqual(user.email, 'simple@test.com')
    
    def test_cadastro_creation(self):
        """Testa criação básica de cadastro"""
        user = User.objects.create_user(
            email='cadastro@test.com',
            password='testpass123'
        )
        
        cadastro = Cadastro.objects.create(
            re='123456',
            dig='7',
            nome='Test Militar',
            nome_de_guerra='Test',
            genero='Masculino',
            nasc=date(1990, 1, 1),
            matricula=date(2010, 1, 1),
            admissao=date(2010, 1, 1),
            previsao_de_inatividade=date(2040, 1, 1),
            cpf='123.456.789-00',
            rg='123456789',
            tempo_para_averbar_inss=5,
            tempo_para_averbar_militar=3,
            email='test@policiamilitar.sp.gov.br',
            telefone='(11) 99999-9999',
            alteracao='Inclusão',
            user=user
        )
        
        self.assertEqual(cadastro.re, '123456')
        self.assertEqual(str(cadastro), '123456 7 Test')
    
    def test_detalhes_situacao_str_representation(self):
        """Testa a representação string dos detalhes de situação"""
        user = User.objects.create_user(
            email='situacao@example.com',
            password='testpass123'
        )
        
        cadastro = Cadastro.objects.create(
            re='888888',
            dig='8',
            nome='Situacao Test',
            nome_de_guerra='Situacao',
            genero='Masculino',
            nasc=date(1990, 1, 1),
            matricula=date(2010, 1, 1),
            admissao=date(2010, 1, 1),
            previsao_de_inatividade=date(2040, 1, 1),
            cpf='888.888.888-88',
            rg='888888888',
            tempo_para_averbar_inss=5,
            tempo_para_averbar_militar=3,
            email='situacao@policiamilitar.sp.gov.br',
            telefone='(11) 88888-8888',
            alteracao='Inclusão',
            user=user
        )
        
        detalhes = DetalhesSituacao.objects.create(
            cadastro=cadastro,
            situacao='Efetivo',
            sgb='EM',
            usuario_alteracao=user
        )
        
        self.assertEqual(str(detalhes), '888888 - Efetivo')


class PropertyTests(TestCase):
    """Testes focados em propriedades calculadas"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='props@example.com',
            password='testpass123'
        )
        
        # Criar cadastro com datas específicas para testar propriedades
        self.cadastro = Cadastro.objects.create(
            re='555555',
            dig='5',
            nome='Property Test',
            nome_de_guerra='Property',
            genero='Masculino',
            nasc=date(1990, 1, 15),
            matricula=date(2010, 6, 1),
            admissao=date(2010, 6, 1),
            previsao_de_inatividade=date(2025, 1, 1),  # Data futura próxima
            cpf='555.555.555-55',
            rg='555555555',
            tempo_para_averbar_inss=10,
            tempo_para_averbar_militar=8,
            email='property@policiamilitar.sp.gov.br',
            telefone='(11) 55555-5555',
            alteracao='Inclusão',
            user=self.user
        )
    
    def test_idade_detalhada(self):
        """Testa o cálculo detalhado da idade"""
        idade = self.cadastro.idade_detalhada
        self.assertIsInstance(idade, str)
        self.assertIn('anos', idade)
    
    def test_previsao_inatividade_dias(self):
        """Testa o cálculo de dias para inatividade"""
        # A propriedade é um método, então precisa ser chamada com ()
        dias = self.cadastro.previsao_de_inatividade_dias()
        self.assertIsInstance(dias, int)
    
    def test_tempo_para_averbar_inss_inteiro(self):
        """Testa a propriedade tempo_para_averbar_inss_inteiro"""
        tempo = self.cadastro.tempo_para_averbar_inss_inteiro
        self.assertIsInstance(tempo, int)
        self.assertEqual(tempo, 10)
    
    def test_tempo_para_averbar_militar_inteiro(self):
        """Testa a propriedade tempo_para_averbar_militar_inteiro"""
        tempo = self.cadastro.tempo_para_averbar_militar_inteiro
        self.assertIsInstance(tempo, int)
        self.assertEqual(tempo, 8)


class ModelTests(BaseTestCase):
    """Testes para os modelos"""
    
    def test_cadastro_creation(self):
        """Testa a criação de um cadastro militar"""
        self.assertEqual(self.cadastro.re, '123456')
        self.assertEqual(self.cadastro.nome_de_guerra, 'Silva')
        self.assertEqual(str(self.cadastro), '123456 7 Silva')
    
    def test_cadastro_properties(self):
        """Testa as propriedades calculadas do cadastro"""
        # Testar idade detalhada
        self.assertIn('anos', self.cadastro.idade_detalhada)
        
        # Testar status de inatividade
        self.assertIsNotNone(self.cadastro.inativa_status)
        
        # Testar última promoção
        self.assertEqual(self.cadastro.ultima_promocao, self.promocao)
    
    def test_detalhes_situacao_creation(self):
        """Testa a criação de detalhes de situação"""
        self.assertEqual(self.detalhes_situacao.situacao, 'Efetivo')
        self.assertEqual(self.detalhes_situacao.sgb, 'EM')
        self.assertIn('anos', self.detalhes_situacao.tempo_na_unidade)
    
    def test_detalhes_situacao_properties(self):
        """Testa as propriedades de detalhes de situação"""
        # Testar badge de situação
        self.assertIn('bg-green-500', self.detalhes_situacao.status)
        
        # Testar badge de prontidão
        self.assertIn('bg-green-500', self.detalhes_situacao.prontidao_badge)
    
    def test_promocao_creation(self):
        """Testa a criação de promoção"""
        self.assertEqual(self.promocao.posto_grad, 'Cap PM')
        self.assertIn('anos', self.promocao.ultima_promocao_detalhada)
    
    def test_categoria_efetivo_creation(self):
        """Testa a criação de categoria de efetivo"""
        self.assertEqual(self.categoria_efetivo.tipo, 'ATIVO')
        self.assertTrue(self.categoria_efetivo.ativo)
    
    def test_categoria_efetivo_properties(self):
        """Testa as propriedades de categoria de efetivo"""
        # Testar badge de tipo
        self.assertIn('bg-green-500', self.categoria_efetivo.tipo_badge)
        
        # Testar status
        self.assertEqual(self.categoria_efetivo.status, 'EM VIGOR')
    
    def test_historico_creation(self):
        """Testa a criação de registros históricos"""
        # Criar histórico de categoria
        historico_cat = HistoricoCatEfetivo.objects.create(
            cat_efetivo=self.categoria_efetivo,
            tipo='ATIVO',
            data_inicio=date(2020, 1, 1),
            usuario_alteracao=self.user
        )
        
        # Criar histórico de situação
        historico_situacao = HistoricoDetalhesSituacao.objects.create(
            cadastro=self.cadastro,
            situacao='Efetivo',
            sgb='EM',
            usuario_alteracao=self.user
        )
        
        # Criar histórico de promoção
        historico_promocao = HistoricoPromocao.objects.create(
            cadastro=self.cadastro,
            posto_grad='Cap PM',
            quadro='Oficiais',
            grupo='Cap',
            ultima_promocao=date(2023, 1, 1),
            usuario_alteracao=self.user
        )
        
        self.assertEqual(historico_cat.tipo, 'ATIVO')
        self.assertEqual(historico_situacao.situacao, 'Efetivo')
        self.assertEqual(historico_promocao.posto_grad, 'Cap PM')


class PublicViewTests(TestCase):
    """Testes para views públicas ou que não requerem permissões especiais"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='public@example.com',
            password='testpass123'
        )
        self.client = Client()
    
    def test_pagina_buscar_militar(self):
        """Testa acesso à página de buscar militar"""
        response = self.client.get(reverse('efetivo:buscar_militar_page'))
        self.assertEqual(response.status_code, 200)


class AuthenticationTests(TestCase):
    """Testes de autenticação básica"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='auth@example.com',
            password='testpass123'
        )
        self.client = Client()
    
    def test_login_required_redirect(self):
        """Testa que views protegidas redirecionam para login"""
        response = self.client.get(reverse('efetivo:cadastrar_militar'))
        self.assertEqual(response.status_code, 302)  # Redireciona para login


class FormValidationTests(TestCase):
    """Testes de validação de formulários"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='validation@example.com',
            password='testpass123'
        )
    
    def test_cadastro_cpf_duplicado(self):
        """Testa que não permite CPF duplicado"""
        # Primeiro cadastro
        cadastro1 = Cadastro.objects.create(
            re='111111',
            dig='1',
            nome='Primeiro',
            nome_de_guerra='Primeiro',
            genero='Masculino',
            nasc=date(1990, 1, 1),
            matricula=date(2010, 1, 1),
            admissao=date(2010, 1, 1),
            previsao_de_inatividade=date(2040, 1, 1),
            cpf='111.111.111-11',
            rg='111111111',
            tempo_para_averbar_inss=5,
            tempo_para_averbar_militar=3,
            email='primeiro@policiamilitar.sp.gov.br',
            telefone='(11) 11111-1111',
            alteracao='Inclusão',
            user=self.user
        )
        
        # Tentativa de segundo cadastro com mesmo CPF
        with self.assertRaises(Exception):
            cadastro2 = Cadastro.objects.create(
                re='222222',  # RE diferente
                dig='2',
                nome='Segundo',
                nome_de_guerra='Segundo',
                genero='Masculino',
                nasc=date(1991, 1, 1),
                matricula=date(2011, 1, 1),
                admissao=date(2011, 1, 1),
                previsao_de_inatividade=date(2041, 1, 1),
                cpf='111.111.111-11',  # CPF duplicado
                rg='222222222',
                tempo_para_averbar_inss=6,
                tempo_para_averbar_militar=4,
                email='segundo@policiamilitar.sp.gov.br',
                telefone='(11) 22222-2222',
                alteracao='Inclusão',
                user=self.user
            )


class MetricTests(TestCase):
    """Testes para métricas do Prometheus"""
    
    def test_signal_handlers(self):
        """Testa se os signal handlers estão funcionando"""
        user = User.objects.create_user(
            email='metrics@example.com',
            password='testpass123'
        )
        
        # Criar cadastro
        cadastro = Cadastro.objects.create(
            re='777777',
            dig='7',
            nome='Metrics Test',
            nome_de_guerra='Metrics',
            genero='Masculino',
            nasc=date(1990, 1, 1),
            matricula=date(2010, 1, 1),
            admissao=date(2010, 1, 1),
            previsao_de_inatividade=date(2040, 1, 1),
            cpf='777.777.777-77',
            rg='777777777',
            tempo_para_averbar_inss=5,
            tempo_para_averbar_militar=3,
            email='metrics@policiamilitar.sp.gov.br',
            telefone='(11) 77777-7777',
            alteracao='Inclusão',
            user=user
        )
        
        # Contar situações antes
        count_before = DetalhesSituacao.objects.count()
        
        # Criar nova situação funcional
        nova_situacao = DetalhesSituacao.objects.create(
            cadastro=cadastro,
            situacao='Mov. Interna',
            sgb='2ºSGB',
            usuario_alteracao=user
        )
        
        # Verifica se o objeto foi criado
        self.assertEqual(DetalhesSituacao.objects.count(), count_before + 1)


class APITests(BaseTestCase):
    """Testes para endpoints AJAX/API"""
    
    def test_check_rpt(self):
        """Testa verificação de RPT"""
        self.client.login(email='test@example.com', password='testpass123')
        
        response = self.client.get(reverse('efetivo:check_rpt', args=[self.cadastro.id]))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('exists', data)


# Testes específicos para funcionalidades do sistema
class FunctionalTests(TestCase):
    """Testes funcionais específicos"""
    
    def test_cadastro_search_result(self):
        """Testa o método get_search_result do cadastro"""
        user = User.objects.create_user(
            email='search@example.com',
            password='testpass123'
        )
        
        cadastro = Cadastro.objects.create(
            re='999999',
            dig='9',
            nome='Search Test',
            nome_de_guerra='Search',
            genero='Masculino',
            nasc=date(1990, 1, 1),
            matricula=date(2010, 1, 1),
            admissao=date(2010, 1, 1),
            previsao_de_inatividade=date(2040, 1, 1),
            cpf='999.999.999-99',
            rg='999999999',
            tempo_para_averbar_inss=5,
            tempo_para_averbar_militar=3,
            email='search@policiamilitar.sp.gov.br',
            telefone='(11) 99999-9999',
            alteracao='Inclusão',
            user=user
        )
        
        search_result = cadastro.get_search_result()
        self.assertEqual(search_result['title'], 'Search (999999-9)')
        self.assertEqual(search_result['fields']['RE'], '999999-9')
        self.assertEqual(search_result['fields']['Nome'], 'Search Test')


# Comando para executar os testes específicos:
# python manage.py test backend.efetivo.tests.SimpleModelTests
# python manage.py test backend.efetivo.tests.PropertyTests
# python manage.py test backend.efetivo.tests.PublicViewTests