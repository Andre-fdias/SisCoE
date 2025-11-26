# backend/municipios/tests.py
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import date
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
import pandas as pd
import tempfile
from PIL import Image

from .models import Posto, Contato, Pessoal, Cidade

User = get_user_model()


class MunicipiosModelsTest(TestCase):
    """Testes para os modelos do app municipios"""

    def setUp(self):
        self.user = User.objects.create_user(email="test@example.com", password="testpass123")
        self.posto = Posto.objects.create(
            sgb="1ºSGB",
            posto_secao="703151000 - CMT 1º SGB",
            posto_atendimento="EB SOROCABA",
            cidade_posto="Sorocaba",
            tipo_cidade="Administrativo",
            op_adm="Sede",
            usuario=self.user,
        )
        self.contato = Contato.objects.create(
            posto=self.posto, telefone="1532223333", rua="Rua Teste", numero="123",
            bairro="Centro", cidade="Sorocaba", cep="18000100", email="teste@example.com",
            longitude=-47.4589, latitude=-23.5012,
        )
        self.pessoal = Pessoal.objects.create(
            posto=self.posto, cel=1, ten_cel=2, maj=3, cap=4, tenqo=5, tenqa=6, asp=7, st_sgt=8, cb_sd=9,
        )
        self.cidade = Cidade.objects.create(
            posto=self.posto, municipio="Sorocaba", descricao="Cidade principal",
            longitude=-47.4589, latitude=-23.5012,
        )

    def test_posto_creation(self):
        self.assertEqual(self.posto.posto_atendimento, "EB SOROCABA")
        self.assertEqual(str(self.posto), "EB SOROCABA - Sorocaba")

    def test_contato_creation(self):
        self.assertEqual(self.contato.telefone, "1532223333")
        self.assertEqual(str(self.contato), "Contato EB SOROCABA")

    def test_pessoal_creation(self):
        self.assertEqual(self.pessoal.total, 37)
        self.assertEqual(str(self.pessoal), "EB SOROCABA - Sorocaba")

    def test_cidade_creation(self):
        self.assertEqual(self.cidade.municipio, "Sorocaba")
        self.assertEqual(str(self.cidade), "Sorocaba - EB SOROCABA")

class MunicipiosSecurityTest(TestCase):
    """
    Testa a segurança e o controle de acesso do app 'municipios', garantindo que:
    1. Apenas usuários com permissão 'sgb' ou superior podem acessar.
    2. Usuários autorizados têm acesso a todas as views e dados.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user_basico = User.objects.create_user(email="basico@example.com", password="password", permissoes="basico")
        cls.user_sgb = User.objects.create_user(email="sgb@example.com", password="password", permissoes="sgb")
        cls.admin_user = User.objects.create_superuser(email="admin@example.com", password="password")
        cls.posto = Posto.objects.create(
            sgb="1ºSGB", posto_secao="703151000 - CMT 1º SGB", cidade_posto="Sorocaba", usuario=cls.admin_user
        )
        cls.cidade = Cidade.objects.create(posto=cls.posto, municipio="Sorocaba")

        cls.url_patterns_to_check = [
            ("municipios:municipios_home", {}),
            ("municipios:posto_list", {}),
            ("municipios:municipio_list", {}),
            ("municipios:posto_detail", {'pk': cls.posto.pk}),
            ("municipios:municipio_detail", {'pk': cls.cidade.pk}),
            ("municipios:posto_create", {}),
        ]

    def setUp(self):
        self.client = Client()

    def test_unauthenticated_user_is_redirected(self):
        """Verifica se usuários não autenticados são redirecionados para a tela de login."""
        for url_name, kwargs in self.url_patterns_to_check:
            url = reverse(url_name, kwargs=kwargs)
            response = self.client.get(url)
            self.assertRedirects(response, f'/accounts/login/?next={url}', msg_prefix=f"URL {url} não redirecionou.")

    def test_basico_user_is_denied_access(self):
        """[SEGURANÇA] Garante que um usuário com permissão 'basico' recebe 403 (Forbidden)."""
        self.client.login(email=self.user_basico.email, password="password")
        for url_name, kwargs in self.url_patterns_to_check:
            url = reverse(url_name, kwargs=kwargs)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 403, f"Acesso à URL {url} não foi negado para usuário 'basico'.")

    def test_sgb_user_has_full_access(self):
        """[SEGURANÇA] Garante que um usuário com permissão 'sgb' tem acesso total (status 200)."""
        self.client.login(email=self.user_sgb.email, password="password")
        for url_name, kwargs in self.url_patterns_to_check:
            if url_name == 'municipios:posto_create':
                continue
            url = reverse(url_name, kwargs=kwargs)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, f"Acesso à URL {url} foi negado indevidamente para usuário 'sgb'.")

    def test_sgb_user_sees_all_records(self):
        """[REQUISITO] Garante que um usuário autorizado vê todos os registros, sem filtro."""
        Posto.objects.create(
            sgb="2ºSGB", posto_secao="703152000 - CMT 2º SGB", cidade_posto="Itu", usuario=self.admin_user
        )
        self.client.login(email=self.user_sgb.email, password="password")
        response = self.client.get(reverse("municipios:posto_list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['postos']), 2, "Usuário 'sgb' não viu todos os registros de postos.")
