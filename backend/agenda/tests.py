from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from .models import Lembrete, Tarefa

User = get_user_model()


class AgendaSecurityTest(TestCase):
    """
    Testa a segurança e o controle de acesso do app 'agenda',
    garantindo que:
    1. Apenas usuários com permissão 'sgb' ou superior podem acessar.
    2. Usuários que acessam só podem ver e gerenciar seus próprios eventos.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Configura dados para todos os testes: usuários com diferentes permissões e eventos para cada um.
        """
        cls.user_basico = User.objects.create_user(
            email="basico@example.com", password="password", permissoes="basico"
        )
        cls.user_sgb = User.objects.create_user(
            email="sgb@example.com", password="password", permissoes="sgb"
        )
        cls.user_outro_sgb = User.objects.create_user(
            email="outro_sgb@example.com", password="password", permissoes="sgb"
        )

        # Eventos do Usuário SGB
        cls.lembrete_sgb = Lembrete.objects.create(
            titulo="Lembrete do SGB", data=timezone.now(), user=cls.user_sgb
        )
        cls.tarefa_sgb = Tarefa.objects.create(
            titulo="Tarefa do SGB", data_inicio=timezone.now(), data_fim=timezone.now() + timedelta(days=1), user=cls.user_sgb
        )

        # Eventos do Outro Usuário SGB
        cls.lembrete_outro = Lembrete.objects.create(
            titulo="Lembrete do Outro SGB", data=timezone.now(), user=cls.user_outro_sgb
        )

    def setUp(self):
        self.client = Client()

    def test_unauthenticated_user_is_redirected(self):
        """Verifica se usuários não autenticados são redirecionados para o login."""
        response = self.client.get(reverse("agenda:calendario"))
        self.assertRedirects(response, f'/accounts/login/?next={reverse("agenda:calendario")}')

    def test_basico_user_is_denied_access(self):
        """[SEGURANÇA] Garante que um usuário com permissão 'basico' é negado com 403."""
        self.client.login(email=self.user_basico.email, password="password")
        response = self.client.get(reverse("agenda:calendario"))
        self.assertEqual(response.status_code, 403, "Usuário 'basico' não recebeu 403 Forbidden.")

    def test_sgb_user_can_access_agenda(self):
        """Verifica se um usuário com permissão 'sgb' pode acessar a agenda."""
        self.client.login(email=self.user_sgb.email, password="password")
        response = self.client.get(reverse("agenda:calendario"))
        self.assertEqual(response.status_code, 200)

    def test_sgb_user_sees_only_own_events(self):
        """[SEGURANÇA] Garante que um usuário 'sgb' vê apenas seus próprios eventos."""
        self.client.login(email=self.user_sgb.email, password="password")
        response = self.client.get(reverse("agenda:calendario"))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.lembrete_sgb.titulo)
        self.assertContains(response, self.tarefa_sgb.titulo)
        self.assertNotContains(response, self.lembrete_outro.titulo)

    def test_sgb_user_cannot_access_others_events_details(self):
        """[SEGURANÇA] Garante que um usuário 'sgb' não pode ver, editar ou excluir eventos de outro."""
        self.client.login(email=self.user_sgb.email, password="password")
        
        # Tenta acessar a página de edição do lembrete de outro usuário
        edit_url = reverse("agenda:lembrete_editar", kwargs={'pk': self.lembrete_outro.pk})
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 404, "Usuário 'sgb' acessou a página de edição de evento alheio.")

        # Tenta excluir o lembrete de outro usuário
        delete_url = reverse("agenda:excluir_lembrete", kwargs={'pk': self.lembrete_outro.pk})
        response = self.client.post(delete_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 404, "Usuário 'sgb' conseguiu excluir evento alheio.")
        self.assertTrue(Lembrete.objects.filter(pk=self.lembrete_outro.pk).exists(), "Evento alheio foi excluído indevidamente.")

    def test_sgb_user_can_manage_own_events(self):
        """Verifica se um usuário 'sgb' pode gerenciar seus próprios eventos."""
        self.client.login(email=self.user_sgb.email, password="password")
        
        # Edição
        edit_url = reverse("agenda:lembrete_editar", kwargs={'pk': self.lembrete_sgb.pk})
        response_edit_get = self.client.get(edit_url)
        self.assertEqual(response_edit_get.status_code, 200)

        # Exclusão
        delete_url = reverse("agenda:excluir_lembrete", kwargs={'pk': self.lembrete_sgb.pk})
        response_delete = self.client.post(delete_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response_delete.status_code, 200)
        self.assertTrue(response_delete.json()['success'])
        self.assertFalse(Lembrete.objects.filter(pk=self.lembrete_sgb.pk).exists())

    def test_create_views_assign_correct_user(self):
        """Verifica se as views de criação atribuem o evento ao usuário 'sgb' logado."""
        self.client.login(email=self.user_sgb.email, password="password")
        
        # Cria Lembrete
        lembrete_data = {
            "titulo": "Lembrete Criado por SGB",
            "descricao": "Teste",
            "data": (timezone.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
            "cor": "#112233"
        }
        response = self.client.post(reverse("agenda:lembrete_novo"), lembrete_data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        new_lembrete = Lembrete.objects.get(titulo="Lembrete Criado por SGB")
        self.assertEqual(new_lembrete.user, self.user_sgb)
        
        # Cria Tarefa
        tarefa_data = {
            "titulo": "Tarefa Criada por SGB",
            "descricao": "Teste",
            "data_inicio": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data_fim": (timezone.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
            "cor": "#332211"
        }
        response = self.client.post(reverse("agenda:tarefa_nova"), tarefa_data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        new_tarefa = Tarefa.objects.get(titulo="Tarefa Criada por SGB")
        self.assertEqual(new_tarefa.user, self.user_sgb)
