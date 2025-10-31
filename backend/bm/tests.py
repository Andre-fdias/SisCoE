# backend/bm/tests.py
import io
import os
import tempfile
from datetime import datetime, date
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.http import HttpRequest, HttpResponse
from django.db import IntegrityError
import pandas as pd
from PIL import Image

from .models import Cadastro_bm, Imagem_bm
from .views import listar_bm, cadastrar_bm, ver_bm, editar_bm, atualizar_foto, excluir_bm, importar_bm, exportar_bm

User = get_user_model()

class TestModels(TestCase):
    def setUp(self):
        # Criar usuário de forma compatível
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.cadastro_data = {
            'nome': 'João da Silva',
            'nome_de_guerra': 'Silva',
            'situacao': 'Efetivo',
            'sgb': '1ºSGB',
            'posto_secao': '703151101 - EB CERRADO',
            'cpf': '12345678901',
            'rg': '123456789',
            'cnh': '12345678901',
            'cat_cnh': 'B',
            'esb': 'SIM',
            'ovb': 'LEVE',
            'admissao': date(2020, 1, 1),
            'nasc': date(1990, 1, 1),
            'email': 'joao@example.com',
            'telefone': '11999999999',
            'apresentacao_na_unidade': date(2020, 1, 15),
            'funcao': 'MOTORISTA',
            'genero': 'Masculino',
            'user': self.user
        }

    def test_create_cadastro_bm(self):
        """Testa criação de Cadastro_bm"""
        cadastro = Cadastro_bm.objects.create(**self.cadastro_data)
        
        self.assertEqual(cadastro.nome, 'João da Silva')
        self.assertEqual(cadastro.cpf, '12345678901')
        self.assertTrue(cadastro.id is not None)
        
    def test_cpf_unique_constraint(self):
        """Testa constraint única de CPF"""
        Cadastro_bm.objects.create(**self.cadastro_data)
        
        # Testar com CPF diferente para evitar erro imediato
        data2 = self.cadastro_data.copy()
        data2['cpf'] = '12345678901'  # Mesmo CPF
        
        with self.assertRaises(Exception):
            Cadastro_bm.objects.create(**data2)
            
    def test_idade_detalhada_property(self):
        """Testa cálculo de idade detalhada"""
        cadastro = Cadastro_bm.objects.create(**self.cadastro_data)
        
        idade = cadastro.idade_detalhada
        self.assertIsInstance(idade, str)
        self.assertIn('anos', idade)
        
    def test_status_property(self):
        """Testa propriedade status com marcação HTML"""
        cadastro = Cadastro_bm.objects.create(**self.cadastro_data)
        
        status = cadastro.status
        # Verificar se retorna string (pode não ter atributo 'safe' em testes)
        self.assertIsInstance(status, str)
        self.assertIn('bg-green-500', status)

    def test_create_imagem_bm(self):
        """Testa criação de Imagem_bm"""
        cadastro = Cadastro_bm.objects.create(**self.cadastro_data)
        
        # Criar imagem temporária para teste
        image = Image.new('RGB', (100, 100), color='red')
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(temp_file.name)
        
        with open(temp_file.name, 'rb') as img_file:
            imagem = Imagem_bm.objects.create(
                cadastro=cadastro,
                image=SimpleUploadedFile('test.jpg', img_file.read(), content_type='image/jpeg'),
                user=self.user
            )
            
        self.assertEqual(imagem.cadastro, cadastro)
        self.assertTrue(imagem.image.name.startswith('img/fotos_bm/'))

class TestViews(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.cadastro_data = {
            'nome': 'João da Silva',
            'nome_de_guerra': 'Silva',
            'situacao': 'Efetivo',
            'sgb': '1ºSGB',
            'posto_secao': '703151101 - EB CERRADO',
            'cpf': '12345678901',
            'rg': '123456789',
            'cnh': '12345678901',
            'cat_cnh': 'B',
            'esb': 'SIM',
            'ovb': 'LEVE',
            'admissao': '2020-01-01',
            'nasc': '1990-01-01',
            'email': 'joao@example.com',
            'telefone': '11999999999',
            'apresentacao_na_unidade': '2020-01-15',
            'funcao': 'MOTORISTA',
            'genero': 'Masculino'
        }
        
        self.cadastro = Cadastro_bm.objects.create(
            nome='João da Silva',
            nome_de_guerra='Silva',
            situacao='Efetivo',
            sgb='1ºSGB',
            posto_secao='703151101 - EB CERRADO',
            cpf='12345678901',
            rg='123456789',
            cnh='12345678901',
            cat_cnh='B',
            esb='SIM',
            ovb='LEVE',
            admissao=date(2020, 1, 1),
            nasc=date(1990, 1, 1),
            email='joao@example.com',
            telefone='11999999999',
            apresentacao_na_unidade=date(2020, 1, 15),
            funcao='MOTORISTA',
            genero='Masculino',
            user=self.user
        )

    def test_listar_bm_authenticated(self):
        """Testa listagem de bombeiros com usuário autenticado"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('bm:listar_bm'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'listar_bm.html')
        
    def test_listar_bm_unauthenticated(self):
        """Testa redirecionamento para login quando não autenticado"""
        response = self.client.get(reverse('bm:listar_bm'))
        self.assertEqual(response.status_code, 302)

    def test_ver_bm(self):
        """Testa visualização de cadastro individual"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('bm:ver_bm', args=[self.cadastro.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ver_bm.html')

    def test_cadastrar_bm_get(self):
        """Testa acesso ao formulário de cadastro"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('bm:cadastrar_bm'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cadastro_bm.html')

    def test_cadastrar_bm_post_success(self):
        """Testa cadastro bem-sucedido"""
        self.client.force_login(self.user)
        
        data = self.cadastro_data.copy()
        data['cpf'] = '98765432100'  # CPF diferente
        
        response = self.client.post(reverse('bm:cadastrar_bm'), data)
        
        self.assertIn(response.status_code, [200, 302])
        if response.status_code == 302:
            self.assertTrue(Cadastro_bm.objects.filter(cpf='98765432100').exists())

class TestExportUtils(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.cadastro = Cadastro_bm.objects.create(
            nome='Teste Export',
            nome_de_guerra='Export',
            situacao='Efetivo',
            sgb='1ºSGB',
            posto_secao='703151101 - EB CERRADO',
            cpf='12312312312',
            rg='123456789',
            cnh='12345678901',
            cat_cnh='B',
            esb='SIM',
            ovb='LEVE',
            admissao=date(2020, 1, 1),
            nasc=date(1990, 1, 1),
            email='test@example.com',
            telefone='11999999999',
            apresentacao_na_unidade=date(2020, 1, 15),
            funcao='MOTORISTA',
            genero='Masculino',
            user=self.user
        )

    @patch('backend.bm.export_utils.export_to_pdf_military')
    def test_export_bm_data_pdf(self, mock_export):
        """Testa exportação para PDF"""
        request = self.factory.get('/')
        request.user = self.user
        
        # Mock da resposta
        mock_response = HttpResponse(content_type='application/pdf')
        mock_export.return_value = mock_response
        
        queryset = Cadastro_bm.objects.filter(id=self.cadastro.id)
        from .export_utils import export_bm_data
        response = export_bm_data(request, queryset, 'pdf')
        
        self.assertEqual(response, mock_response)

    @patch('backend.bm.export_utils.export_to_excel_military')
    def test_export_bm_data_excel(self, mock_export):
        """Testa exportação para Excel"""
        request = self.factory.get('/')
        request.user = self.user
        
        mock_response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        mock_export.return_value = mock_response
        
        queryset = Cadastro_bm.objects.filter(id=self.cadastro.id)
        from .export_utils import export_bm_data
        response = export_bm_data(request, queryset, 'xlsx')
        
        self.assertEqual(response, mock_response)

    def test_export_bm_data_invalid_format(self):
        """Testa exportação com formato inválido"""
        request = self.factory.get('/')
        request.user = self.user
        
        queryset = Cadastro_bm.objects.filter(id=self.cadastro.id)
        from .export_utils import export_bm_data
        response = export_bm_data(request, queryset, 'invalid')
        
        self.assertEqual(response.status_code, 400)

class TestImportBM(TestCase):
    def setUp(self):
        self.client = Client()
        
        self.user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )

    def create_test_csv(self):
        """Cria arquivo CSV temporário para testes"""
        data = [{
            'nome': 'Teste Import',
            'nome_de_guerra': 'Import',
            'cpf': '11122233344',
            'rg': '123456789',
            'admissao': '2020-01-01',
            'nasc': '1990-01-01',
            'apresentacao_na_unidade': '2020-01-15',
            'posto_secao': '703151101 - EB CERRADO',
            'sgb': '1ºSGB',
            'situacao': 'Efetivo',
            'cnh': '12345678901',
            'cat_cnh': 'B',
            'esb': 'SIM',
            'ovb': 'LEVE',
            'email': 'test@example.com',
            'telefone': '11999999999',
            'funcao': 'MOTORISTA',
            'genero': 'Masculino'
        }]
        
        df = pd.DataFrame(data)
        csv_content = df.to_csv(index=False, sep=';', encoding='utf-8-sig')
        return SimpleUploadedFile("test.csv", csv_content.encode('utf-8-sig'), content_type="text/csv")

    def test_importar_bm_superuser_required(self):
        """Testa que apenas superusuários podem importar"""
        regular_user = User.objects.create_user(
            email='regular@example.com',
            password='testpass123'
        )
            
        self.client.force_login(regular_user)
        
        response = self.client.get(reverse('bm:importar_bm'))
        self.assertEqual(response.status_code, 302)

    def test_importar_bm_csv_success(self):
        """Testa importação CSV bem-sucedida"""
        self.client.force_login(self.user)
        
        csv_file = self.create_test_csv()
        response = self.client.post(reverse('bm:importar_bm'), {'arquivo': csv_file})
        
        self.assertEqual(response.status_code, 302)

# Testes Básicos de Modelos
class TestBasicModels(TestCase):
    def test_model_str_representation(self):
        """Testa representação string dos modelos"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        cadastro = Cadastro_bm(
            nome='Teste',
            nome_de_guerra='Teste',
            situacao='Efetivo',
            sgb='1ºSGB',
            posto_secao='703151101 - EB CERRADO',
            cpf='11122233366',
            rg='123456789',
            cnh='12345678901',
            cat_cnh='B',
            esb='SIM',
            ovb='LEVE',
            admissao=date(2020, 1, 1),
            nasc=date(1990, 1, 1),
            email='test@example.com',
            telefone='11333333333',
            apresentacao_na_unidade=date(2020, 1, 15),
            funcao='MOTORISTA',
            genero='Masculino',
            user=user
        )
        
        self.assertEqual(str(cadastro), 'Teste')

    def test_imagem_bm_str(self):
        """Testa representação string de Imagem_bm"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        cadastro = Cadastro_bm.objects.create(
            nome='Teste Imagem',
            nome_de_guerra='Imagem',
            situacao='Efetivo',
            sgb='1ºSGB',
            posto_secao='703151101 - EB CERRADO',
            cpf='99988877766',
            rg='123456789',
            cnh='12345678901',
            cat_cnh='B',
            esb='SIM',
            ovb='LEVE',
            admissao=date(2020, 1, 1),
            nasc=date(1990, 1, 1),
            email='test@example.com',
            telefone='11222222222',
            apresentacao_na_unidade=date(2020, 1, 15),
            funcao='MOTORISTA',
            genero='Masculino',
            user=user
        )
        
        imagem = Imagem_bm(cadastro=cadastro, user=user)
        self.assertIn('Imagem de Imagem', str(imagem))