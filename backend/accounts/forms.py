from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from backend.accounts.models import User
import random
import string

class CustomUserForm(forms.ModelForm):
    first_name = forms.CharField(
        label='Nome Completo',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'bg-gray-700 border border-gray-600 text-gray-200 sm:text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5',
            'readonly': 'readonly'
        })
    )
    last_name = forms.CharField(
        label='Nome de Guerra',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'bg-gray-700 border border-gray-600 text-gray-200 sm:text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5',
            'readonly': 'readonly'
        })
    )
    email = forms.EmailField(
        label='E-mail Funcional',
        widget=forms.EmailInput(attrs={
            'class': 'bg-gray-700 border border-gray-600 text-gray-200 sm:text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5',
            'readonly': 'readonly'
        })
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        # Gera uma senha aleatória
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        user.set_password(password)
        if commit:
            user.save()
        return user, password  # Retorna tanto o usuário quanto a senha