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
    garantindo que um usuário só pode ver e gerenciar seus próprios eventos.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Configura dados para todos os testes: dois usuários e eventos para cada um.
        """
        # Usuário A
        cls.user_a = User.objects.create_user(
            email="usera@example.com",
            password="password_a",
            permissoes="basico"
        )
        # Usuário B
        cls.user_b = User.objects.create_user(
            email="userb@example.com",
            password="password_b",
            permissoes="basico"
        )

        # Eventos do Usuário A
        cls.lembrete_a = Lembrete.objects.create(
            titulo="Lembrete do Usuário A",
            data=timezone.now(),
            user=cls.user_a
        )
        cls.tarefa_a = Tarefa.objects.create(
            titulo="Tarefa do Usuário A",
            data_inicio=timezone.now(),
            data_fim=timezone.now() + timedelta(days=1),
            user=cls.user_a
        )

        # Eventos do Usuário B
        cls.lembrete_b = Lembrete.objects.create(
            titulo="Lembrete do Usuário B",
            data=timezone.now(),
            user=cls.user_b
        )
        cls.tarefa_b = Tarefa.objects.create(
            titulo="Tarefa do Usuário B",
            data_inicio=timezone.now(),
            data_fim=timezone.now() + timedelta(days=1),
            user=cls.user_b
        )

    def setUp(self):
        self.client = Client()

    def test_unauthenticated_user_is_redirected(self):
        """Verifica se usuários não autenticados são redirecionados para o login."""
        urls = [
            reverse("agenda:calendario"),
            reverse("agenda:lembrete_editar", kwargs={'pk': self.lembrete_a.pk}),
            reverse("agenda:tarefa_editar", kwargs={'pk': self.tarefa_a.pk}),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertRedirects(response, f'/accounts/login/?next={url}')

    def test_user_sees_only_own_events_in_list(self):
        """[SEGURANÇA] Garante que um usuário vê apenas seus próprios eventos no calendário."""
        self.client.login(email=self.user_a.email, password="password_a")
        response = self.client.get(reverse("agenda:calendario"))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.lembrete_a.titulo)
        self.assertContains(response, self.tarefa_a.titulo)
        self.assertNotContains(response, self.lembrete_b.titulo)
        self.assertNotContains(response, self.tarefa_b.titulo)

    def test_user_cannot_access_edit_page_of_others_events(self):
        """[SEGURANÇA] Garante que um usuário não pode acessar a página de edição de eventos de outro."""
        self.client.login(email=self.user_a.email, password="password_a")
        
        # Tenta acessar a página de edição do lembrete do usuário B
        lembrete_b_url = reverse("agenda:lembrete_editar", kwargs={'pk': self.lembrete_b.pk})
        response = self.client.get(lembrete_b_url)
        self.assertEqual(response.status_code, 404, "Usuário A acessou a página de edição do Lembrete do usuário B.")

        # Tenta acessar a página de edição da tarefa do usuário B
        tarefa_b_url = reverse("agenda:tarefa_editar", kwargs={'pk': self.tarefa_b.pk})
        response = self.client.get(tarefa_b_url)
        self.assertEqual(response.status_code, 404, "Usuário A acessou a página de edição da Tarefa do usuário B.")

    def test_user_cannot_delete_others_events(self):
        """[SEGURANÇA] Garante que um usuário não pode excluir eventos de outro."""
        self.client.login(email=self.user_a.email, password="password_a")

        # Tenta excluir o lembrete do usuário B
        lembrete_b_url = reverse("agenda:excluir_lembrete", kwargs={'pk': self.lembrete_b.pk})
        response = self.client.post(lembrete_b_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 404, "Usuário A conseguiu enviar um POST de exclusão para o Lembrete do usuário B.")
        self.assertTrue(Lembrete.objects.filter(pk=self.lembrete_b.pk).exists(), "Lembrete do usuário B foi excluído indevidamente.")

        # Tenta excluir a tarefa do usuário B
        tarefa_b_url = reverse("agenda:excluir_tarefa", kwargs={'pk': self.tarefa_b.pk})
        response = self.client.post(tarefa_b_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 404, "Usuário A conseguiu enviar um POST de exclusão para a Tarefa do usuário B.")
        self.assertTrue(Tarefa.objects.filter(pk=self.tarefa_b.pk).exists(), "Tarefa do usuário B foi excluída indevidamente.")
    
    def test_user_can_edit_and_delete_own_events(self):
        """Verifica se um usuário pode editar e excluir seus próprios eventos."""
        self.client.login(email=self.user_a.email, password="password_a")
        
        # Edição
        edit_url = reverse("agenda:lembrete_editar", kwargs={'pk': self.lembrete_a.pk})
        response_edit_get = self.client.get(edit_url)
        self.assertEqual(response_edit_get.status_code, 200)

        # Exclusão
        delete_url = reverse("agenda:excluir_lembrete", kwargs={'pk': self.lembrete_a.pk})
        response_delete = self.client.post(delete_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response_delete.status_code, 200)
        self.assertTrue(response_delete.json()['success'])
        self.assertFalse(Lembrete.objects.filter(pk=self.lembrete_a.pk).exists())

    def test_create_views_assign_correct_user(self):
        """Verifica se as views de criação atribuem o evento ao usuário logado."""
        self.client.login(email=self.user_a.email, password="password_a")
        
        # Cria Lembrete
        lembrete_data = {
            "titulo": "Lembrete Criado em Teste",
            "descricao": "Teste",
            "data": (timezone.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
            "cor": "#112233"
        }
        response = self.client.post(reverse("agenda:lembrete_novo"), lembrete_data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        new_lembrete = Lembrete.objects.get(titulo="Lembrete Criado em Teste")
        self.assertEqual(new_lembrete.user, self.user_a)
        
        # Cria Tarefa
        tarefa_data = {
            "titulo": "Tarefa Criada em Teste",
            "descricao": "Teste",
            "data_inicio": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data_fim": (timezone.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
            "cor": "#332211"
        }
        response = self.client.post(reverse("agenda:tarefa_nova"), tarefa_data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        new_tarefa = Tarefa.objects.get(titulo="Tarefa Criada em Teste")
        self.assertEqual(new_tarefa.user, self.user_a)