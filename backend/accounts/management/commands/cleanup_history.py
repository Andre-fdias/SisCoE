# backend/accounts/management/commands/cleanup_history.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from backend.accounts.models import User, UserActionLog
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Exclui registros de histórico de ações e acessos com mais de 6 meses.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando a limpeza de registros de histórico...'))

        # Define o período de retenção (6 meses)
        six_months_ago = timezone.now() - timedelta(days=180)

        # 1. Limpeza do UserActionLog
        try:
            action_logs_to_delete = UserActionLog.objects.filter(timestamp__lt=six_months_ago)
            count_action_logs = action_logs_to_delete.count()
            if count_action_logs > 0:
                action_logs_to_delete.delete()
                self.stdout.write(self.style.SUCCESS(f'{count_action_logs} registros de UserActionLog foram excluídos.'))
            else:
                self.stdout.write(self.style.NOTICE('Nenhum registro de UserActionLog para excluir.'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Erro ao limpar UserActionLog: {e}'))
            logger.error(f'Erro ao limpar UserActionLog: {e}', exc_info=True)


        # 2. Limpeza do login_history (JSONField) no modelo User
        try:
            users_with_history = User.objects.filter(login_history__isnull=False)
            total_users_processed = 0
            total_entries_removed = 0

            for user in users_with_history:
                original_history_count = len(user.login_history)
                
                # Filtra o histórico para manter apenas as entradas dos últimos 6 meses
                updated_history = [
                    entry for entry in user.login_history 
                    if 'login_time' in entry and timezone.datetime.fromisoformat(entry['login_time']) >= six_months_ago
                ]

                if len(updated_history) < original_history_count:
                    user.login_history = updated_history
                    user.save(update_fields=['login_history'])
                    total_users_processed += 1
                    total_entries_removed += original_history_count - len(updated_history)
            
            if total_users_processed > 0:
                self.stdout.write(self.style.SUCCESS(f'{total_entries_removed} entradas de login_history foram removidas de {total_users_processed} usuários.'))
            else:
                self.stdout.write(self.style.NOTICE('Nenhum registro de login_history para excluir.'))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Erro ao limpar login_history: {e}'))
            logger.error(f'Erro ao limpar login_history: {e}', exc_info=True)

        self.stdout.write(self.style.SUCCESS('Limpeza de histórico concluída com sucesso!'))
