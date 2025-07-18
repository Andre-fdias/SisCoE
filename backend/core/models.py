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
        null=True,
        blank=True
    )
    re = models.CharField(max_length=6, blank=True, null=True)
    dig = models.CharField(max_length=1, blank=True, null=True)
    posto_grad = models.CharField(max_length=100, choices=posto_grad_choices, blank=True, null=True)
    cpf = models.CharField(max_length=14, blank=True, null=True, unique=True)
    tipo = models.CharField(max_length=15, choices=tipo_choices, blank=True, null=True)

    class Meta:
        ordering = ('user__first_name',)
        verbose_name = 'perfil'
        verbose_name_plural = 'perfis'

    def __str__(self):
        return f'{self.user.get_full_name()} - {self.re}-{self.dig}'

    @property
    def full_name(self):
        return f'{self.user.first_name} {self.user.last_name}'.strip()
    
    @property
    def image(self):
        """Retorna a imagem do cadastro associado ou None"""
        if self.cadastro and hasattr(self.cadastro, 'imagens'):
            imagem = self.cadastro.imagens.filter(is_profile=True).first()
            return imagem.image if imagem else None
        return None

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


    def sync_with_cadastro(self):
        """Sincroniza os dados com o cadastro do efetivo"""
        if self.cadastro:
            self.re = self.cadastro.re
            self.dig = self.cadastro.dig
            self.cpf = self.cadastro.cpf
            
            # Sincroniza o posto/grad com a última promoção
            ultima_promocao = self.cadastro.promocoes.order_by('-ultima_promocao').first()
            if ultima_promocao:
                self.posto_grad = ultima_promocao.posto_grad
            
            # Sincroniza o tipo (administrativo/operacional) com os detalhes de situação
            detalhes_situacao = self.cadastro.detalhes_situacao.order_by('-data_alteracao').first()
            if detalhes_situacao and detalhes_situacao.op_adm:
                self.tipo = detalhes_situacao.op_adm.lower()

    def save(self, *args, **kwargs):
        # Se não tem cadastro associado mas tem CPF, tenta vincular
        if not self.cadastro and self.cpf:
            try:
                cadastro = Cadastro.objects.get(cpf=self.cpf)
                self.cadastro = cadastro
            except Cadastro.DoesNotExist:
                pass
        
        # Se tem cadastro, sincroniza os dados
        if self.cadastro:
            self.sync_with_cadastro()
        
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.cadastro and self.cpf != self.cadastro.cpf:
            raise ValidationError("O CPF do perfil deve ser igual ao CPF do cadastro associado.")

# core/models.py
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        try:
            # Tenta encontrar um cadastro pelo email (se o email do usuário for igual ao do cadastro)
            cadastro = Cadastro.objects.filter(email=instance.email).first()
            
            # Se não encontrar pelo email, tenta pelo nome (pode ser menos preciso)
            if not cadastro:
                # Remove sufixos comuns de email para tentar casar com o nome
                email_prefix = instance.email.split('@')[0]
                cadastro = Cadastro.objects.filter(
                    models.Q(nome__icontains=email_prefix) | 
                    models.Q(nome_de_guerra__icontains=email_prefix)
                ).first()
            
            # Cria o perfil com ou sem cadastro associado
            profile = Profile.objects.create(user=instance, cadastro=cadastro)
            
            # Se encontrou um cadastro, sincroniza os dados
            if cadastro:
                profile.sync_with_cadastro()
                profile.save()
                
                # Atualiza também o nome do usuário
                instance.first_name = cadastro.nome_de_guerra
                instance.save()
                
        except Exception as e:
            print(f"Erro ao criar perfil: {e}")

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        if hasattr(instance, 'profile'):
            instance.profile.save()
    except Exception as e:
        print(f"Erro ao salvar perfil para o usuário {instance.email}: {e}")