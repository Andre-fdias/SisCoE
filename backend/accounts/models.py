# accounts/models.py
from __future__ import unicode_literals

from datetime import datetime, timedelta

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.dispatch import receiver
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .managers import UserManager
# Importar o modelo Cadastro do app efetivo
from backend.efetivo.models import Cadastro


class User(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de usuário personalizado.
    """
    email = models.EmailField(_('email address'), max_length=100, unique=True, blank=False, null=False)
    
    # first_name e last_name serão preenchidos com nome e nome_de_guerra do Cadastro
    first_name = models.CharField(_('first name'), max_length=150, blank=False, null=False)
    last_name = models.CharField(_('last name'), max_length=150, blank=False, null=False)
    
    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True)
    is_active = models.BooleanField(_('active'), default=True)
    is_admin = models.BooleanField(
        _('admin status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_computer_name = models.CharField(max_length=255, null=True, blank=True)
    login_history = models.JSONField(default=list, blank=True)
    is_online = models.BooleanField(default=False)
    is_superuser = models.BooleanField(
        _('superuser status'),
        default=False,
        help_text=_('Designates that this user has all permissions without explicitly assigning them.'),
    )
    # NOVO CAMPO: Indica se o usuário precisa trocar a senha
    must_change_password = models.BooleanField(
        _('must change password'),
        default=False, # Definir como False por padrão, será True na criação/reset
        help_text=_('Designates whether the user must change their password on next login.'),
    )
    # Novo campo para registrar a data da última alteração de senha
    last_password_change = models.DateTimeField(
        _('Última Alteração de Senha'), 
        default=timezone.now,
        null=True, # Permitir valores nulos, embora o default já resolva
        blank=True
    )

    @property
    def password_expired(self):
        """
        Verifica se a senha do usuário expirou (mais de 180 dias).
        """
        if self.last_password_change:
            # Compara a data da última alteração de senha com a data atual
            return (timezone.now() - self.last_password_change).days > 180
        return False

    # Novo campo para níveis de permissão
    PERMISSOES_CHOICES = (
        ("basico", "Básico"),
        ("sgb", "SGB"),
        ("gestor", "Gestor"),
        ("admin", "Admin"),
        ("visitantes", "Visitante"),
    )
    permissoes = models.CharField(_('Nível de Permissão'), max_length=20, choices=PERMISSOES_CHOICES, default="basico")

    # Adiciona a relação OneToOne com o modelo Cadastro
    # on_delete=models.SET_NULL significa que se um Cadastro for deletado, o campo 'cadastro' aqui será NULL
    # related_name='user_account' permite acessar o User a partir do Cadastro (ex: cadastro_obj.user_account)
    cadastro = models.OneToOneField(
        Cadastro, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='user_account',
        verbose_name=_("Cadastro Militar")
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
            models.Index(fields=['permissoes']),
        ]


    def __str__(self):
        """Retorna a representação em string do usuário (email)."""
        return self.email

    def has_perm(self, perm, obj=None):
        """Verifica se o usuário tem uma permissão específica."""
        return True

    def has_module_perms(self, app_label):
        """Verifica se o usuário tem permissões para visualizar o app `app_label`."""
        return True

    def get_full_name(self):
        """
        Retorna o primeiro nome mais o sobrenome, com um espaço entre eles.
        """
        full_name = f'{self.first_name} {self.last_name}'
        return full_name.strip()

    def get_short_name(self):
        """
        Retorna o nome curto para o usuário (primeiro nome).
        """
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Envia um e-mail para este usuário.
        """
        from django.core.mail import send_mail 
        send_mail(subject, message, from_email, [self.email], **kwargs)
    
    # NOTE: A propriedade 'cadastro' foi removida pois já existe um campo 'cadastro'
    # que serve ao mesmo propósito de forma mais direta e eficiente.

    @property
    def is_staff(self):
        """
        Indica se o usuário pode acessar o site de administração.
        """
        return self.is_admin or self.is_superuser

    def get_absolute_url(self):
        """Retorna a URL absoluta para a página de detalhes do usuário."""
        return reverse_lazy('accounts:user_detail', kwargs={'pk': self.pk})
    
    def update_login_history(self, ip, computer_name, login_time=None, logout_time=None):
        """
        Atualiza o histórico de login do usuário.
        """
        history = self.login_history
        
        if isinstance(login_time, str):
            login_time = datetime.fromisoformat(login_time)
        
        if isinstance(logout_time, str):
            logout_time = datetime.fromisoformat(logout_time)

        if login_time:
            history.append({
                'login_time': login_time.isoformat() if login_time else None,
                'ip': ip,
                'computer_name': computer_name,
                'logout_time': None,
            })
        elif logout_time:
            for entry in reversed(history):
                if entry.get('logout_time') is None:
                    entry['logout_time'] = logout_time.isoformat()
                    break
        self.login_history = history

    def get_login_duration(self, login_time_str, logout_time_str):
        """
        Calcula e formata a duração de uma sessão de login.
        """
        if login_time_str and logout_time_str:
            try:
                login_time = datetime.fromisoformat(login_time_str)
                logout_time = datetime.fromisoformat(logout_time_str)
                duration = logout_time - login_time
                
                days, seconds = duration.days, duration.seconds
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                seconds = seconds % 60
                
                parts = []
                if days > 0:
                    parts.append(f"{days}d")
                if hours > 0:
                    parts.append(f"{hours:02}h")
                if minutes > 0:
                    parts.append(f"{minutes:02}m")
                if seconds > 0 or not parts:
                    parts.append(f"{seconds:02}s")
                
                return " ".join(parts)
            except ValueError:
                return "Erro de formato de data"
        return "N/A"
    
    def format_datetime(self, datetime_str):
        """
        Formata uma string de data/hora ISO para um formato legível.
        """
        if datetime_str:
            try:
                dt_object = datetime.fromisoformat(datetime_str)
                if timezone.is_aware(dt_object):
                    dt_object = timezone.localtime(dt_object)
                return dt_object.strftime("%d/%m/%Y %H:%M:%S")
            except ValueError:
                return "Formato inválido"
        return "N/A"

class UserActionLog(models.Model):
    """
    Modelo para registrar as ações dos usuários no sistema.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("Usuário"))
    action = models.CharField(_("Ação"), max_length=255)
    timestamp = models.DateTimeField(_("Data/Hora"), auto_now_add=True)
    ip_address = models.GenericIPAddressField(_("Endereço IP"), null=True, blank=True)
    computer_name = models.CharField(_("Nome do Computador"), max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = _("Log de Ação do Usuário")
        verbose_name_plural = _("Logs de Ações dos Usuários")
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.action} - {self.timestamp.strftime('%d/%m/%Y %H:%M:%S')}"
    

class SearchableUserActionLog(UserActionLog):
    """
    Proxy Model para UserActionLog para ser usado em funcionalidades de busca.
    """
    class Meta:
        proxy = True
        verbose_name = _("Log de Ação Pesquisável")
        verbose_name_plural = _("Logs de Ações Pesquisáveis")
        
    def get_search_result(self):
        """Retorna um dicionário formatado para resultados de busca."""
        return {
            'title': f"{self.user.email} - {self.action}",
            'fields': {
                'Usuário': self.user.email,
                'Ação': self.action,
                'Data': self.timestamp.strftime('%d/%m/%Y %H:%M'),
                'IP': self.ip_address or 'N/A'
            }
        }
    

class SearchableUser(User):
    """
    Proxy Model para User para ser usado em funcionalidades de busca.
    """
    class Meta:
        proxy = True
        verbose_name = _("Usuário Pesquisável")
        verbose_name_plural = _("Usuários Pesquisáveis") 
        
    def get_search_result(self):
        """Retorna um dicionário formatado para resultados de busca."""
        return {
            'title': self.get_full_name() or self.email,
            'fields': {
                'Nome Completo': self.get_full_name() or 'N/A',
                'Email': self.email
            }
        }


class TermosAceite(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='termos_aceitos')
    data_aceite = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    signature_data = models.TextField()  # Armazena a assinatura em base64
    versao_termos = models.CharField(max_length=50)
    
    class Meta:
        verbose_name = "Termo de Aceite"
        verbose_name_plural = "Termos de Aceite"
        
    def __str__(self):
        return f"Aceite de {self.usuario.email} em {self.data_aceite}"

