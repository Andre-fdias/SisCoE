# backend/accounts/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.test.utils import override_settings

from .models import User, UserActionLog, TermosAceite, Profile
from .forms import CustomAuthenticationForm, CustomUserCreationForm, PasswordChangeForm

User = get_user_model()


class UserModelTest(TestCase):
    """Testes para o modelo User"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@email.com',
            password='testpassword123',
            first_name='Test',
            last_name='User',
            permissoes='basico'
        )
        self.superuser = User.objects.create_superuser(
            email='super@email.com',
            password='superpassword123'
        )

    def test_user_creation(self):
        """Testa a criação de usuário comum"""
        self.assertEqual(self.user.email, 'test@email.com')
        self.assertEqual(self.user.first_name, 'Test')
        self.assertEqual(self.user.last_name, 'User')
        self.assertEqual(self.user.permissoes, 'basico')
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_admin)
        self.assertFalse(self.user.is_superuser)

    def test_superuser_creation(self):
        """Testa a criação de superusuário"""
        self.assertEqual(self.superuser.email, 'super@email.com')
        self.assertTrue(self.superuser.is_active)
        self.assertTrue(self.superuser.is_admin)
        self.assertTrue(self.superuser.is_superuser)
        self.assertEqual(self.superuser.permissoes, 'admin')

    def test_user_str_representation(self):
        """Testa a representação em string do usuário"""
        self.assertEqual(str(self.user), 'test@email.com')

    def test_get_full_name(self):
        """Testa o método get_full_name"""
        self.assertEqual(self.user.get_full_name(), 'Test User')

    def test_get_short_name(self):
        """Testa o método get_short_name"""
        self.assertEqual(self.user.get_short_name(), 'Test')

    def test_has_permission_level(self):
        """Testa o sistema de hierarquia de permissões"""
        # Teste para usuário básico
        self.assertTrue(self.user.has_permission_level('basico'))
        self.assertFalse(self.user.has_permission_level('gestor'))
        
        # Teste para superusuário (deve ter todas as permissões)
        self.assertTrue(self.superuser.has_permission_level('basico'))
        self.assertTrue(self.superuser.has_permission_level('admin'))

    def test_is_staff_property(self):
        """Testa a propriedade is_staff"""
        self.assertFalse(self.user.is_staff)
        self.assertTrue(self.superuser.is_staff)


class UserActionLogTest(TestCase):
    """Testes para o modelo UserActionLog"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@email.com',
            password='testpassword123'
        )

    def test_action_log_creation(self):
        """Testa a criação de log de ações do usuário"""
        log = UserActionLog.objects.create(
            user=self.user,
            action='Test action',
            ip_address='127.0.0.1',
            computer_name='TEST-PC'
        )
        
        self.assertEqual(str(log), f"{self.user.email} - Test action")
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, 'Test action')


class AuthenticationFormsTest(TestCase):
    """Testes para formulários de autenticação"""
    
    def test_custom_authentication_form(self):
        """Testa o formulário de autenticação personalizado"""
        # Criar um usuário primeiro para o formulário de autenticação funcionar
        user = User.objects.create_user(
            email='test@email.com',
            password='testpassword123'
        )
        
        form_data = {
            'username': 'test@email.com',
            'password': 'testpassword123'
        }
        form = CustomAuthenticationForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Verifica se o campo username é tratado como email
        self.assertEqual(form.fields['username'].label, "Email")

    def test_custom_user_creation_form(self):
        """Testa o formulário de criação de usuário"""
        form_data = {
            'email': 'newuser@email.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123',
            'permissoes': 'basico'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        self.assertEqual(user.email, 'newuser@email.com')
        self.assertTrue(user.is_active)

    def test_password_change_form(self):
        """Testa o formulário de alteração de senha"""
        user = User.objects.create_user(
            email='test@email.com',
            password='oldpassword123'
        )
        
        form_data = {
            'old_password': 'oldpassword123',
            'new_password1': 'newcomplexpassword123',
            'new_password2': 'newcomplexpassword123'
        }
        form = PasswordChangeForm(user=user, data=form_data)
        self.assertTrue(form.is_valid())


class ViewsTest(TestCase):
    """Testes para views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@email.com',
            password='testpassword123',
            first_name='Test',
            last_name='User'
        )

    def test_login_view_get(self):
        """Testa acesso à página de login via GET"""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 302)  # Redireciona para landing page

    def test_login_view_post_success(self):
        """Testa login bem-sucedido"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'test@email.com',
            'password': 'testpassword123'
        })
        # Deve redirecionar após login bem-sucedido
        self.assertEqual(response.status_code, 302)

    def test_login_view_post_failure(self):
        """Testa login com credenciais inválidas"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'test@email.com',
            'password': 'wrongpassword'
        })
        # Deve redirecionar com erro
        self.assertEqual(response.status_code, 302)

    def test_logout_view(self):
        """Testa logout"""
        self.client.login(email='test@email.com', password='testpassword123')
        response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)  # Redireciona após logout

    def test_user_detail_view_own_profile(self):
        """Testa visualização do próprio perfil"""
        self.client.login(email='test@email.com', password='testpassword123')
        response = self.client.get(reverse('accounts:user_detail', args=[self.user.pk]))
        self.assertEqual(response.status_code, 200)

    def test_acesso_negado_view(self):
        """Testa página de acesso negado"""
        # A view acesso_negado retorna status 403, não 200
        response = self.client.get(reverse('accounts:acesso_negado'))
        self.assertEqual(response.status_code, 403)  # Corrigido para 403
        self.assertTemplateUsed(response, 'accounts/acesso_negado.html')


class PermissionTest(TestCase):
    """Testes para sistema de permissões"""
    
    def setUp(self):
        self.client = Client()
        
        # Criar usuários com diferentes níveis de permissão
        self.basico_user = User.objects.create_user(
            email='basico@email.com',
            password='password123',
            permissoes='basico'
        )
        self.gestor_user = User.objects.create_user(
            email='gestor@email.com',
            password='password123',
            permissoes='gestor'
        )

    def test_permission_hierarchy(self):
        """Testa a hierarquia de permissões"""
        self.assertTrue(self.gestor_user.has_permission_level('basico'))
        self.assertTrue(self.gestor_user.has_permission_level('gestor'))
        self.assertFalse(self.basico_user.has_permission_level('gestor'))


class ForcePasswordChangeTest(TestCase):
    """Testes para troca de senha forçada"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@email.com',
            password='tempassword123',
            must_change_password=True
        )

    def test_force_password_change_redirect(self):
        """Testa redirecionamento para troca de senha forçada"""
        self.client.login(email='test@email.com', password='tempassword123')
        response = self.client.get('/')  # Tenta acessar qualquer página
        # Deve redirecionar para troca de senha forçada
        self.assertEqual(response.status_code, 302)
        self.assertIn('force-password-change', response.url)

    def test_force_password_change_view(self):
        """Testa a view de troca de senha forçada"""
        self.client.login(email='test@email.com', password='tempassword123')
        response = self.client.get(reverse('accounts:force_password_change'))
        self.assertEqual(response.status_code, 200)


class ProfileModelTest(TestCase):
    """Testes para o modelo Profile"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@email.com',
            password='testpassword123'
        )

    def test_profile_creation(self):
        """Testa a criação de perfil associado ao usuário"""
        profile = Profile.objects.create(
            user=self.user,
            bio='Test biography',
            avatar=None
        )
        
        self.assertEqual(str(profile), f"Perfil de {self.user.email}")
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.bio, 'Test biography')


class UserManagerTest(TestCase):
    """Testes para o UserManager"""
    
    def test_create_user(self):
        """Testa o gerenciador de usuários para criação de usuário comum"""
        user = User.objects.create_user(
            email='manager@email.com',
            password='password123'
        )
        
        self.assertEqual(user.email, 'manager@email.com')
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_admin)
        self.assertEqual(user.permissoes, 'basico')

    def test_create_superuser(self):
        """Testa o gerenciador de usuários para criação de superusuário"""
        superuser = User.objects.create_superuser(
            email='supermanager@email.com',
            password='password123'
        )
        
        self.assertEqual(superuser.email, 'supermanager@email.com')
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_admin)
        self.assertEqual(superuser.permissoes, 'admin')

    def test_create_user_no_email(self):
        """Testa criação de usuário sem email deve falhar"""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email='',
                password='password123'
            )


class TermosAceiteTest(TestCase):
    """Testes para o modelo TermosAceite"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@email.com',
            password='testpassword123'
        )

    def test_termo_aceite_creation(self):
        """Testa a criação de termo de aceite"""
        termo = TermosAceite.objects.create(
            usuario=self.user,
            ip_address='127.0.0.1',
            signature_data='test_signature_data',
            versao_termos='1.0'
        )
        
        self.assertEqual(str(termo), f"Termo de {self.user.email}")
        self.assertEqual(termo.usuario, self.user)
        self.assertEqual(termo.versao_termos, '1.0')


class IntegrationTest(TestCase):
    """Testes de integração"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='integration@email.com',
            password='password123',
            first_name='Integration',
            last_name='Test'
        )

    def test_complete_user_flow(self):
        """Testa um fluxo completo do usuário: login -> navegação -> logout"""
        # Login
        login_success = self.client.login(email='integration@email.com', password='password123')
        self.assertTrue(login_success)
        
        # Acessar perfil
        response = self.client.get(reverse('accounts:user_detail', args=[self.user.pk]))
        self.assertEqual(response.status_code, 200)
        
        # Logout
        response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)


class SecurityTest(TestCase):
    """Testes de segurança"""
    
    def setUp(self):
        self.client = Client()

    def test_brute_force_protection(self):
        """Testa proteção contra força bruta (múltiplas tentativas de login)"""
        for i in range(5):
            response = self.client.post(reverse('accounts:login'), {
                'username': 'nonexistent@email.com',
                'password': f'wrongpassword{i}'
            })
            # Todas as tentativas devem falhar
            self.assertNotEqual(response.status_code, 200)


class URLTest(TestCase):
    """Testes para URLs"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='url_test@email.com',
            password='password123'
        )

    def test_nonexistent_url_returns_404(self):
        """Testa que URLs não existentes retornam 404"""
        response = self.client.get('/accounts/nonexistent-url/')
        self.assertEqual(response.status_code, 404)

    def test_authenticated_access_to_protected_urls(self):
        """Testa acesso autenticado a URLs protegidas"""
        self.client.login(email='url_test@email.com', password='password123')
        response = self.client.get(reverse('accounts:user_detail', args=[self.user.pk]))
        self.assertEqual(response.status_code, 200)


class ServiceTest(TestCase):
    """Testes básicos para serviços"""
    
    def test_brevo_service_import(self):
        """Testa que o módulo brevo_service pode ser importado"""
        try:
            from .brevo_service import send_brevo_email
            self.assertTrue(callable(send_brevo_email))
        except ImportError:
            self.fail("Não foi possível importar send_brevo_email")

    def test_utils_import(self):
        """Testa que os utilitários podem ser importados"""
        try:
            from .utils import get_client_ip, get_computer_name
            self.assertTrue(callable(get_client_ip))
            self.assertTrue(callable(get_computer_name))
        except ImportError:
            self.fail("Não foi possível importar utilitários")


class AppConfigTest(TestCase):
    """Testes para configuração do app"""
    
    def test_app_name(self):
        """Testa o nome do app"""
        from django.apps import apps
        app_config = apps.get_app_config('accounts')
        self.assertEqual(app_config.name, 'backend.accounts')

    def test_user_model(self):
        """Testa que o modelo User está correto"""
        self.assertEqual(get_user_model(), User)