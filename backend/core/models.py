# backend/core/models.py
# Remova: from backend.accounts.models import User # Não é mais necessário importar User diretamente
# Remova: from backend.efetivo.models import Cadastro # REMOVA ESTA LINHA PARA EVITAR IMPORTAÇÃO CIRCULAR
import logging

logger = logging.getLogger(__name__)

# REMOVA TODO O BLOCO DO MODELO Profile E SEUS MÉTODOS
# class Profile(models.Model):
#     posto_grad_choices = (...
#     tipo_choices = (...
#     user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     cadastro = models.OneToOneField('efetivo.Cadastro', on_delete=models.SET_NULL, null=True, blank=True, related_name='profile_rel')
#     posto_grad = models.CharField(max_length=100, choices=posto_grad_choices, blank=True, null=True)
#     tipo = models.CharField(max_length=20, choices=tipo_choices, blank=True, null=True)
#     cpf = models.CharField(max_length=14, blank=True, null=True, unique=True)
#     create_at = models.DateTimeField(auto_now_add=True)
#     update_at = models.DateTimeField(auto_now=True)
#     class Meta:
#         verbose_name = "Perfil"
#         verbose_name_plural = "Perfis"
#     def __str__(self):
#         return f'Perfil de {self.user.email}'
#     @property
#     def get_posto_grad_display(self):
#         return self.get_posto_grad_display()
#     @property
#     def get_tipo_display(self):
#         return self.get_tipo_display()
#     @property
#     def display_cpf(self):
#         return self.cpf
#     def sync_with_cadastro(self):
#         if self.cadastro:
#             self.posto_grad = self.cadastro.ultima_promocao.posto_grad if self.cadastro.ultima_promocao else ""
#             self.tipo = self.cadastro.detalhes_situacao.first().op_adm if self.cadastro.detalhes_situacao.first() else ""
#             self.cpf = self.cadastro.cpf
#             self.save(update_fields=['posto_grad', 'tipo', 'cpf'])
#             logger.info(f"Profile de {self.user.email} sincronizado com Cadastro {self.cadastro.re}.")
#         else:
#             logger.warning(f"Tentativa de sincronizar Profile de {self.user.email} sem Cadastro associado.")

# REMOVA TODO O BLOCO DO RECEIVER create_or_update_user_profile
# @receiver(post_save, sender=settings.AUTH_USER_MODEL)
# def create_or_update_user_profile(sender, instance, created, **kwargs):
#     try:
#         if created:
#             profile = Profile.objects.create(user=instance)
#             print(f"DEBUG: Profile criado para novo usuário {instance.email}.")
#         else:
#             profile, created = Profile.objects.get_or_create(user=instance)
#             if created:
#                 print(f"DEBUG: Profile criado (get_or_create) para usuário existente {instance.email}.")
#         from backend.efetivo.models import Cadastro
#         if not profile.cadastro and instance.email:
#             cadastro = Cadastro.objects.filter(email=instance.email).first()
#             if cadastro:
#                 profile.cadastro = cadastro
#                 profile.save(update_fields=['cadastro'])
#                 print(f"DEBUG: Profile de {instance.email} associado ao Cadastro {cadastro.re}.")
#                 profile.sync_with_cadastro()
#             else:
#                 print(f"DEBUG: Nenhum Cadastro encontrado para associar a {instance.email}.")
#         elif profile.cadastro:
#             profile.sync_with_cadastro()
#             print(f"DEBUG: Profile de {instance.email} sincronizado com Cadastro existente {profile.cadastro.re}.")
#     except Exception as e:
#         print(f"ERRO: No signal create_or_update_user_profile para {instance.email}: {e}")
#         logger.error(f"Erro ao criar ou atualizar perfil para o usuário {instance.email}: {e}", exc_info=True)

# REMOVA TODO O BLOCO DO MODELO SearchableProfile
# class SearchableProfile(Profile):
#     class Meta:
#         proxy = True
#         verbose_name = "Perfil Pesquisável"
#         verbose_name_plural = "Perfis Pesquisáveis"
#     def get_search_result(self):
#         return {
#             'title': self.user.get_full_name() or self.user.email,
#             'fields': {
#                 'Usuário': self.user.email,
#                 'Posto/Grad': self.get_posto_grad_display() if self.posto_grad else 'N/A',
#                 'Tipo': self.get_tipo_display() if self.tipo else 'N/A',
#                 'CPF': self.cpf or 'N/A',
#             }
#         }
