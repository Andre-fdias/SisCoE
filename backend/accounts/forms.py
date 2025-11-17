# accounts/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    UserCreationForm,
    UserChangeForm,
    PasswordChangeForm as AuthPasswordChangeForm,
    AuthenticationForm,
)
from django.forms import PasswordInput

User = get_user_model()


class CustomAuthenticationForm(AuthenticationForm):
    """
    Formulário de autenticação personalizado para permitir login por email.
    """

    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={"autofocus": True, "class": "form-input", "placeholder": "Seu Email"}
        ),
    )
    password = forms.CharField(
        label="Senha",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"class": "form-input", "placeholder": "Sua Senha"}
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Renomeia o campo 'username' para 'email' na validação interna
        self.fields["username"].label = "Email"
        self.fields["username"].widget.attrs["placeholder"] = "Seu Email"


class CustomUserCreationForm(UserCreationForm):
    """
    Um formulário personalizado para criação de usuários.
    """

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "permissoes",
        )  # Adicione 'permissoes' aqui
        field_classes = {"email": forms.EmailField}

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este e-mail já está em uso.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = True  # Ativa o usuário por padrão ao criar
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    """
    Um formulário personalizado para edição de usuários.
    """

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_admin",
            "permissoes",
            "must_change_password",
        )
        field_classes = {"email": forms.EmailField}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Se o usuário não for superusuário, remove a opção de alterar is_admin e is_superuser
        if self.instance and not self.instance.is_superuser:
            if "is_admin" in self.fields:
                del self.fields["is_admin"]
            if "is_superuser" in self.fields:
                del self.fields["is_superuser"]
            if "groups" in self.fields:
                del self.fields["groups"]
            if "user_permissions" in self.fields:
                del self.fields["user_permissions"]


class PasswordChangeForm(AuthPasswordChangeForm):
    """
    Formulário de mudança de senha personalizado.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].widget = PasswordInput(
            attrs={"class": "form-input", "placeholder": "Senha Antiga"}
        )
        self.fields["new_password1"].widget = PasswordInput(
            attrs={"class": "form-input", "placeholder": "Nova Senha"}
        )
        self.fields["new_password2"].widget = PasswordInput(
            attrs={"class": "form-input", "placeholder": "Confirme a Nova Senha"}
        )

    def clean_new_password2(self):
        new_password1 = self.cleaned_data.get("new_password1")
        new_password2 = self.cleaned_data.get("new_password2")
        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError("As senhas não coincidem.")
        return new_password2


class ForcePasswordChangeForm(forms.Form):
    """
    Formulário para forçar a mudança de senha no primeiro login.
    """

    new_password1 = forms.CharField(
        label="Nova Senha",
        widget=forms.PasswordInput(
            attrs={"class": "form-input", "placeholder": "Nova Senha"}
        ),
        strip=False,
        help_text="Sua senha não pode ser muito parecida com suas outras informações pessoais.<br>Sua senha deve conter pelo menos 8 caracteres.<br>Sua senha não pode ser uma senha comumente usada.<br>Sua senha não pode ser totalmente numérica.",
    )
    new_password2 = forms.CharField(
        label="Confirme a Nova Senha",
        widget=forms.PasswordInput(
            attrs={"class": "form-input", "placeholder": "Confirme a Nova Senha"}
        ),
        strip=False,
    )

    def clean_new_password2(self):
        new_password1 = self.cleaned_data.get("new_password1")
        new_password2 = self.cleaned_data.get("new_password2")
        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError("As senhas não coincidem.")
        return new_password2

    def save(self, user):
        user.set_password(self.cleaned_data["new_password1"])
        user.must_change_password = False
        user.save()
        return user


class UserPermissionChangeForm(forms.ModelForm):
    """
    Formulário para gestores/admins alterarem o nível de permissão e status de outros usuários.
    Inclui is_active, is_admin, is_superuser e must_change_password.
    """

    class Meta:
        model = User
        fields = (
            "permissoes",
            "is_active",
            "is_admin",
            "is_superuser",
            "must_change_password",
        )

    def __init__(self, *args, **kwargs):
        current_user = kwargs.pop(
            "current_user", None
        )  # O usuário que está fazendo a edição
        super().__init__(*args, **kwargs)

        # Se o usuário a ser editado é um superusuário
        if self.instance and self.instance.is_superuser:
            # Apenas um superusuário pode editar outro superusuário
            if current_user and not current_user.is_superuser:
                for field_name in self.fields:
                    self.fields[field_name].widget.attrs["disabled"] = "disabled"
                    self.fields[field_name].help_text = (
                        "Permissões de superusuários só podem ser alteradas por outro superusuário."
                    )
            # Se o superusuário está editando a si mesmo, ou outro superusuário
            # Apenas 'is_active' e 'must_change_password' podem ser editados por este formulário
            # 'is_superuser' e 'is_admin' são controlados pelo sistema ou por outros meios
            if self.instance == current_user or (
                self.instance.is_superuser
                and current_user
                and current_user.is_superuser
            ):
                self.fields["is_superuser"].widget.attrs["disabled"] = "disabled"
                self.fields["is_admin"].widget.attrs["disabled"] = "disabled"
                self.fields["permissoes"].widget.attrs["disabled"] = "disabled"
                self.fields["is_superuser"].help_text = (
                    "Este campo não pode ser alterado diretamente por este formulário."
                )
                self.fields["is_admin"].help_text = (
                    "Este campo não pode ser alterado diretamente por este formulário."
                )
                self.fields["permissoes"].help_text = (
                    "Este campo não pode ser alterado diretamente para superusuários."
                )

        # Se o usuário a ser editado NÃO é um superusuário
        else:
            # Um gestor não pode alterar o status de admin ou superusuário
            if (
                current_user
                and current_user.has_permission_level("gestor")
                and not current_user.is_superuser
            ):
                if "is_admin" in self.fields:
                    self.fields["is_admin"].widget.attrs["disabled"] = "disabled"
                    self.fields["is_admin"].help_text = (
                        "Você não tem permissão para alterar o status de administrador."
                    )
                if "is_superuser" in self.fields:
                    self.fields["is_superuser"].widget.attrs["disabled"] = "disabled"
                    self.fields["is_superuser"].help_text = (
                        "Você não tem permissão para alterar o status de superusuário."
                    )

            # Um usuário não pode alterar suas próprias permissões ou status
            if self.instance == current_user:
                for field_name in self.fields:
                    self.fields[field_name].widget.attrs["disabled"] = "disabled"
                    self.fields[field_name].help_text = (
                        "Você não pode alterar suas próprias permissões ou status por esta tela."
                    )
