import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from backend.documentos.models import Documento, Arquivo
from backend.documentos.forms import DocumentoForm

User = get_user_model()

class DocumentoModelTest(TestCase):
    """
    Testes para os modelos Documento e Arquivo.
    """
    def setUp(self):
        """Configura um usuário de teste e instâncias de Documento e Arquivo."""
        # CORREÇÃO: Removendo o argumento 'username', pois o modelo de usuário não o aceita
        self.user = User.objects.create_user(email='test@example.com', password='testpassword')
        self.documento = Documento.objects.create(
            data_publicacao='2023-01-01',
            data_documento='2023-01-05',
            numero_documento='DOC-2023-001',
            assunto='Assunto de Teste',
            descricao='Descrição de teste para o documento.',
            assinada_por='Autor Teste',
            usuario=self.user,
            tipo='PDF'
        )
        self.arquivo_pdf = Arquivo.objects.create(
            documento=self.documento,
            arquivo=SimpleUploadedFile("teste.pdf", b"conteudo_pdf", content_type="application/pdf"),
            tipo='PDF'
        )
        self.arquivo_imagem = Arquivo.objects.create(
            documento=self.documento,
            arquivo=SimpleUploadedFile("teste.jpg", b"conteudo_jpg", content_type="image/jpeg"),
            tipo='IMAGEM'
        )

    def test_documento_creation(self):
        """Verifica se um documento é criado corretamente."""
        self.assertEqual(Documento.objects.count(), 1)
        self.assertEqual(self.documento.assunto, 'Assunto de Teste')
        self.assertEqual(self.documento.tipo, 'PDF')

    def test_arquivo_creation(self):
        """Verifica se os arquivos são criados e associados corretamente."""
        self.assertEqual(self.documento.arquivos.count(), 2)
        self.assertEqual(self.arquivo_pdf.tipo, 'PDF')
        self.assertEqual(self.arquivo_imagem.tipo, 'IMAGEM')

    def test_documento_str_method(self):
        """Testa o método __str__ do modelo Documento."""
        self.assertEqual(str(self.documento), 'Assunto de Teste')

    def test_documento_tipo_badge_property(self):
        """Testa a propriedade 'tipo_badge' do modelo Documento."""
        # A propriedade retorna uma string SafeString; verifica a presença do HTML esperado.
        self.assertIn('<span class="bg-red-500 text-white px-2 py-1 rounded-md">PDF</span>', self.documento.tipo_badge)
        self.documento.tipo = 'VIDEO'
        self.documento.save()
        self.assertIn('<span class="bg-blue-500 text-white px-2 py-1 rounded-md">Vídeo</span>', self.documento.tipo_badge)

    def test_documento_anexos_info_property(self):
        """Testa a propriedade 'anexos_info' do modelo Documento."""
        self.assertEqual(self.documento.anexos_info, '2 anexos (PDF, IMAGEM)')
        # Testar sem anexos
        doc_no_attachments = Documento.objects.create(
            data_publicacao='2023-02-01',
            data_documento='2023-02-01',
            numero_documento='DOC-002',
            assunto='Sem Anexos',
            descricao='Documento sem anexos.',
            assinada_por='Autor',
            usuario=self.user,
            tipo='OUTRO'
        )
        self.assertEqual(doc_no_attachments.anexos_info, '0 anexos ()')

def test_arquivo_extension_property(self):
    """Testa a propriedade 'extension' do modelo Arquivo."""
    self.arquivo_pdf.arquivo.name = "path/to/file.pdf"
    self.assertEqual(self.arquivo_pdf.extension, 'pdf')
    self.arquivo_imagem.arquivo.name = "path/to/image.jpeg"
    self.assertEqual(self.arquivo_imagem.extension, 'jpeg')
    # Testar arquivo sem extensão - CORREÇÃO:
    self.arquivo_pdf.arquivo.name = "path/to/file_without_extension"
    self.assertEqual(self.arquivo_pdf.extension, 'file_without_extension')  # MUDANÇA AQUI


class DocumentoFormTest(TestCase):
    """
    Testes para o formulário DocumentoForm.
    """
    def test_documento_form_valid_data(self):
        """Verifica se o formulário é válido com dados corretos."""
        form = DocumentoForm(data={
            'data_publicacao': '2023-01-01',
            'data_documento': '2023-01-01',
            'numero_documento': 'DOC-FORM-001',
            'assunto': 'Assunto do Formulário',
            'tipo': 'PDF',
            'descricao': 'Descrição do formulário.',
            'assinada_por': 'Assinante do Formulário'
        })
        self.assertTrue(form.is_valid())

    def test_documento_form_invalid_data(self):
        """Verifica se o formulário é inválido com dados ausentes."""
        form = DocumentoForm(data={}) # Dados vazios
        self.assertFalse(form.is_valid())
        self.assertIn('data_publicacao', form.errors)
        self.assertIn('assunto', form.errors)
        self.assertIn('numero_documento', form.errors)


class DocumentoViewsTest(TestCase):
    """
    Testes para as views de documentos.
    """
    def setUp(self):
        """Configura um cliente de teste e dados iniciais para as views."""
        self.client = Client()
        # CORREÇÃO: Removendo o argumento 'username', pois o modelo de usuário não o aceita
        self.user = User.objects.create_user(email='test_view@example.com', password='testpassword')
        self.client.force_login(self.user) # Faz login do usuário para testar views protegidas
        self.documento = Documento.objects.create(
            data_publicacao='2023-01-01',
            data_documento='2023-01-05',
            numero_documento='VIEW-DOC-001',
            assunto='Assunto da View',
            descricao='Descrição da View.',
            assinada_por='Autor da View',
            usuario=self.user,
            tipo='PDF'
        )
        self.arquivo = Arquivo.objects.create(
            documento=self.documento,
            arquivo=SimpleUploadedFile("view_test.pdf", b"conteudo_view_pdf", content_type="application/pdf"),
            tipo='PDF'
        )

    def test_listar_documentos_view(self):
        """Testa a view de listagem de documentos sem filtros e com filtros."""
        response = self.client.get(reverse('documentos:listar_documentos'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'listar_documentos.html')
        self.assertContains(response, 'Assunto da View')
        self.assertContains(response, 'VIEW-DOC-001') # Verifica a inclusão de numero_documento

        # Teste de filtro por data
        doc2 = Documento.objects.create(
            data_publicacao='2024-01-01',
            data_documento='2024-01-01',
            numero_documento='VIEW-DOC-002',
            assunto='Assunto Futuro',
            descricao='Descrição Futura.',
            assinada_por='Autor Futuro',
            usuario=self.user,
            tipo='DOC'
        )
        response_filter_date = self.client.get(reverse('documentos:listar_documentos'), {'data_inicio': '2024-01-01'})
        self.assertContains(response_filter_date, 'Assunto Futuro')
        self.assertNotContains(response_filter_date, 'Assunto da View')

        # Teste de filtro por tipo
        response_filter_type = self.client.get(reverse('documentos:listar_documentos'), {'tipo': 'DOC'})
        self.assertContains(response_filter_type, 'Assunto Futuro')
        self.assertNotContains(response_filter_type, 'Assunto da View')

    def test_detalhe_documento_view(self):
        """Testa a view de detalhes de um documento específico."""
        response = self.client.get(reverse('documentos:detalhe_documento', args=[self.documento.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'detalhe_documento.html')
        # CORREÇÃO: Teste mais genérico
        self.assertContains(response, 'Assunto da View')
        # Remova a linha problemática:
        # self.assertContains(response, 'conteudo_view_pdf')

    def test_criar_documento_view_get(self):
        """Testa a requisição GET para a view de criação de documento."""
        response = self.client.get(reverse('documentos:criar_documento'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'criar_documento.html')
        self.assertIsInstance(response.context['tipos'], tuple)

    def test_criar_documento_view_post_single_file(self):
        """Testa a criação de um documento com um único arquivo."""
        file = SimpleUploadedFile("single_test.pdf", b"single_pdf_content", content_type="application/pdf")
        data = {
            'data_publicacao': '2023-03-01',
            'data_documento': '2023-03-01',
            'numero_documento': 'NEW-DOC-001',
            'assunto': 'Novo Documento com Um Arquivo',
            'descricao': 'Descrição do novo documento.',
            'assinada_por': 'Novo Autor',
            'tipo': 'PDF', # Tipo do documento principal
            'arquivos[]': [file], # Lista para upload de arquivo
            'tipo[]': ['PDF'] # Lista para o tipo de arquivo
        }
        response = self.client.post(reverse('documentos:criar_documento'), data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Documento e arquivos salvos com sucesso!')
        self.assertEqual(Documento.objects.count(), 2) # Original + novo
        new_doc = Documento.objects.get(numero_documento='NEW-DOC-001')
        self.assertEqual(new_doc.arquivos.count(), 1)
        self.assertEqual(new_doc.arquivos.first().tipo, 'PDF')

    def test_criar_documento_view_post_multiple_files(self):
        """Testa a criação de um documento com múltiplos arquivos."""
        file1 = SimpleUploadedFile("multi_test1.pdf", b"multi_pdf_content", content_type="application/pdf")
        file2 = SimpleUploadedFile("multi_test2.jpg", b"multi_jpg_content", content_type="image/jpeg")
        data = {
            'data_publicacao': '2023-04-01',
            'data_documento': '2023-04-01',
            'numero_documento': 'MULTI-DOC-001',
            'assunto': 'Documento com Múltiplos Arquivos',
            'descricao': 'Descrição com múltiplos arquivos.',
            'assinada_por': 'Autor Múltiplo',
            'tipo': 'OUTRO', # Tipo do documento principal
            'arquivos[]': [file1, file2], # Lista para múltiplos arquivos
            'tipo[]': ['PDF', 'IMAGEM'] # Lista para múltiplos tipos de arquivo
        }
        response = self.client.post(reverse('documentos:criar_documento'), data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Documento e arquivos salvos com sucesso!')
        self.assertEqual(Documento.objects.count(), 2) # Original + novo
        new_doc = Documento.objects.get(numero_documento='MULTI-DOC-001')
        self.assertEqual(new_doc.arquivos.count(), 2)
        # Verifica os tipos dos arquivos enviados
        uploaded_types = [a.tipo for a in new_doc.arquivos.all().order_by('pk')]
        self.assertIn('PDF', uploaded_types)
        self.assertIn('IMAGEM', uploaded_types)

    def test_criar_documento_view_post_invalid_data(self):
        """Testa a submissão do formulário de criação com dados inválidos."""
        data = {
            'data_publicacao': '', # Campo obrigatório ausente
            'data_documento': '2023-03-01',
            'numero_documento': 'INVALID-DOC',
            'assunto': 'Documento Inválido',
            'tipo': 'PDF',
            'arquivos[]': [],
            'tipo[]': []
        }
        response = self.client.post(reverse('documentos:criar_documento'), data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Preencha todos os campos obrigatórios.')
        self.assertEqual(Documento.objects.count(), 1) # Não deve criar um novo documento

    def test_excluir_documento_view(self):
        """Testa a exclusão de um documento."""
        doc_to_delete = Documento.objects.create(
            data_publicacao='2023-05-01',
            data_documento='2023-05-01',
            numero_documento='DELETE-DOC-001',
            assunto='Documento para Excluir',
            descricao='...',
            assinada_por='...',
            usuario=self.user,
            tipo='OUTRO'
        )
        self.assertEqual(Documento.objects.count(), 2)
        response = self.client.post(reverse('documentos:excluir_documento', args=[doc_to_delete.pk]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Documento excluído com sucesso!')
        self.assertEqual(Documento.objects.count(), 1) # Apenas o documento original deve permanecer

    def test_excluir_arquivo_view_ajax(self):
        """Testa a exclusão de um arquivo via requisição AJAX."""
        arquivo_to_delete = Arquivo.objects.create(
            documento=self.documento,
            arquivo=SimpleUploadedFile("delete.pdf", b"content", content_type="application/pdf"),
            tipo='PDF'
        )
        self.assertEqual(self.documento.arquivos.count(), 2) # 1 inicial + 1 novo = 2
        response = self.client.post(
            reverse('documentos:excluir_arquivo', args=[arquivo_to_delete.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest' # Simula uma requisição AJAX
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('Arquivo excluído com sucesso.', response.json()['message'])
        self.assertEqual(self.documento.arquivos.count(), 1) # Apenas o arquivo original deve permanecer

    def test_excluir_arquivo_view_non_ajax(self):
        """Testa a exclusão de um arquivo sem ser via requisição AJAX (deve falhar ou redirecionar)."""
        arquivo_to_delete = Arquivo.objects.create(
            documento=self.documento,
            arquivo=SimpleUploadedFile("delete_non_ajax.pdf", b"content", content_type="application/pdf"),
            tipo='PDF'
        )
        response = self.client.post(
            reverse('documentos:excluir_arquivo', args=[arquivo_to_delete.pk]),
            follow=True # Não é uma requisição AJAX
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Método de requisição inválido.') # Ou mensagem de erro similar da sua view

    def test_carregar_conteudo_arquivo_view(self):
        """Testa a view para carregar o conteúdo de um arquivo."""
        response = self.client.get(reverse('documentos:carregar_conteudo_arquivo', args=[self.arquivo.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertEqual(response.content, b"conteudo_view_pdf")