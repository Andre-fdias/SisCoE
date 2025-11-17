from django.core.management.base import BaseCommand
from backend.core.models import Profile
from backend.efetivo.models import Cadastro


class Command(BaseCommand):
    help = "Vincula perfis aos cadastros correspondentes pelo CPF"

    def handle(self, *args, **options):
        for profile in Profile.objects.filter(cadastro__isnull=True):
            if profile.cpf:
                try:
                    cadastro = Cadastro.objects.get(cpf=profile.cpf)
                    profile.cadastro = cadastro
                    profile.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Vinculado perfil {profile.id} ao cadastro {cadastro.id}"
                        )
                    )
                except Cadastro.DoesNotExist:
                    # Cria novo cadastro se não existir
                    cadastro = Cadastro.objects.create(cpf=profile.cpf)
                    profile.cadastro = cadastro
                    profile.save()
                    self.stdout.write(
                        self.style.WARNING(
                            f"Criado cadastro {cadastro.id} para perfil {profile.id}"
                        )
                    )
                except Cadastro.MultipleObjectsReturned:
                    cadastro = Cadastro.objects.filter(cpf=profile.cpf).first()
                    profile.cadastro = cadastro
                    profile.save()
                    self.stdout.write(
                        self.style.WARNING(
                            f"Vinculado perfil {profile.id} ao primeiro cadastro encontrado: {cadastro.id}"
                        )
                    )
