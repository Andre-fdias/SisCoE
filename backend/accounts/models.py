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

from django.db.models import QuerySet # Importe QuerySet

# Importar o modelo Cadastro do app efetivo
# Certifique-se de que este caminho está correto para o seu projeto
try:
    from backend.efetivo.models import Cadastro, DetalhesSituacao
except ImportError:
    # Fallback para ambientes de teste ou onde o app 'efetivo' não está disponível
    class Cadastro(models.Model):
        class Meta:
            app_label = 'efetivo' 
            managed = False 
        nome = models.CharField(max_length=255)
    
    class DetalhesSituacao(models.Model):
        class Meta:
            app_label = 'efetivo'
            managed = False
        sgb = models.CharField(max_length=9, blank=True, null=True)


from .managers import UserManager # Certifique-se de ter este manager definido


class User(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de usuário personalizado.
    """
    email = models.EmailField(_('email address'), max_length=100, unique=True, blank=False, null=False)
    
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
    login_history = models.JSONField(_('Histórico de Login'), default=list, blank=True, null=True)
    is_online = models.BooleanField(default=False)
    is_superuser = models.BooleanField(
        _('superuser status'),
        default=False,
        help_text=_('Designates that this user has all permissions without explicitly assigning them.'),
    )
    must_change_password = models.BooleanField(
        _('must change password'),
        default=False, 
        help_text=_('Designates whether the user must change their password on next login.'),
    )
    last_password_change = models.DateTimeField(
        _('Última Alteração de Senha'), 
        default=timezone.now,
        null=True, 
        blank=True
    )

    @property
    def password_expired(self):
        """
        Verifica se a senha do usuário expirou (mais de 180 dias).
        """
        if self.last_password_change:
            return (timezone.now() - self.last_password_change).days > 180
        return False

    PERMISSOES_CHOICES = (
        ("basico", "Básico"),
        ("visitantes", "Visitante"),
        ("sgb", "SGB"),
        ("gestor", "Gestor"),
        ("admin", "Admin"),
    )
    permissoes = models.CharField(_('Nível de Permissão'), max_length=20, choices=PERMISSOES_CHOICES, default="basico")

    cadastro = models.OneToOneField(
        'efetivo.Cadastro', 
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
        permissions = [
            ("can_view_all_access_history", "Can view all users' access history"),
            ("can_view_all_action_history", "Can view all users' action history"),
            ("can_manage_user_permissions", "Can manage user permissions"),
            ("can_view_user_list", "Can view user list"),
        ]
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
            models.Index(fields=['permissoes']),
        ]

    def has_permission_level(self, required_level):
        """
        Verifica se o usuário tem o nível de permissão necessário (ou superior)
        baseado na hierarquia definida em PERMISSOES_CHOICES.
        """
        level_map = {choice[0]: i for i, choice in enumerate(self.PERMISSOES_CHOICES)}
        
        if self.is_superuser:
            return True

        user_level_value = level_map.get(self.permissoes)
        req_level_value = level_map.get(required_level)

        if user_level_value is None or req_level_value is None:
            return False
            
        return user_level_value >= req_level_value

    def filter_by_permissions(self, queryset: QuerySet) -> QuerySet:
        """
        Filtra um QuerySet (presumivelmente de objetos relacionados a Cadastro)
        com base nas permissões do usuário logado e seu SGB.
        
        Args:
            queryset (QuerySet): O QuerySet a ser filtrado (ex: Cadastro.objects.all()).

        Returns:
            QuerySet: O QuerySet filtrado de acordo com as permissões.
        """
        if self.is_superuser or self.has_permission_level('gestor'):
            return queryset
        
        if self.permissoes == 'sgb':
            user_sgb = None
            if self.cadastro: # Garante que o usuário tem um Cadastro associado
                try:
                    # CORREÇÃO AQUI: Acessar o RelatedManager e obter o objeto mais recente.
                    # Assume que a relação inversa de DetalhesSituacao para Cadastro
                    # é 'detalhes_situacao_set'. Se você definiu um related_name, use-o.
                    # Ex: self.cadastro.meu_related_name.order_by(...).first()
                    latest_detail = self.cadastro.detalhessituacao_set.order_by('-data_alteracao', '-id').first()
                    if latest_detail:
                        user_sgb = latest_detail.sgb
                except DetalhesSituacao.DoesNotExist:
                    pass
                except AttributeError:
                    # Este erro pode ocorrer se 'detalhessituacao_set' não existir
                    # ou se houver um problema com a relação no modelo 'Cadastro'.
                    # Verifique se DetalhesSituacao tem um ForeignKey para Cadastro.
                    pass

            if user_sgb:
                # Este filtro ('detalhes_situacao__sgb') assume que o modelo
                # que está sendo filtrado pelo 'queryset' tem uma relação
                # 'detalhes_situacao' que aponta para DetalhesSituacao,
                # e que DetalhesSituacao tem o campo 'sgb'.
                return queryset.filter(detalhes_situacao__sgb=user_sgb)
            else:
                return queryset.none()
        
        return queryset.none()
    

    def __str__(self):
        return self.email

    def get_full_name(self):
        full_name = f'{self.first_name} {self.last_name}'
        return full_name.strip()

    def get_short_name(self):
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        from django.core.mail import send_mail 
        send_mail(subject, message, from_email, [self.email], **kwargs)
    
    @property
    def is_staff(self):
        return self.is_admin or self.is_superuser

    def get_absolute_url(self):
        return reverse_lazy('accounts:user_detail', kwargs={'pk': self.pk})
    
    def update_login_history(self, ip, computer_name, login_time=None, logout_time=None):
        history = self.login_history if isinstance(self.login_history, list) else []
        
        if login_time and not isinstance(login_time, str):
            login_time = login_time.isoformat()
        if logout_time and not isinstance(logout_time, str):
            logout_time = logout_time.isoformat()

        if login_time:
            history.append({
                'login_time': login_time,
                'ip': ip,
                'computer_name': computer_name,
                'logout_time': None, 
            })
        elif logout_time:
            for entry in reversed(history): 
                if entry.get('logout_time') is None:
                    entry['logout_time'] = logout_time
                    break
        
        self.login_history = history

    def get_login_duration(self, login_time_str, logout_time_str):
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
                
                return " ".join(parts) or "0s" 
            except (ValueError, TypeError):
                return "Erro de formato de data/hora"
        return "N/A"
    
    def format_datetime(self, datetime_str):
        if datetime_str:
            try:
                dt_object = datetime.fromisoformat(datetime_str)
                if timezone.is_aware(dt_object):
                    dt_object = timezone.localtime(dt_object) 
                return dt_object.strftime("%d/%m/%Y %H:%M:%S")
            except (ValueError, TypeError):
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
    """
    Modelo para registrar o aceite de termos de uso pelos usuários.
    """
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='termos_aceitos')
    data_aceite = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    signature_data = models.TextField()  # Armazena a assinatura em base64
    versao_termos = models.CharField(max_length=50)
    
    class Meta:
        verbose_name = "Termo de Aceite"
        verbose_name_plural = "Termos de Aceite"
        ordering = ['-data_aceite']
    
    def __str__(self):
        return f"Termo de {self.usuario.email} em {self.data_aceite.strftime('%d/%m/%Y %H:%M')}"

