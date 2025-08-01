# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name') # Apenas os campos do User

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adicione classes Tailwind CSS aos campos do formulário
        for field_name in self.fields:
            if field_name in ['password', 'password2']: # Campos de senha
                self.fields[field_name].widget.attrs.update({
                    'class': 'bg-gray-300 border border-gray-300 text-gray-900 sm:text-sm rounded-lg focus:ring-cyan-600 focus:border-cyan-600 block w-full p-2.5'
                })
            elif field_name in ['email', 'first_name', 'last_name']: # Outros campos
                 self.fields[field_name].widget.attrs.update({
                    'class': 'bg-gray-300 border border-gray-300 text-gray-900 sm:text-sm rounded-lg focus:ring-cyan-600 focus:border-cyan-600 block w-full p-2.5'
                })


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'is_active', 'is_admin', 'permissoes') # Ajuste os campos conforme necessário
