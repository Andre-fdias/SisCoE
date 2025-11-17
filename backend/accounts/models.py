from __future__ import unicode_literals

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.conf import settings
from django.db import models
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models import QuerySet

try:
    from backend.efetivo.models import Cadastro, DetalhesSituacao
except ImportError:

    class Cadastro(models.Model):
        class Meta:
            app_label = "efetivo"
            managed = False

        nome = models.CharField(max_length=255)

    class DetalhesSituacao(models.Model):
        class Meta:
            app_label = "efetivo"
            managed = False

        sgb = models.CharField(max_length=9, blank=True, null=True)


from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_("email address"), max_length=100, unique=True)
    first_name = models.CharField(_("first name"), max_length=150)
    last_name = models.CharField(_("last name"), max_length=150)

    date_joined = models.DateTimeField(_("date joined"), auto_now_add=True)
    is_active = models.BooleanField(_("active"), default=True)
    is_admin = models.BooleanField(_("admin status"), default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_computer_name = models.CharField(max_length=255, null=True, blank=True)
    login_history = models.JSONField(
        _("Login History"), default=list, blank=True, null=True
    )
    is_online = models.BooleanField(default=False)
    must_change_password = models.BooleanField(default=False)
    last_password_change = models.DateTimeField(
        default=timezone.now, null=True, blank=True
    )

    # Definindo as permissões em ordem de hierarquia
    PERMISSOES_CHOICES = (
        ("basico", "Básico"),
        ("visitantes", "Visitante"),  # Agora o 2º nível
        ("sgb", "SGB"),
        ("gestor", "Gestor"),
        ("admin", "Admin"),
    )
    permissoes = models.CharField(
        _("Permission Level"),
        max_length=20,
        choices=PERMISSOES_CHOICES,
        default="basico",
    )

    cadastro = models.OneToOneField(
        "efetivo.Cadastro",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_account",
        verbose_name=_("Military Record"),
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["permissoes"]),
        ]

    def has_permission_level(self, required_level):
        hierarchy = {"basico": 0, "visitantes": 1, "sgb": 2, "gestor": 3, "admin": 4}

        if self.is_superuser:
            return True

        user_level = hierarchy.get(self.permissoes)
        req_level = hierarchy.get(required_level)

        if None in (user_level, req_level):
            return False

        return user_level >= req_level

    def get_user_sgb(self):
        """Obtém o SGB do usuário a partir de seu cadastro associado"""
        if not hasattr(self, "_user_sgb_cache"):
            self._user_sgb_cache = None
            if self.cadastro:
                try:
                    latest_situacao = self.cadastro.detalhes_situacao.order_by(
                        "-data_alteracao"
                    ).first()
                    if latest_situacao:
                        self._user_sgb_cache = latest_situacao.sgb
                except AttributeError:
                    pass
        return self._user_sgb_cache

    def filter_by_permissions(self, queryset: QuerySet) -> QuerySet:
        """
        Filtra um QuerySet baseado nas permissões do usuário:
        - Superusuários e gestores veem tudo
        - Usuários SGB veem apenas registros do mesmo SGB
         - Outros veem um queryset vazio
        """
        if self.is_superuser or self.has_permission_level("gestor"):
            return queryset

        if self.permissoes == "sgb":
            user_sgb = self.get_user_sgb()
            if user_sgb:
                return queryset.filter(detalhes_situacao__sgb=user_sgb).distinct()
            return queryset.none()

        return queryset.none()

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        from django.core.mail import send_mail

        send_mail(subject, message, from_email, [self.email], **kwargs)

    @property
    def is_staff(self):
        return self.is_admin or self.is_superuser

    @property
    def password_expired(self):
        if self.last_password_change:
            return (timezone.now() - self.last_password_change).days > 180
        return False

    def get_absolute_url(self):
        return reverse_lazy("accounts:user_detail", kwargs={"pk": self.pk})

    def update_login_history(
        self, ip, computer_name, login_time=None, logout_time=None
    ):
        history = self.login_history if isinstance(self.login_history, list) else []

        if login_time:
            history.append(
                {
                    "login_time": (
                        login_time.isoformat()
                        if not isinstance(login_time, str)
                        else login_time
                    ),
                    "ip": ip,
                    "computer_name": computer_name,
                    "logout_time": None,
                }
            )
        elif logout_time:
            for entry in reversed(history):
                if entry.get("logout_time") is None:
                    entry["logout_time"] = (
                        logout_time.isoformat()
                        if not isinstance(logout_time, str)
                        else logout_time
                    )
                    break

        self.login_history = history


class UserActionLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    computer_name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["timestamp"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.action}"


class TermosAceite(models.Model):
    usuario = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="termos_aceitos"
    )
    data_aceite = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    signature_data = models.TextField()
    versao_termos = models.CharField(max_length=50)

    class Meta:
        ordering = ["-data_aceite"]

    def __str__(self):
        return f"Termo de {self.usuario.email}"


# Proxy Models para busca
class SearchableUser(User):
    class Meta:
        proxy = True
        verbose_name = _("Searchable User")

    def get_search_result(self):
        return {
            "title": self.get_full_name() or self.email,
            "fields": {"Full Name": self.get_full_name(), "Email": self.email},
        }


class SearchableUserActionLog(UserActionLog):
    class Meta:
        proxy = True
        verbose_name = _("Searchable Action Log")

    def get_search_result(self):
        return {
            "title": f"{self.user.email} - {self.action}",
            "fields": {
                "User": self.user.email,
                "Action": self.action,
                "Date": self.timestamp.strftime("%d/%m/%Y %H:%M"),
                "IP": self.ip_address or "N/A",
            },
        }


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    bio = models.TextField(blank=True, null=True, verbose_name="Biografia")
    avatar = models.ImageField(
        upload_to="avatars/", null=True, blank=True, verbose_name="Avatar"
    )

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfis"

    def __str__(self):
        return f"Perfil de {self.user.email}"
