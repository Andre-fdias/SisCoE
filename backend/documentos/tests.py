from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Documento, Arquivo
from datetime import date

User = get_user_model()

class DocumentoSecurityTest(TestCase):
    """
    Testa a segurança e o controle de acesso do app 'documentos'.
    Garante que as vulnerabilidades críticas de acesso indevido foram corrigidas.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Configura os dados iniciais para todos os testes da classe.
        Cria usuários com diferentes níveis de permissão e documentos associados.
        """
        # Usuário 1 (Básico)
        cls.user_basico = User.objects.create_user(
            email="basico@example.com",
            password="testpassword",
            first_name="Usuario",
            last_name="Basico",
            permissoes="basico"
        )

        # Usuário 2 (Outro Básico)
        cls.user_outro = User.objects.create_user(
            email="outro@example.com",
            password="testpassword",
            first_name="Outro",
            last_name="Usuario",
            permissoes="basico"
        )

        # Usuário 3 (Gestor)
        cls.user_gestor = User.objects.create_user(
            email="gestor@example.com",
            password="testpassword",
            first_name="Usuario",
            last_name="Gestor",
            permissoes="gestor"
        )

        # Usuário 4 (Admin)
        cls.user_admin = User.objects.create_user(
            email="admin@example.com",
            password="testpassword",
            first_name="Usuario",
            last_name="Admin",
            permissoes="admin"
        )

        # Documentos
        cls.doc_basico = Documento.objects.create(
            assunto="Documento do Básico",
            usuario=cls.user_basico,
            data_documento=date.today(),
            numero_documento="DOC001"
        )

        cls.doc_outro = Documento.objects.create(
            assunto="Documento do Outro",
            usuario=cls.user_outro,
            data_documento=date.today(),
            numero_documento="DOC002"
        )

        # URLs
        cls.listar_url = reverse("documentos:listar_documentos")
        cls.criar_url = reverse("documentos:criar_documento")
        cls.detalhe_basico_url = reverse("documentos:detalhe_documento", kwargs={'pk': cls.doc_basico.pk})
        cls.detalhe_outro_url = reverse("documentos:detalhe_documento", kwargs={'pk': cls.doc_outro.pk})
        cls.editar_basico_url = reverse("documentos:editar_documento", kwargs={'pk': cls.doc_basico.pk})
        cls.editar_outro_url = reverse("documentos:editar_documento", kwargs={'pk': cls.doc_outro.pk})
        cls.excluir_basico_url = reverse("documentos:excluir_documento", kwargs={'pk': cls.doc_basico.pk})
        cls.excluir_outro_url = reverse("documentos:excluir_documento", kwargs={'pk': cls.doc_outro.pk})

    def setUp(self):
        """
        Configura o cliente de teste antes de cada teste.
        """
        self.client = Client()

    def test_unauthenticated_access_redirects_to_login(self):
        """
        Testa se usuários não autenticados são redirecionados para a página de login.
        """
        urls = [
            self.listar_url, self.criar_url, self.detalhe_basico_url,
            self.editar_basico_url, self.excluir_basico_url
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertRedirects(response, f'/accounts/login/?next={url}')

    def test_basico_user_can_see_own_documents_list(self):
        """
        Testa se um usuário básico vê apenas seus documentos na listagem.
        """
        self.client.login(email="basico@example.com", password="testpassword")
        response = self.client.get(self.listar_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.doc_basico.assunto)
        self.assertNotContains(response, self.doc_outro.assunto)

    def test_basico_user_can_access_own_document_details(self):
        """
        Testa se um usuário básico pode acessar os detalhes de seu próprio documento.
        """
        self.client.login(email="basico@example.com", password="testpassword")
        response = self.client.get(self.detalhe_basico_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.doc_basico.assunto)

    def test_basico_user_cannot_access_other_user_document(self):
        """
        [TESTE DE SEGURANÇA CRÍTICO]
        Testa se um usuário básico NÃO PODE acessar, editar ou excluir documentos de outro usuário.
        """
        self.client.login(email="basico@example.com", password="testpassword")
        
        # Não pode ver detalhes
        response_detalhe = self.client.get(self.detalhe_outro_url)
        self.assertEqual(response_detalhe.status_code, 404)

        # Não pode acessar a página de edição
        response_editar = self.client.get(self.editar_outro_url)
        self.assertEqual(response_editar.status_code, 404)

        # Não pode excluir (POST)
        response_excluir = self.client.post(self.excluir_outro_url)
        self.assertEqual(response_excluir.status_code, 404)
        self.assertTrue(Documento.objects.filter(pk=self.doc_outro.pk).exists(), "Documento de outro usuário foi excluído indevidamente.")

    def test_gestor_can_see_all_documents(self):
        """
        Testa se um usuário 'gestor' pode ver todos os documentos na listagem.
        """
        self.client.login(email="gestor@example.com", password="testpassword")
        response = self.client.get(self.listar_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.doc_basico.assunto)
        self.assertContains(response, self.doc_outro.assunto)

    def test_gestor_can_access_other_user_document(self):
        """
        Testa se um usuário 'gestor' PODE acessar, editar e excluir documentos de outros usuários.
        """
        self.client.login(email="gestor@example.com", password="testpassword")

        # Pode ver detalhes
        response_detalhe = self.client.get(self.detalhe_outro_url)
        self.assertEqual(response_detalhe.status_code, 200)

        # Pode acessar a página de edição
        response_editar = self.client.get(self.editar_outro_url)
        self.assertEqual(response_editar.status_code, 200)

        # Pode excluir
        response_excluir = self.client.post(self.excluir_outro_url)
        self.assertEqual(response_excluir.status_code, 302) # Redireciona após exclusão
        self.assertFalse(Documento.objects.filter(pk=self.doc_outro.pk).exists(), "Documento não foi excluído pelo gestor.")

    def test_admin_can_access_other_user_document(self):
        """
        Testa se um usuário 'admin' PODE acessar, editar e excluir documentos de outros usuários.
        """
        self.client.login(email="admin@example.com", password="testpassword")

        # Pode ver detalhes
        response_detalhe = self.client.get(self.detalhe_outro_url)
        self.assertEqual(response_detalhe.status_code, 200)

        # Pode acessar a página de edição
        response_editar = self.client.get(self.editar_outro_url)
        self.assertEqual(response_editar.status_code, 200)
        
    def test_file_upload_in_create_documento(self):
        """
        Testa se o upload de arquivos funciona corretamente na criação do documento.
        """
        self.client.login(email="basico@example.com", password="testpassword")
        
        # Cria um arquivo simples em memória
        file_content = b"Este e um arquivo de teste."
        uploaded_file = SimpleUploadedFile("teste.txt", file_content, content_type="text/plain")
        
        form_data = {
            "data_documento": date.today(),
            "numero_documento": "DOC_UPLOAD_TEST",
            "assunto": "Teste de Upload",
            "descricao": "Testando upload.",
            "assinada_por": "Sistema de Teste",
            "tipo": "TEXT",
            "arquivos[]": [uploaded_file],
            "tipo[]": ["TEXT"]
        }
        
        response = self.client.post(self.criar_url, data=form_data)
        
        # Verifica se foi redirecionado com sucesso
        self.assertEqual(response.status_code, 302)
        
        # Verifica se o documento e o arquivo foram criados
        doc = Documento.objects.get(numero_documento="DOC_UPLOAD_TEST")
        self.assertEqual(doc.assunto, "Teste de Upload")
        self.assertEqual(doc.arquivos.count(), 1)
        
        arquivo_salvo = doc.arquivos.first()
        self.assertEqual(arquivo_salvo.arquivo.name.split('/')[-1], "teste.txt")
        self.assertEqual(arquivo_salvo.tipo, "TEXT")

        # Limpa o arquivo após o teste
        arquivo_salvo.arquivo.delete()
        doc.delete()