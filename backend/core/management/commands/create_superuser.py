from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Cria um superusuário se não existir"

    def handle(self, *args, **options):
        User = get_user_model()

        # Verifica se já existe algum superusuário
        if not User.objects.filter(is_superuser=True).exists():
            try:
                # Cria superusuário usando email como identificador
                User.objects.create_superuser(
                    email="admin@siscoe.com",
                    password="bombeiros",
                    first_name="Administrador",
                    last_name="Sistema",
                )
                self.stdout.write(
                    self.style.SUCCESS("Superusuário criado com sucesso!")
                )
                self.stdout.write(
                    self.style.WARNING("Email: admin@siscoe.com | Senha: bombeiros")
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erro ao criar superusuário: {e}"))
        else:
            self.stdout.write(self.style.WARNING("Superusuário já existe no sistema."))
