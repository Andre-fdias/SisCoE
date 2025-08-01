# accounts/managers.py
from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """
    Gerenciador de usuários personalizado para o modelo User.
    """
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Cria e salva um Usuário com o e-mail e senha fornecidos.
        """
        if not email:
            raise ValueError('O e-mail fornecido deve ser definido')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """
        Cria e salva um Usuário comum.
        Define o nível de permissão como 'basico' por padrão.
        """
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_admin', False) # Definir is_admin como False por padrão para usuários comuns
        extra_fields.setdefault('permissoes', 'basico') # Define o nível de permissão como 'basico'
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """
        Cria e salva um superusuário.
        Define o nível de permissão como 'admin'.
        """
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('permissoes', 'admin') # Superusuário tem permissão 'admin'

        if extra_fields.get('is_admin') is not True:
            raise ValueError('Superuser deve ter is_admin=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser deve ter is_superuser=True.')
        if extra_fields.get('permissoes') != 'admin': # Verifica a permissão também
            raise ValueError('Superuser deve ter permissoes="admin".')

        return self._create_user(email, password, **extra_fields)

