# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserActionLog, SearchableUserActionLog, SearchableUser, Profile
from .forms import CustomUserCreationForm, CustomUserChangeForm

# Define o inline para o Profile
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    inlines = (ProfileInline,)

    list_display = ('email', 'first_name', 'last_name', 'is_admin', 'is_active', 'permissoes', 'cadastro_link')
    list_filter = ('is_admin', 'is_active', 'permissoes')
    search_fields = ('email', 'first_name', 'last_name', 'cadastro__cpf', 'cadastro__nome_de_guerra')
    ordering = ('email',)
    filter_horizontal = ()

    readonly_fields = ('last_login', 'date_joined') # Adicionado para corrigir o erro

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informações Pessoais', {'fields': ('first_name', 'last_name', 'cadastro')}), # Adiciona 'cadastro'
        ('Permissões', {'fields': ('is_admin', 'is_active', 'is_superuser', 'groups', 'user_permissions', 'permissoes')}),
        ('Datas Importantes', {'fields': ('last_login', 'date_joined')}),
        ('Histórico de Login', {'fields': ('last_login_ip', 'last_login_computer_name', 'login_history', 'is_online')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password', 'password2', 'permissoes', 'cadastro'), # Adiciona 'cadastro'
        }),
    )

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(UserAdmin, self).get_inline_instances(request, obj)

    def cadastro_link(self, obj):
        if obj.cadastro:
            from django.utils.html import format_html
            from django.urls import reverse
            link = reverse("admin:efetivo_cadastro_change", args=[obj.cadastro.pk])
            return format_html('<a href="{}">{} ({})</a>', link, obj.cadastro.nome_de_guerra, obj.cadastro.cpf)
        return "-"
    cadastro_link.short_description = "Cadastro Militar"


@admin.register(UserActionLog)
class UserActionLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp', 'ip_address', 'computer_name')
    list_filter = ('action', 'timestamp', 'user')
    search_fields = ('user__email', 'action', 'ip_address', 'computer_name')
    date_hierarchy = 'timestamp' # Adiciona uma hierarquia de data para navegação
    readonly_fields = ('user', 'action', 'timestamp', 'ip_address', 'computer_name') # Torna os campos somente leitura

@admin.register(SearchableUserActionLog)
class SearchableUserActionLogAdmin(UserActionLogAdmin):
    # Este é um proxy model, então ele herda as configurações do UserActionLogAdmin
    pass

@admin.register(SearchableUser)
class SearchableUserAdmin(UserAdmin):
    # Este é um proxy model, então ele herda as configurações do UserAdmin
    pass
