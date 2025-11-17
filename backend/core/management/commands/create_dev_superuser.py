from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    """
    Cria um superusuário para o ambiente de desenvolvimento se ele não existir.
    """

    help = "Cria um superusuário padrão para desenvolvimento."

    def handle(self, *args, **options):
        User = get_user_model()
        email = "admin@siscoe.com"
        password = "bombeiros"

        if not User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.SUCCESS(
                    f"Criando superusuário de desenvolvimento com email {email}..."
                )
            )
            User.objects.create_superuser(
                username=email, email=email, password=password
            )
            self.stdout.write(self.style.SUCCESS("Superusuário criado com sucesso!"))
        else:
            self.stdout.write(
                self.style.WARNING(f"Superusuário com email {email} já existe.")
            )
