# tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from backend.documentos.models import Documento, Arquivo
from backend.documentos.forms import DocumentoForm
from datetime import date

User = get_user_model()

class DocumentoModelTest(TestCase):
    """Testes básicos para o modelo Documento"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.documento = Documento.objects.create(
            data_publicacao=date(2024, 1, 1),
            data_documento=date(2024, 1, 1),
            numero_documento='DOC001',
            assunto='Teste de Documento',
            descricao='Descrição do documento de teste',
            assinada_por='Test User',
            usuario=self.user,
            tipo='PDF'
        )

    def test_documento_creation(self):
        """Testa a criação de um documento"""
        self.assertEqual(self.documento.assunto, 'Teste de Documento')
        self.assertEqual(self.documento.numero_documento, 'DOC001')
        self.assertEqual(self.documento.usuario, self.user)
        self.assertEqual(str(self.documento), 'Teste de Documento')

    def test_documento_tipo_badge(self):
        """Testa a propriedade tipo_badge"""
        self.assertIn('bg-red-500', self.documento.tipo_badge)
        
        self.documento.tipo = 'VIDEO'
        self.assertIn('bg-blue-500', self.documento.tipo_badge)

    def test_documento_anexos_info(self):
        """Testa a propriedade anexos_info"""
        self.assertEqual(self.documento.anexos_info, '0 anexos ()')
        
        arquivo = Arquivo.objects.create(
            documento=self.documento,
            arquivo=SimpleUploadedFile('test.pdf', b'file_content'),
            tipo='PDF'
        )
        
        self.assertEqual(self.documento.anexos_info, '1 anexos (PDF)')


class ArquivoModelTest(TestCase):
    """Testes básicos para o modelo Arquivo"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.documento = Documento.objects.create(
            data_publicacao=date(2024, 1, 1),
            data_documento=date(2024, 1, 1),
            numero_documento='DOC001',
            assunto='Teste de Documento',
            descricao='Descrição do documento de teste',
            assinada_por='Test User',
            usuario=self.user,
            tipo='PDF'
        )
        
        self.arquivo = Arquivo.objects.create(
            documento=self.documento,
            arquivo=SimpleUploadedFile('test.pdf', b'file_content'),
            tipo='PDF'
        )

    def test_arquivo_creation(self):
        """Testa a criação de um arquivo"""
        self.assertEqual(self.arquivo.documento, self.documento)
        self.assertEqual(self.arquivo.tipo, 'PDF')
        self.assertTrue(self.arquivo.arquivo.name)

    def test_arquivo_extension(self):
        """Testa a propriedade extension"""
        self.assertEqual(self.arquivo.extension, 'pdf')

    def test_arquivo_mime_type(self):
        """Testa o método mime_type"""
        self.assertEqual(self.arquivo.mime_type(), 'PDF/pdf')


class DocumentoFormTest(TestCase):
    """Testes para o formulário de Documento"""
    
    def test_documento_form_valid_data(self):
        """Testa o formulário com dados válidos"""
        form_data = {
            'data_publicacao': '2024-01-01',
            'data_documento': '2024-01-01',
            'numero_documento': 'DOC001',
            'assunto': 'Teste de Formulário',
            'descricao': 'Descrição de teste',
            'assinada_por': 'Test User',
            'tipo': 'PDF'
        }
        form = DocumentoForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_documento_form_invalid_data(self):
        """Testa o formulário com dados inválidos"""
        form_data = {
            'data_publicacao': 'data-invalida',
            'numero_documento': '',
            'assunto': '',
        }
        form = DocumentoForm(data=form_data)
        self.assertFalse(form.is_valid())


class DocumentoQueryTest(TestCase):
    """Testes de consultas e filtros"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        # Cria vários documentos para testar filtros
        self.doc1 = Documento.objects.create(
            data_publicacao=date(2024, 1, 1),
            data_documento=date(2024, 1, 1),
            numero_documento='DOC001',
            assunto='Documento de Teste 1',
            descricao='Descrição 1',
            assinada_por='User 1',
            usuario=self.user,
            tipo='PDF'
        )
        
        self.doc2 = Documento.objects.create(
            data_publicacao=date(2024, 2, 1),
            data_documento=date(2024, 2, 1),
            numero_documento='DOC002',
            assunto='Documento de Teste 2',
            descricao='Descrição 2',
            assinada_por='User 2',
            usuario=self.user,
            tipo='VIDEO'
        )

    def test_filter_by_tipo(self):
        """Testa filtro por tipo de documento"""
        pdf_docs = Documento.objects.filter(tipo='PDF')
        self.assertEqual(pdf_docs.count(), 1)
        self.assertEqual(pdf_docs.first().numero_documento, 'DOC001')

    def test_filter_by_assunto(self):
        """Testa filtro por assunto"""
        docs = Documento.objects.filter(assunto__icontains='Teste')
        self.assertEqual(docs.count(), 2)

    def test_order_by_data(self):
        """Testa ordenação por data"""
        docs = Documento.objects.order_by('-data_documento')
        self.assertEqual(docs.first().numero_documento, 'DOC002')


class ArquivoRelationshipTest(TestCase):
    """Testes de relacionamento entre Documento e Arquivo"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.documento = Documento.objects.create(
            data_publicacao=date(2024, 1, 1),
            data_documento=date(2024, 1, 1),
            numero_documento='DOC001',
            assunto='Teste de Documento',
            descricao='Descrição do documento de teste',
            assinada_por='Test User',
            usuario=self.user,
            tipo='PDF'
        )

    def test_arquivo_relationship(self):
        """Testa o relacionamento Documento-Arquivo"""
        arquivo1 = Arquivo.objects.create(
            documento=self.documento,
            arquivo=SimpleUploadedFile('test1.pdf', b'file_content'),
            tipo='PDF'
        )
        
        arquivo2 = Arquivo.objects.create(
            documento=self.documento,
            arquivo=SimpleUploadedFile('test2.jpg', b'file_content'),
            tipo='IMAGEM'
        )
        
        # Verifica se os arquivos estão relacionados ao documento
        self.assertEqual(self.documento.arquivos.count(), 2)
        self.assertIn(arquivo1, self.documento.arquivos.all())
        self.assertIn(arquivo2, self.documento.arquivos.all())

    def test_arquivo_deletion_on_documento_delete(self):
        """Testa se arquivos são deletados quando o documento é deletado"""
        Arquivo.objects.create(
            documento=self.documento,
            arquivo=SimpleUploadedFile('test.pdf', b'file_content'),
            tipo='PDF'
        )
        
        arquivo_count_before = Arquivo.objects.count()
        self.documento.delete()
        arquivo_count_after = Arquivo.objects.count()
        
        self.assertEqual(arquivo_count_after, arquivo_count_before - 1)


class SimpleIntegrationTest(TestCase):
    """Testes de integração simples que funcionam"""
    
    def test_documento_workflow(self):
        """Testa um fluxo simples de criação e exclusão"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        # Cria documento
        doc = Documento.objects.create(
            data_publicacao=date(2024, 1, 1),
            data_documento=date(2024, 1, 1),
            numero_documento='DOC_TEST',
            assunto='Documento Test',
            descricao='Descrição',
            assinada_por='Test User',
            usuario=user,
            tipo='PDF'
        )
        
        # Adiciona arquivo
        arquivo = Arquivo.objects.create(
            documento=doc,
            arquivo=SimpleUploadedFile('test.pdf', b'file_content'),
            tipo='PDF'
        )
        
        # Verifica se tudo foi criado
        self.assertEqual(Documento.objects.count(), 1)
        self.assertEqual(Arquivo.objects.count(), 1)
        
        # Exclui documento
        doc.delete()
        
        # Verifica se arquivo também foi excluído (se CASCADE está funcionando)
        self.assertEqual(Documento.objects.count(), 0)
        self.assertEqual(Arquivo.objects.count(), 0)


class DocumentoCountTest(TestCase):
    """Testes de contagem e estatísticas"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        # Cria alguns documentos
        for i in range(3):
            Documento.objects.create(
                data_publicacao=date(2024, 1, i+1),
                data_documento=date(2024, 1, i+1),
                numero_documento=f'DOC{i+1:03d}',
                assunto=f'Documento {i+1}',
                descricao=f'Descrição {i+1}',
                assinada_por='Test User',
                usuario=self.user,
                tipo='PDF'
            )

    def test_documento_count(self):
        """Testa a contagem de documentos"""
        self.assertEqual(Documento.objects.count(), 3)

    def test_documento_with_arquivos_count(self):
        """Testa documentos com arquivos"""
        doc = Documento.objects.first()
        Arquivo.objects.create(
            documento=doc,
            arquivo=SimpleUploadedFile('test.pdf', b'file_content'),
            tipo='PDF'
        )
        
        docs_com_arquivos = Documento.objects.filter(arquivos__isnull=False).distinct()
        self.assertEqual(docs_com_arquivos.count(), 1)


class DocumentoFieldTest(TestCase):
    """Testes específicos para campos do modelo Documento"""
    
    def test_documento_field_types(self):
        """Testa os tipos de campos do Documento"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        doc = Documento.objects.create(
            data_publicacao=date(2024, 1, 1),
            data_documento=date(2024, 1, 1),
            numero_documento='DOC001',
            assunto='Teste',
            descricao='Descrição',
            assinada_por='Test User',
            usuario=user,
            tipo='PDF'
        )
        
        # Testa tipos de campos
        self.assertIsInstance(doc.data_publicacao, date)
        self.assertIsInstance(doc.data_documento, date)
        self.assertIsInstance(doc.numero_documento, str)
        self.assertIsInstance(doc.assunto, str)
        self.assertIsInstance(doc.descricao, str)
        self.assertIsInstance(doc.assinada_por, str)
        self.assertIsInstance(doc.tipo, str)


class ArquivoFieldTest(TestCase):
    """Testes específicos para campos do modelo Arquivo"""
    
    def test_arquivo_field_types(self):
        """Testa os tipos de campos do Arquivo"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        doc = Documento.objects.create(
            data_publicacao=date(2024, 1, 1),
            data_documento=date(2024, 1, 1),
            numero_documento='DOC001',
            assunto='Teste',
            descricao='Descrição',
            assinada_por='Test User',
            usuario=user,
            tipo='PDF'
        )
        
        arquivo = Arquivo.objects.create(
            documento=doc,
            arquivo=SimpleUploadedFile('test.pdf', b'file_content'),
            tipo='PDF'
        )
        
        # Testa tipos de campos
        self.assertEqual(arquivo.documento, doc)
        self.assertIsInstance(arquivo.tipo, str)
        self.assertTrue(hasattr(arquivo, 'arquivo'))


class DocumentoTipoChoicesTest(TestCase):
    """Testes para as choices do modelo Documento"""
    
    def test_tipo_choices(self):
        """Testa as opções disponíveis para tipo"""
        choices = Documento.TIPO_CHOICES
        expected_choices = [
            ('PDF', 'PDF'),
            ('VIDEO', 'Vídeo'),
            ('AUDIO', 'Áudio'),
            ('DOC', 'Documento'),
            ('SHEET', 'Planilha'),
            ('IMAGEM', 'Imagem'),
            ('TEXT', 'Texto'),
            ('OUTRO', 'Outro'),
        ]
        
        self.assertEqual(len(choices), len(expected_choices))
        
        # Verifica se todas as choices esperadas estão presentes
        for expected_choice in expected_choices:
            self.assertIn(expected_choice, choices)


class ArquivoTipoChoicesTest(TestCase):
    """Testes para as choices do modelo Arquivo"""
    
    def test_tipo_choices(self):
        """Testa as opções disponíveis para tipo"""
        choices = Arquivo.TIPO_CHOICES
        expected_choices = [
            ('PDF', 'PDF'),
            ('VIDEO', 'Vídeo'),
            ('AUDIO', 'Áudio'),
            ('DOC', 'Documento'),
            ('SHEET', 'Planilha'),
            ('IMAGEM', 'Imagem'),
            ('TEXT', 'Texto'),
            ('OUTRO', 'Outro'),
        ]
        
        self.assertEqual(len(choices), len(expected_choices))
        
        # Verifica se todas as choices esperadas estão presentes
        for expected_choice in expected_choices:
            self.assertIn(expected_choice, choices)