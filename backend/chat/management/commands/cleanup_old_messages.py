from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Executa limpeza manual de mensagens antigas (mais de 2 dias)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostra quantas mensagens seriam excluídas sem executar',
        )
        
        parser.add_argument(
            '--days',
            type=int,
            default=2,
            help='Número de dias para considerar como "antigo" (padrão: 2)',
        )
    
    def handle(self, *args, **options):
        # Import aqui para evitar circular imports
        from backend.chat.models import Message
        
        dry_run = options['dry_run']
        days = options['days']
        
        cutoff_date = timezone.now() - timedelta(days=days)
        old_messages = Message.objects.filter(created_at__lt=cutoff_date)
        count = old_messages.count()
        
        self.stdout.write(f'=== LIMPEZA DE MENSAGENS ANTIGAS ===')
        self.stdout.write(f'Data de corte: {cutoff_date}')
        self.stdout.write(f'Mensagens com mais de {days} dias: {count}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('✅ MODO SIMULAÇÃO - Nenhuma mensagem foi excluída')
            )
            
            # Mostra algumas mensagens que seriam excluídas
            if count > 0:
                sample_messages = old_messages.select_related('sender', 'conversation')[:5]
                self.stdout.write('\nAmostra de mensagens que seriam excluídas:')
                for msg in sample_messages:
                    preview = msg.decrypted_text[:50] + "..." if msg.decrypted_text and len(msg.decrypted_text) > 50 else (msg.decrypted_text or "[Sem texto]")
                    self.stdout.write(f'  - {msg.id}: {msg.created_at} - "{preview}"')
                
                if count > 5:
                    self.stdout.write(f'  ... e mais {count - 5} mensagens')
        else:
            if count > 0:
                # Exclui as mensagens
                deleted_count = old_messages.count()
                old_messages.delete()
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {deleted_count} mensagens excluídas com sucesso!')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('✅ Nenhuma mensagem antiga para excluir')
                )