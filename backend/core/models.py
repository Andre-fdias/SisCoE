from backend.accounts.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.safestring import mark_safe
from backend.efetivo.models import Cadastro # Importe a model Cadastro
from django.db import connection
from django.conf import settings
from django.core.exceptions import ValidationError
import logging
from django.db.models import Q # Para usar Q objects na busca por email/nome

logger = logging.getLogger(__name__)

class Profile(models.Model):
    posto_grad_choices = (
        ("", " "),
        ("Cel PM", "Cel PM"),
        ("Ten Cel PM", "Ten Cel PM"),
        ("Maj PM", "Maj PM"),
        ("CAP PM", "Cap PM"),
        ("1º Ten PM", "1º Ten PM"),
        ("1º Ten QAPM", "1º Ten QAOPM"),
        ("2º Ten PM", "2º Ten PM"),
        ("2º Ten QAPM", "2º Ten QAOPM"),
        ("Asp OF PM", "Asp OF PM"),
        ("Subten PM", "Subten PM"),
        ("1º Sgt PM", "1º Sgt PM"),
        ("2º Sgt PM", "2º Sgt PM"),
        ("3º Sgt PM", "3º Sgt PM"),
        ("Cb PM", "Cb PM"),
        ("Sd PM", "Sd PM"),
        ("Sd PM 2ºCL", "Sd PM 2ºCL"),
    )

    tipo_choices = (
        ("administrativo", "Administrativo"),
        ("operacional", "Operacional"),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    cadastro = models.ForeignKey(
        Cadastro,
        on_delete=models.SET_NULL, # Manter Profile mesmo que Cadastro seja apagado
        null=True, blank=True,
        related_name='profiles'
    )
    posto_grad = models.CharField(
        max_length=100,
        choices=posto_grad_choices,
        blank=True,
        null=True
    )
    re = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        unique=True # RE deve ser único, se usado para identificação
    )
    dig = models.CharField(
        max_length=1,
        blank=True,
        null=True
    )
    cpf = models.CharField(
        max_length=14, # Inclui pontos e traço
        blank=True,
        null=True,
        unique=True # CPF deve ser único
    )
    tipo = models.CharField(
        max_length=20,
        choices=tipo_choices,
        blank=True,
        null=True
    )
    is_profile_complete = models.BooleanField(default=False)


    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfis'

    def __str__(self):
        return f'{self.user.email}'


    def sync_with_cadastro(self):
        print(f"DEBUG: sync_with_cadastro chamado para o Profile do usuário {self.user.email}")
        if self.cadastro:
            print(f"DEBUG: Profile tem Cadastro associado. Copiando dados...")
            self.posto_grad = self.cadastro.posto_grad
            self.re = self.cadastro.re
            self.dig = self.cadastro.dig
            self.cpf = self.cadastro.cpf
            print(f"DEBUG: Dados copiados: posto_grad={self.posto_grad}, re={self.re}")
            logger.info(f"Dados do Cadastro (RE: {self.cadastro.re}, Posto: {self.cadastro.posto_grad}) sincronizados com o Profile do usuário {self.user.email}")
        else:
            print(f"DEBUG: Profile NÃO tem Cadastro associado para sincronizar.")
            logger.warning(f"Tentativa de sincronizar Profile {self.user.email} sem Cadastro associado.")


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    print(f"DEBUG: Signal post_save de User disparado para {instance.email}. Created: {created}")
    if kwargs.get('raw', False):
        print("DEBUG: Signal ignorado devido a raw=True.")
        return

    try:
        profile, profile_created = Profile.objects.get_or_create(user=instance)
        print(f"DEBUG: Profile {'criado' if profile_created else 'obtido'} para {instance.email}.")

        if created:
            cadastro = None
            if instance.email:
                cadastro = Cadastro.objects.filter(email=instance.email).first()
                print(f"DEBUG: Buscando Cadastro por email {instance.email}. Encontrado: {cadastro is not None}")

            if cadastro:
                profile.cadastro = cadastro
                print(f"DEBUG: Associando Profile ao Cadastro {cadastro.re}.")
                profile.sync_with_cadastro()
                profile.save()
                print(f"DEBUG: Profile salvo após sincronização com Cadastro.")

                if cadastro.nome_de_guerra and instance.first_name != cadastro.nome_de_guerra:
                    instance.first_name = cadastro.nome_de_guerra
                    instance.save(update_fields=['first_name'])
                    print(f"DEBUG: User first_name atualizado para {instance.first_name}.")
            else:
                print(f"DEBUG: Nenhum Cadastro encontrado para associar a {instance.email}.")
        else:
            print(f"DEBUG: User existente {instance.email}. Nenhuma ação de criação de Profile por este signal.")

    except Exception as e:
        print(f"ERRO: No signal create_or_update_user_profile para {instance.email}: {e}")
        logger.error(f"Erro ao criar ou atualizar perfil para o usuário {instance.email}: {e}", exc_info=True)