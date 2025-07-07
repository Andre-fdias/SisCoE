# backend/bm/tests.py

from django.test import TestCase, Client
from django.urls import reverse, resolve
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date
from io import BytesIO
import csv
from dateutil.relativedelta import relativedelta

from .models import Cadastro_bm, Imagem_bm
from . import views
# Não é necessário importar as funções de export_utils diretamente nos testes se as views já as chamam
# from .export_utils import export_bm_data, export_to_pdf_military, export_to_excel_military, export_to_csv_military


User = get_user_model()

class BmTestSetup(TestCase):
    """
    Classe base para configurar dados comuns de teste.
    """
    def setUp(self):
        self.client = Client()
        # Cria um usuário comum para testes que não requerem permissões de superusuário
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')
        # Cria um superusuário para testes que requerem acesso de admin
        self.admin_user = User.objects.create_superuser(username='admin', email='admin@example.com', password='adminpassword')

        # Loga com o usuário comum por padrão para a maioria dos testes de view
        self.client.login(username='testuser', password='password123')

        # Criar uma instância de Cadastro_bm para testes recorrentes
        self.cadastro_bm = Cadastro_bm.objects.create(
            nome="João Silva",
            nome_de_guerra="Silva",
            situacao="Efetivo",
            sgb="1ºSGB",
            posto_secao="703151101 - EB CERRADO",
            cpf="12345678901",
            rg="123456789",
            cnh="12345678901",
            cat_cnh="AB",
            esb="MASC",
            ovb="B+",
            admissao=date(2010, 1, 1),
            nasc=date(1980, 5, 15),
            email="joao.silva@example.com",
            telefone="11987654321",
            apresentacao_na_unidade=date(2010, 1, 10),
            saida_da_unidade=None,
            funcao="MOTORISTA",
            genero="Masculino",
            user=self.user,
        )

class CadastroBmModelTest(BmTestSetup):
    """
    Testes para o modelo Cadastro_bm.
    """
    def test_cadastro_bm_creation(self):
        """Verifica se um Cadastro_bm pode ser criado."""
        self.assertIsNotNone(self.cadastro_bm.pk)
        self.assertEqual(self.cadastro_bm.nome, "João Silva")
        self.assertEqual(self.cadastro_bm.cpf, "12345678901")
        self.assertEqual(self.cadastro_bm.user, self.user)

    def test_imagem_bm_creation(self):
        """Verifica a criação de Imagem_bm e sua associação."""
        # Cria um arquivo de imagem em memória para simular o upload
        image_file = SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg")
        imagem_bm = Imagem_bm.objects.create(
            cadastro=self.cadastro_bm,
            image=image_file,
            user=self.user
        )
        self.assertIsNotNone(imagem_bm.pk)
        self.assertEqual(imagem_bm.cadastro, self.cadastro_bm)
        self.assertTrue(Imagem_bm.objects.filter(cadastro=self.cadastro_bm).exists())

    def test_idade_detalhada(self):
        """Testa o método idade_detalhada."""
        today = date.today()
        delta = relativedelta(today, self.cadastro_bm.nasc)
        expected_age_string = f"{delta.years} anos, {delta.months} meses e {delta.days} dias"
        self.assertEqual(self.cadastro_bm.idade_detalhada(), expected_age_string)

    def test_tempo_de_servico_detalhado(self):
        """Testa o método tempo_de_servico_detalhado."""
        today = date.today()
        delta = relativedelta(today, self.cadastro_bm.admissao)
        expected_service_string = f"{delta.years} anos, {delta.months} meses e {delta.days} dias"
        self.assertEqual(self.cadastro_bm.tempo_de_servico_detalhado(), expected_service_string)

    def test_apresentacao_detalhada(self):
        """Testa o método apresentacao_detalhada."""
        today = date.today()
        delta = relativedelta(today, self.cadastro_bm.apresentacao_na_unidade)
        expected_presentation_string = f"{delta.years} anos, {delta.months} meses e {delta.days} dias"
        self.assertEqual(self.cadastro_bm.apresentacao_detalhada(), expected_presentation_string)

    def test_status_property(self):
        """Testa a propriedade status para diferentes situações."""
        self.assertIn("Efetivo", self.cadastro_bm.status) #

        self.cadastro_bm.situacao = "Exonerado a Pedido"
        self.cadastro_bm.save() # Salva a mudança para que o status seja atualizado
        self.assertIn("Exonerado a Pedido", self.cadastro_bm.status) #

        self.cadastro_bm.situacao = "Transferido"
        self.cadastro_bm.save() # Salva a mudança
        self.assertIn("Transferido", self.cadastro_bm.status) #

class BmViewsTest(BmTestSetup):
    """
    Testes para as views da aplicação bm.
    """
    def test_listar_bm_view_authenticated(self):
        """Testa a view listar_bm para usuário autenticado."""
        response = self.client.get(reverse('bm:listar_bm'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'listar_bm.html')
        self.assertContains(response, self.cadastro_bm.nome)

    def test_listar_bm_view_unauthenticated(self):
        """Testa a view listar_bm para usuário não autenticado (deve redirecionar para login)."""
        self.client.logout() # Garante que o usuário não está logado
        response = self.client.get(reverse('bm:listar_bm'))
        self.assertRedirects(response, f"/accounts/login/?next={reverse('bm:listar_bm')}")

    def test_ver_bm_view_authenticated(self):
        """Testa a view ver_bm para usuário autenticado."""
        response = self.client.get(reverse('bm:ver_bm', args=[self.cadastro_bm.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ver_bm.html')
        self.assertContains(response, self.cadastro_bm.nome)
        self.assertContains(response, self.cadastro_bm.cpf)

    def test_ver_bm_view_unauthenticated(self):
        """Testa a view ver_bm para usuário não autenticado."""
        self.client.logout()
        response = self.client.get(reverse('bm:ver_bm', args=[self.cadastro_bm.pk]))
        self.assertRedirects(response, f"/accounts/login/?next={reverse('bm:ver_bm', args=[self.cadastro_bm.pk])}")

    def test_cadastrar_bm_get_authenticated(self):
        """Testa o GET da view cadastrar_bm para usuário autenticado."""
        response = self.client.get(reverse('bm:cadastrar_bm'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cadastro_bm.html')

    def test_cadastrar_bm_get_unauthenticated(self):
        """Testa o GET da view cadastrar_bm para usuário não autenticado."""
        self.client.logout()
        response = self.client.get(reverse('bm:cadastrar_bm'))
        self.assertRedirects(response, f"/accounts/login/?next={reverse('bm:cadastrar_bm')}")

    def test_cadastrar_bm_post_valid(self):
        """Testa o POST da view cadastrar_bm com dados válidos."""
        # É importante estar logado como um usuário que pode cadastrar (admin ou com permissão)
        self.client.login(username='admin', password='adminpassword')
        initial_count = Cadastro_bm.objects.count()
        response = self.client.post(reverse('bm:cadastrar_bm'), {
            'nome': 'Maria Souza',
            'nome_de_guerra': 'Souza',
            'situacao': 'Efetivo',
            'sgb': '2ºSGB',
            'posto_secao': '703151201 - EB SANTA ROSÁLIA',
            'cpf': '98765432109',
            'rg': '987654321',
            'cnh': '98765432109',
            'cat_cnh': 'B',
            'esb': 'FEM',
            'ovb': 'A-',
            'admissao': '2020-03-01',
            'nasc': '1990-01-01',
            'email': 'maria.souza@example.com',
            'telefone': '11998877665',
            'apresentacao_na_unidade': '2020-03-05',
            'saida_da_unidade': '',
            'funcao': 'AUXILIARES',
            'genero': 'Feminino',
        })
        self.assertEqual(Cadastro_bm.objects.count(), initial_count + 1)
        self.assertRedirects(response, reverse('bm:ver_bm', args=[Cadastro_bm.objects.last().pk]))

    def test_cadastrar_bm_post_invalid(self):
        """Testa o POST da view cadastrar_bm com dados inválidos (ex: CPF duplicado)."""
        self.client.login(username='admin', password='adminpassword')
        initial_count = Cadastro_bm.objects.count()
        response = self.client.post(reverse('bm:cadastrar_bm'), {
            'nome': 'João Silva Duplicate',
            'nome_de_guerra': 'Silva',
            'situacao': 'Efetivo',
            'sgb': '1ºSGB',
            'posto_secao': '703151101 - EB CERRADO',
            'cpf': '12345678901',  # CPF duplicado, que já existe self.cadastro_bm
            'rg': '123456789',
            'cnh': '12345678901',
            'cat_cnh': 'AB',
            'esb': 'MASC',
            'ovb': 'B+',
            'admissao': '2010-01-01',
            'nasc': '1980-05-15',
            'email': 'duplicate@example.com',
            'telefone': '11987654321',
            'apresentacao_na_unidade': '2010-01-10',
            'saida_da_unidade': '',
            'funcao': 'MOTORISTA',
            'genero': 'Masculino',
        })
        # Espera-se que o número de objetos não aumente (ou seja, não foi criado um novo)
        self.assertEqual(Cadastro_bm.objects.count(), initial_count)
        # Verifica se houve um redirecionamento de volta para a página de cadastro (indicando erro ou falha)
        self.assertRedirects(response, reverse('bm:cadastrar_bm'))


    def test_editar_bm_get_authenticated(self):
        """Testa o GET da view editar_bm para usuário autenticado."""
        response = self.client.get(reverse('bm:editar_bm', args=[self.cadastro_bm.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'editar_bm.html')
        self.assertContains(response, self.cadastro_bm.nome)

    def test_editar_bm_get_unauthenticated(self):
        """Testa o GET da view editar_bm para usuário não autenticado."""
        self.client.logout()
        response = self.client.get(reverse('bm:editar_bm', args=[self.cadastro_bm.pk]))
        self.assertRedirects(response, f"/accounts/login/?next={reverse('bm:editar_bm', args=[self.cadastro_bm.pk])}")

    def test_editar_bm_post_valid(self):
        """Testa o POST da view editar_bm com dados válidos."""
        self.client.login(username='admin', password='adminpassword')
        new_name = "João Silva Atualizado"
        response = self.client.post(reverse('bm:editar_bm', args=[self.cadastro_bm.pk]), {
            'nome': new_name,
            'nome_de_guerra': self.cadastro_bm.nome_de_guerra,
            'situacao': self.cadastro_bm.situacao, #
            'sgb': self.cadastro_bm.sgb, #
            'posto_secao': self.cadastro_bm.posto_secao, #
            'cpf': self.cadastro_bm.cpf, #
            'rg': self.cadastro_bm.rg, #
            'cnh': self.cadastro_bm.cnh, #
            'cat_cnh': self.cadastro_bm.cat_cnh, #
            'esb': self.cadastro_bm.esb, #
            'ovb': self.cadastro_bm.ovb, #
            'admissao': self.cadastro_bm.admissao.strftime('%Y-%m-%d'), #
            'nasc': self.cadastro_bm.nasc.strftime('%Y-%m-%d'), #
            'email': self.cadastro_bm.email, #
            'telefone': self.cadastro_bm.telefone, #
            'apresentacao_na_unidade': self.cadastro_bm.apresentacao_na_unidade.strftime('%Y-%m-%d'), #
            'saida_da_unidade': '', #
            'funcao': self.cadastro_bm.funcao, #
            'genero': self.cadastro_bm.genero, #
            'status': self.cadastro_bm.situacao # Campo 'status' que a view espera receber
        })
        self.cadastro_bm.refresh_from_db() # Recarrega a instância do banco de dados para obter as mudanças
        self.assertEqual(self.cadastro_bm.nome, new_name)
        self.assertRedirects(response, reverse('bm:ver_bm', args=[self.cadastro_bm.pk]))

    def test_excluir_bm_view_authenticated(self):
        """Testa a view excluir_bm para usuário autenticado."""
        self.client.login(username='admin', password='adminpassword') # Login como admin para ter permissão de exclusão
        initial_count = Cadastro_bm.objects.count()
        response = self.client.post(reverse('bm:excluir_bm', args=[self.cadastro_bm.pk]))
        self.assertEqual(Cadastro_bm.objects.count(), initial_count - 1)
        self.assertRedirects(response, reverse('bm:listar_bm'))

    def test_excluir_bm_view_unauthenticated(self):
        """Testa a view excluir_bm para usuário não autenticado."""
        self.client.logout()
        response = self.client.post(reverse('bm:excluir_bm', args=[self.cadastro_bm.pk]))
        self.assertRedirects(response, f"/accounts/login/?next={reverse('bm:excluir_bm', args=[self.cadastro_bm.pk])}")


    def test_exportar_bm_csv(self):
        """Testa a exportação para CSV."""
        response = self.client.post(reverse('bm:exportar_bm'), {'export_format': 'csv'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename="relacao_efetivo.csv"', response['Content-Disposition'])

        content = response.content.decode('utf-8')
        reader = csv.reader(content.splitlines(), delimiter=';')
        rows = list(reader)

        # Verifica se o cabeçalho e dados estão presentes (exemplo simples)
        self.assertIn("15º GRUPAMENTO DE BOMBEIROS MILITARES - RELAÇÃO DE EFETIVO", rows[0][0]) #
        self.assertIn(self.cadastro_bm.nome, content) #

    def test_exportar_bm_pdf(self):
        """Testa a exportação para PDF."""
        response = self.client.post(reverse('bm:exportar_bm'), {'export_format': 'pdf'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment; filename="relacao_efetivo.pdf"', response['Content-Disposition'])

    def test_exportar_bm_xlsx(self):
        """Testa a exportação para XLSX."""
        response = self.client.post(reverse('bm:exportar_bm'), {'export_format': 'xlsx'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertIn('attachment; filename="relacao_efetivo.xlsx"', response['Content-Disposition'])

    def test_importar_bm_get_authenticated(self):
        """Testa o GET da view importar_bm para usuário autenticado."""
        response = self.client.get(reverse('bm:importar_bm'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'importar_bm.html')

    def test_importar_bm_get_unauthenticated(self):
        """Testa o GET da view importar_bm para usuário não autenticado."""
        self.client.logout()
        response = self.client.get(reverse('bm:importar_bm'))
        self.assertRedirects(response, f"/accounts/login/?next={reverse('bm:importar_bm')}")

    def test_importar_bm_post_valid_csv(self):
        """Testa o POST da view importar_bm com um CSV válido."""
        self.client.login(username='admin', password='adminpassword')
        initial_count = Cadastro_bm.objects.count()
        csv_data = (
            "nome,nome_de_guerra,situacao,sgb,posto_secao,cpf,rg,cnh,cat_cnh,esb,ovb,admissao,nasc,email,telefone,apresentacao_na_unidade,saida_da_unidade,funcao,genero\n"
            "Carlos Santos,Santos,Efetivo,3ºSGB,703151202 - EB ÉDEM,11122233344,112233445,11122233344,A,MASC,AB+,2015-06-01,1985-02-20,carlos.santos@example.com,11991122334,2015-06-05,,TELEGRAFISTA,Masculino\n"
        )
        # SimpleUploadedFile simula um arquivo enviado através de um formulário
        csv_file = SimpleUploadedFile("test_import.csv", csv_data.encode('utf-8'), content_type="text/csv")

        response = self.client.post(reverse('bm:importar_bm'), {'csv_file': csv_file})
        self.assertEqual(Cadastro_bm.objects.count(), initial_count + 1)
        self.assertRedirects(response, reverse('bm:listar_bm'))
        self.assertTrue(Cadastro_bm.objects.filter(cpf="11122233344").exists())

    def test_importar_bm_post_invalid_csv_duplicate_cpf(self):
        """Testa o POST da view importar_bm com um CSV contendo CPF duplicado."""
        self.client.login(username='admin', password='adminpassword')
        initial_count = Cadastro_bm.objects.count()
        # CSV com um CPF que já existe (o do self.cadastro_bm)
        csv_data = (
            "nome,nome_de_guerra,situacao,sgb,posto_secao,cpf,rg,cnh,cat_cnh,esb,ovb,admissao,nasc,email,telefone,apresentacao_na_unidade,saida_da_unidade,funcao,genero\n"
            "Duplicado,Teste,Efetivo,1ºSGB,703151101 - EB CERRADO,12345678901,999888777,12345678901,A,MASC,A+,2023-01-01,1990-01-01,duplicado@example.com,11912345678,2023-01-05,,AUXILIARES,Masculino\n"
        )
        csv_file = SimpleUploadedFile("test_import_duplicate.csv", csv_data.encode('utf-8'), content_type="text/csv")

        response = self.client.post(reverse('bm:importar_bm'), {'csv_file': csv_file})
        # O count não deve mudar, pois o registro duplicado deve ser ignorado
        self.assertEqual(Cadastro_bm.objects.count(), initial_count)
        self.assertRedirects(response, reverse('bm:listar_bm')) # Redireciona para listar_bm

class BmURLsTest(BmTestSetup):
    """
    Testes para as URLs da aplicação bm.
    """
    def test_listar_bm_url_resolves(self):
        """Verifica se a URL 'listar_bm' resolve para a view correta."""
        url = reverse('bm:listar_bm')
        self.assertEqual(resolve(url).func, views.listar_bm)

    def test_cadastrar_bm_url_resolves(self):
        """Verifica se a URL 'cadastrar_bm' resolve para a view correta."""
        url = reverse('bm:cadastrar_bm')
        self.assertEqual(resolve(url).func, views.cadastrar_bm)

    def test_ver_bm_url_resolves(self):
        """Verifica se a URL 'ver_bm' resolve para a view correta."""
        # Usa um ID fictício, pois o que importa é a resolução da URL, não a existência do objeto aqui
        url = reverse('bm:ver_bm', args=[1])
        self.assertEqual(resolve(url).func, views.ver_bm)

    def test_editar_bm_url_resolves(self):
        """Verifica se a URL 'editar_bm' resolve para a view correta."""
        url = reverse('bm:editar_bm', args=[1])
        self.assertEqual(resolve(url).func, views.editar_bm)

    def test_excluir_bm_url_resolves(self):
        """Verifica se a URL 'excluir_bm' resolve para a view correta."""
        url = reverse('bm:excluir_bm', args=[1])
        self.assertEqual(resolve(url).func, views.excluir_bm)

    def test_importar_bm_url_resolves(self):
        """Verifica se a URL 'importar_bm' resolve para a view correta."""
        url = reverse('bm:importar_bm')
        self.assertEqual(resolve(url).func, views.importar_bm)

    def test_exportar_bm_url_resolves(self):
        """Verifica se a URL 'exportar_bm' resolve para a view correta."""
        url = reverse('bm:exportar_bm')
        self.assertEqual(resolve(url).func, views.exportar_bm)

    def test_atualizar_foto_url_resolves(self):
        """Verifica se a URL 'atualizar_foto' resolve para a view correta."""
        url = reverse('bm:atualizar_foto', args=[1])
        self.assertEqual(resolve(url).func, views.atualizar_foto)

# Testes de Admin (requer login como superusuário)
class AdminTest(BmTestSetup):
    """
    Testes para a interface de administração do Django.
    """
    def test_cadastro_bm_admin_list_view(self):
        """Testa a visualização da lista de Cadastro_bm no admin."""
        self.client.login(username='admin', password='adminpassword')
        response = self.client.get(reverse('admin:bm_cadastro_bm_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.cadastro_bm.nome)

    def test_cadastro_bm_admin_add_view(self):
        """Testa a página de adicionar Cadastro_bm no admin."""
        self.client.login(username='admin', password='adminpassword')
        response = self.client.get(reverse('admin:bm_cadastro_bm_add'))
        self.assertEqual(response.status_code, 200)

    def test_cadastro_bm_admin_change_view(self):
        """Testa a página de alteração de Cadastro_bm no admin."""
        self.client.login(username='admin', password='adminpassword')
        response = self.client.get(reverse('admin:bm_cadastro_bm_change', args=[self.cadastro_bm.pk]))
        self.assertEqual(response.status_code, 200)

    def test_imagem_bm_admin_list_view(self):
        """Testa a visualização da lista de Imagem_bm no admin."""
        self.client.login(username='admin', password='adminpassword')
        response = self.client.get(reverse('admin:bm_imagem_bm_changelist'))
        self.assertEqual(response.status_code, 200)