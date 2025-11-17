# backend/municipios/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from .models import Posto, Contato, Pessoal, Cidade

User = get_user_model()


class MunicipiosModelsTest(TestCase):
    """Testes para os modelos do app municipios"""

    def setUp(self):
        """Configuração inicial para os testes"""
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )

        # Criar um posto de exemplo
        self.posto = Posto.objects.create(
            sgb="1ºSGB",
            posto_secao="703151000 - CMT 1º SGB",
            posto_atendimento="EB SOROCABA",
            cidade_posto="Sorocaba",
            tipo_cidade="Administrativo",
            op_adm="Sede",
            usuario=self.user,
        )

        # Criar contato associado
        self.contato = Contato.objects.create(
            posto=self.posto,
            telefone="1532223333",
            rua="Rua Teste",
            numero="123",
            bairro="Centro",
            cidade="Sorocaba",
            cep="18000100",
            email="teste@example.com",
            longitude=-47.4589,
            latitude=-23.5012,
        )

        # Criar pessoal associado - CORRIGIDO: removido 'cel' e 'asp' do cálculo
        self.pessoal = Pessoal.objects.create(
            posto=self.posto,
            cel=1,  # Não conta no total
            ten_cel=2,  # Conta
            maj=3,  # Conta
            cap=4,  # Conta
            tenqo=5,  # Conta
            tenqa=6,  # Conta
            asp=7,  # Não conta no total
            st_sgt=8,  # Conta
            cb_sd=9,  # Conta
        )

        # Criar cidade associada
        self.cidade = Cidade.objects.create(
            posto=self.posto,
            municipio="Sorocaba",
            descricao="Cidade principal",
            longitude=-47.4589,
            latitude=-23.5012,
        )

    def test_posto_creation(self):
        """Testa a criação de um Posto"""
        self.assertEqual(self.posto.posto_atendimento, "EB SOROCABA")
        self.assertEqual(self.posto.sgb, "1ºSGB")
        self.assertEqual(self.posto.cidade_posto, "Sorocaba")
        self.assertEqual(str(self.posto), "EB SOROCABA - Sorocaba")
        self.assertTrue(isinstance(self.posto.data_criacao, timezone.datetime))

    def test_contato_creation(self):
        """Testa a criação de um Contato"""
        self.assertEqual(self.contato.telefone, "1532223333")
        self.assertEqual(self.contato.rua, "Rua Teste")
        self.assertEqual(str(self.contato), "Contato EB SOROCABA")
        self.assertEqual(self.contato.posto, self.posto)

    def test_pessoal_creation(self):
        """Testa a criação de Pessoal"""
        self.assertEqual(self.pessoal.cel, 1)
        self.assertEqual(self.pessoal.ten_cel, 2)
        self.assertEqual(self.pessoal.maj, 3)
        self.assertEqual(self.pessoal.cap, 4)
        # O total deve ser: ten_cel + maj + cap + tenqo + tenqa + st_sgt + cb_sd
        # 2 + 3 + 4 + 5 + 6 + 8 + 9 = 37
        self.assertEqual(self.pessoal.total, 37)
        self.assertEqual(str(self.pessoal), "EB SOROCABA - Sorocaba")

    def test_cidade_creation(self):
        """Testa a criação de uma Cidade"""
        self.assertEqual(self.cidade.municipio, "Sorocaba")
        self.assertEqual(self.cidade.descricao, "Cidade principal")
        self.assertEqual(str(self.cidade), "Sorocaba - EB SOROCABA")
        self.assertEqual(self.cidade.get_nome_municipio(), "Sorocaba")


class MunicipiosViewsTest(TestCase):
    """Testes para as views do app municipios"""

    def setUp(self):
        self.client = TestCase.client_class()
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )

        self.posto = Posto.objects.create(
            sgb="1ºSGB",
            posto_secao="703151000 - CMT 1º SGB",
            posto_atendimento="EB SOROCABA",
            cidade_posto="Sorocaba",
            tipo_cidade="Administrativo",
            op_adm="Sede",
            usuario=self.user,
        )

        # Criar Pessoal para evitar erro no template
        self.pessoal = Pessoal.objects.create(
            posto=self.posto,
            cel=0,
            ten_cel=0,
            maj=0,
            cap=0,
            tenqo=0,
            tenqa=0,
            asp=0,
            st_sgt=0,
            cb_sd=0,
        )

    def test_posto_list_view_authenticated(self):
        """Testa acesso à lista de postos com usuário autenticado"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("municipios:posto_list"))
        self.assertEqual(response.status_code, 200)

    def test_posto_detail_view(self):
        """Testa a view de detalhes do posto"""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("municipios:posto_detail", args=[self.posto.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_posto_list_view_unauthenticated(self):
        """Testa redirecionamento para login quando não autenticado"""
        response = self.client.get(reverse("municipios:posto_list"))
        self.assertEqual(response.status_code, 302)  # Redireciona para login


class MunicipiosURLsTest(TestCase):
    """Testes para as URLs do app municipios"""

    def test_urls_exist(self):
        """Testa se as URLs principais existem"""
        self.assertEqual(reverse("municipios:posto_list"), "/municipios/")
        self.assertEqual(reverse("municipios:posto_detail", args=[1]), "/municipios/1/")
        self.assertEqual(reverse("municipios:posto_create"), "/municipios/novo/")


class MunicipiosFormsTest(TestCase):
    """Testes para os formulários do app municipios"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )

        self.posto = Posto.objects.create(
            sgb="1ºSGB",
            posto_secao="703151000 - CMT 1º SGB",
            posto_atendimento="EB SOROCABA",
            cidade_posto="Sorocaba",
            tipo_cidade="Administrativo",
            op_adm="Sede",
            usuario=self.user,
        )

    def test_pessoal_form(self):
        """Testa o formulário de Pessoal"""
        from .forms import PessoalForm

        form_data = {
            "posto": self.posto.id,
            "cel": 1,
            "ten_cel": 2,
            "maj": 3,
            "cap": 4,
            "tenqo": 5,
            "tenqa": 6,
            "asp": 7,
            "st_sgt": 8,
            "cb_sd": 9,
        }

        form = PessoalForm(data=form_data)
        self.assertTrue(form.is_valid())


class BasicAppTest(TestCase):
    """Testes básicos do app"""

    def test_app_loaded(self):
        """Testa se o app está carregado corretamente"""
        from django.apps import apps

        try:
            app_config = apps.get_app_config("municipios")
            self.assertEqual(app_config.name, "backend.municipios")
        except Exception as e:
            self.fail(f"App não carregado: {e}")

    def test_models_imported(self):
        """Testa se os modelos podem ser importados"""
        try:
            from backend.municipios.models import Posto, Contato, Pessoal, Cidade

            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Erro ao importar modelos: {e}")

    def test_basic_math(self):
        """Teste matemático básico"""
        self.assertEqual(1 + 1, 2)


class ExportImportTest(TestCase):
    """Testes para funcionalidades de exportação/importação"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )

    def test_export_utils_import(self):
        """Testa se o módulo de exportação pode ser importado"""
        try:
            from backend.municipios.export_utils import export_efetivo_pdf_report

            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Erro ao importar export_utils: {e}")

    def test_import_utils_import(self):
        """Testa se o módulo de importação pode ser importado"""
        try:
            from backend.municipios.import_utils import importar_dados

            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Erro ao importar import_utils: {e}")


class ModelChoicesTest(TestCase):
    """Testes para as choices dos modelos"""

    def test_posto_choices(self):
        """Testa as choices do modelo Posto"""
        from backend.municipios.models import Posto

        self.assertIn(("1ºSGB", "1ºSGB"), Posto.sgb_choices)
        self.assertIn(("Administrativo", " Administrativo"), Posto.op_adm_choices)
        self.assertIn(("Sorocaba", "Sorocaba"), Posto.cidade_posto_choices)
        # Teste com um valor que realmente existe nas choices
        self.assertIn(
            ("EB VOTORANTIM", "EB VOTORANTIM"), Posto.posto_atendimento_choices
        )

    def test_cidade_choices(self):
        """Testa as choices do modelo Cidade"""
        from backend.municipios.models import Cidade

        # Verifica se algumas cidades estão nas choices
        self.assertIn(("Sorocaba", "Sorocaba"), Cidade.municipio_choices)
        self.assertIn(("Itu", "Itu"), Cidade.municipio_choices)
        self.assertIn(("Botucatu", "Botucatu"), Cidade.municipio_choices)


class PessoalCalculationTest(TestCase):
    """Testes específicos para cálculos do modelo Pessoal"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )

        self.posto = Posto.objects.create(
            sgb="1ºSGB",
            posto_secao="703151000 - CMT 1º SGB",
            posto_atendimento="EB TESTE",
            cidade_posto="Sorocaba",
            tipo_cidade="Administrativo",
            op_adm="Sede",
            usuario=self.user,
        )

    def test_pessoal_total_calculation(self):
        """Testa o cálculo do total de pessoal"""
        pessoal = Pessoal.objects.create(
            posto=self.posto,
            cel=10,  # Não conta no total
            ten_cel=1,  # Conta
            maj=2,  # Conta
            cap=3,  # Conta
            tenqo=4,  # Conta
            tenqa=5,  # Conta
            asp=10,  # Não conta no total
            st_sgt=6,  # Conta
            cb_sd=7,  # Conta
        )

        # Cálculo esperado: ten_cel + maj + cap + tenqo + tenqa + st_sgt + cb_sd
        # 1 + 2 + 3 + 4 + 5 + 6 + 7 = 28
        expected_total = 1 + 2 + 3 + 4 + 5 + 6 + 7
        self.assertEqual(pessoal.total, expected_total)

    def test_pessoal_zero_values(self):
        """Testa o cálculo com valores zero"""
        pessoal = Pessoal.objects.create(
            posto=self.posto,
            cel=0,
            ten_cel=0,
            maj=0,
            cap=0,
            tenqo=0,
            tenqa=0,
            asp=0,
            st_sgt=0,
            cb_sd=0,
        )

        self.assertEqual(pessoal.total, 0)
