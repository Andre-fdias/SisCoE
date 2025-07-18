# accounts/models.py
from __future__ import unicode_literals

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.core.mail import send_mail
from django.db import models
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.safestring import mark_safe
from django.utils import timezone
from datetime import datetime, timedelta

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True)
    is_active = models.BooleanField(_('active'), default=True)
    is_admin = models.BooleanField(
        _('admin status'),
        default=False,
        help_text=_(
            'Designates whether the user can log into this admin site.'),)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_computer_name = models.CharField(max_length=255, null=True, blank=True)
    login_history = models.JSONField(default=list, blank=True)
    is_online = models.BooleanField(default=False)
    is_superuser = models.BooleanField(
        _('superuser status'),
        default=False,
        help_text=_('Designates that this user has all permissions without explicitly assigning them.'),
    )
    is_staff = models.BooleanField(default=False)
    # login_history = models.JSONField(default=list) # This is a duplicate, can be removed.


    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    def get_full_name(self):
        '''
        Returns the first_name plus the last_name, with a space in between.
        '''
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        '''
        Returns the short name for the user.
        '''
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        '''
        Sends an email to this User.
        '''
        send_mail(subject, message, from_email, [self.email], **kwargs)


    
    @property
    def is_staff(self):
        return self.is_admin or super().is_superuser

    def get_absolute_url(self):
        return reverse_lazy('user_detail', kwargs={'pk': self.pk})
    

    
    def update_login_history(self, ip, computer_name, login_time=None, logout_time=None):
        history = self.login_history
        
        # Converte o login_time de string ISO para datetime se for uma string
        if isinstance(login_time, str):
            login_time = datetime.fromisoformat(login_time)
        
        # Converte o logout_time de string ISO para datetime se for uma string
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
            # Encontra a última entrada de login sem logout e a atualiza
            for entry in reversed(history):
                if entry.get('logout_time') is None:
                    entry['logout_time'] = logout_time.isoformat()
                    break
        self.login_history = history
        self.save()

    def get_login_duration(self, login_time_str, logout_time_str):
        if login_time_str and logout_time_str:
            login_time = datetime.fromisoformat(login_time_str)
            logout_time = datetime.fromisoformat(logout_time_str)
            duration = logout_time - login_time
            # Formata a duração para ser mais legível
            days, seconds = duration.days, duration.seconds
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            return f"{days}d {hours:02}h {minutes:02}m {seconds:02}s"
        return "N/A"
    
    def format_datetime(self, datetime_str):
        if datetime_str:
            dt_object = datetime.fromisoformat(datetime_str)
            return dt_object.strftime("%d/%m/%Y %H:%M:%S")
        return "N/A"



class UserActionLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    computer_name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - {self.action} - {self.timestamp}"
    

class SearchableUserActionLog(UserActionLog):
    class Meta:
        proxy = True
        
    def get_search_result(self):
        return {
            'title': f"{self.user.email} - {self.action}",
            'fields': {
                'Usuário': self.user.email,
                'Ação': self.action,
                'Data': self.timestamp.strftime('%d/%m/%Y %H:%M'),
                'IP': self.ip_address
            }
        }
    

# accounts/models.py
class SearchableUser(User):
    class Meta:
        proxy = True
        
    def get_search_result(self):
        # Usando email como identificador principal
        return {
            'title': f"{self.get_full_name() or self.email}",
            'fields': {
                'Nome': self.get_full_name() or '-',
                'Email': self.email
            }
        }