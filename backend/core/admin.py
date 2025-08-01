# core/admin.py
from django.contrib import admin
# Remova: from .models import Profile  # Certifique-se de importar o modelo Profile
from django.utils.translation import gettext_lazy as _ # Importar para nomes de filtros

# ======================\
# FILTROS PERSONALIZADOS\
# ======================\

# Remova as classes de filtro se elas só forem usadas para Profile
# class PostoGraduacaoFilter(admin.SimpleListFilter):
#     title = _('Posto/Graduação')
#     parameter_name = 'posto_grad'
#     def lookups(self, request, model_admin):
#         return Profile.posto_grad_choices
#     def queryset(self, request, queryset):
#         if self.value():
#             return queryset.filter(posto_grad=self.value())
#         return queryset

# class TipoPerfilFilter(admin.SimpleListFilter):
#     title = _('Tipo de Perfil')
#     parameter_name = 'tipo'
#     def lookups(self, request, model_admin):
#         return Profile.tipo_choices
#     def queryset(self, request, queryset):
#         if self.value():
#             return queryset.filter(tipo=self.value())
#         return queryset


# ======================\
# ADMIN PARA PROFILE    \
# ======================\

# Remova toda a classe ProfileAdmin
# class ProfileAdmin(admin.ModelAdmin):
#     list_display = ('user', 'get_posto_grad_display', 'display_cpf', 'get_tipo_display')
#     search_fields = ('user__email', 'user__first_name', 'user__last_name', 'cpf')
#     list_filter = (PostoGraduacaoFilter, TipoPerfilFilter)
#     def get_posto_grad_display(self, obj):
#         return obj.get_posto_grad_display()
#     get_posto_grad_display.short_description = 'Posto/Grad'
#     def get_tipo_display(self, obj):
#         return obj.get_tipo_display()
#     get_tipo_display.short_description = 'Tipo de Perfil'
#     def display_cpf(self, obj):
#         return obj.cpf
#     display_cpf.short_description = 'CPF'

# Remova o registro do ProfileAdmin
# admin.site.register(Profile, ProfileAdmin)
