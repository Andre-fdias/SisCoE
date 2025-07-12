from backend.accounts.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.safestring import mark_safe
from backend.efetivo.models import Cadastro  # Importe a model Cadastro
from django.db import connection
from django.conf import settings
from django.core.exceptions import ValidationError

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
        verbose_name='usuário'
    )
    cadastro = models.OneToOneField(
        Cadastro,
        on_delete=models.CASCADE,
        verbose_name='cadastro',
        null=True,  # Permitir valores nulos temporariamente
        blank=True
    )
    re = models.CharField(max_length=6, blank=False, null=False, unique=True)
    dig = models.CharField(max_length=1, blank=False, null=False)
    posto_grad = models.CharField(max_length=100, choices=posto_grad_choices)
    image = models.ImageField(upload_to='img/fotos_perfil/usuario')
    cpf = models.CharField(max_length=14, blank=False, null=False, unique=True)
    tipo = models.CharField(max_length=15, choices=tipo_choices, blank=False, null=False)
    class Meta:
        ordering = ('user__first_name',)
        verbose_name = 'perfil'
        verbose_name_plural = 'perfis'

    @property
    def full_name(self):
        return f' {self.user.last_name}'.strip()

    def __str__(self):
        return self.full_name

    @property
    def grad(self):
        if self.posto_grad == 'Cel PM':
            return mark_safe('<span class="bg-blue-500 text-white px-2 py-1 rounded">Cel PM</span>')
        if self.posto_grad == 'Ten Cel PM':
            return mark_safe('<span class="bg-blue-500 text-white px-2 py-1 rounded">Ten Cel PM</span>')
        if self.posto_grad == 'Maj PM':
            return mark_safe('<span class="bg-blue-500 text-white px-2 py-1 rounded">Maj PM</span>')
        if self.posto_grad == 'CAP PM':
            return mark_safe('<span class="bg-blue-500 text-white px-2 py-1 rounded">CAP PM</span>')
        if self.posto_grad == '1º Ten PM':
            return mark_safe('<span class="bg-blue-500 text-white px-2 py-1 rounded">1º Ten PM</span>')
        if self.posto_grad == '1º Ten QAPM':
            return mark_safe('<span class="bg-blue-500 text-white px-2 py-1 rounded">1º Ten QAPM</span>')
        if self.posto_grad == '2º Ten PM':
            return mark_safe('<span class="bg-blue-500 text-white px-2 py-1 rounded">2º Ten PM</span>')
        if self.posto_grad == '2º Ten QAPM':
            return mark_safe('<span class="bg-blue-500 text-white px-2 py-1 rounded">2º Ten QAPM</span>')
        if self.posto_grad == 'Asp OF PM':
            return mark_safe('<span class="bg-blue-500 text-white px-2 py-1 rounded">Asp OF PM</span>')
        if self.posto_grad == 'Subten PM':
            return mark_safe('<span class="bg-red-500 text-white px-2 py-1 rounded">Subten PM</span>')
        if self.posto_grad == '1º Sgt PM':
            return mark_safe('<span class="bg-red-500 text-white px-2 py-1 rounded">1º Sgt PM</span>')
        if self.posto_grad == '2º Sgt PM':
            return mark_safe('<span class="bg-red-500 text-white px-2 py-1 rounded">2º Sgt PM</span>')
        if self.posto_grad == '3º Sgt PM':
            return mark_safe('<span class="bg-red-500 text-white px-2 py-1 rounded">3º Sgt PM</span>')
        if self.posto_grad == 'Cb PM':
            return mark_safe('<span class="bg-black text-white px-2 py-1 rounded">Cb PM</span>')
        if self.posto_grad == 'Sd PM':
            return mark_safe('<span class="bg-black text-white px-2 py-1 rounded">Sd PM</span>')
        if self.posto_grad == 'Sd PM 2ºCL':
            return mark_safe('<span class="bg-black text-white px-2 py-1 rounded">Sd PM 2ºCL</span>')


    def clean(self):
        super().clean()
        # Garantir que o CPF do perfil seja igual ao do cadastro
        if self.cadastro and self.cpf != self.cadastro.cpf:
            raise ValidationError("O CPF do perfil deve ser igual ao CPF do cadastro associado.")

    def save(self, *args, **kwargs):
        # Se não tem cadastro associado mas tem CPF, tenta vincular
        if not self.cadastro and self.cpf:
            try:
                cadastro = Cadastro.objects.get(cpf=self.cpf)
                self.cadastro = cadastro
            except Cadastro.DoesNotExist:
                # Cria um novo cadastro se não existir
                cadastro = Cadastro.objects.create(cpf=self.cpf)
                self.cadastro = cadastro
            except Cadastro.MultipleObjectsReturned:
                # Pega o primeiro se houver múltiplos (deveria ser único)
                cadastro = Cadastro.objects.filter(cpf=self.cpf).first()
                self.cadastro = cadastro
        
        # Sincroniza o CPF se houver cadastro associado
        if self.cadastro:
            self.cpf = self.cadastro.cpf
            
        super().save(*args, **kwargs)


# Receivers corrigidos
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        try:
            profile = Profile.objects.create(user=instance)
            
            # Tenta vincular automaticamente pelo CPF se existir
            if profile.cpf:
                try:
                    cadastro = Cadastro.objects.get(cpf=profile.cpf)
                    profile.cadastro = cadastro
                    profile.save()
                except Cadastro.DoesNotExist:
                    # Cria novo cadastro se não existir
                    cadastro = Cadastro.objects.create(cpf=profile.cpf)
                    profile.cadastro = cadastro
                    profile.save()
        except Exception as e:
            print(f"Erro ao criar perfil: {e}")


            
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        if hasattr(instance, 'profile'):
            instance.profile.save()
        else:
            # Se não existir, cria um novo perfil
            Profile.objects.create(user=instance)
    except Exception as e:
        print(f"Erro ao salvar perfil para o usuário {instance.email}: {e}")