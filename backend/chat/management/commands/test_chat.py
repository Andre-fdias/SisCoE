from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Testa se os commands do chat estão funcionando'
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🎉 COMANDO DE TESTE DO CHAT FUNCIONANDO!')
        )
        self.stdout.write('O sistema de commands está configurado corretamente.')