# backend/accounts/management/commands/cleanup_history.py

from django.core.management.base import BaseCommand
from backend.accounts.services import cleanup_history_data
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Exclui registros de histórico de ações e acessos com mais de 6 meses.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando a limpeza de registros de histórico através do management command...'))
        
        try:
            cleanup_history_data()
            self.stdout.write(self.style.SUCCESS('Limpeza de histórico concluída com sucesso!'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Ocorreu um erro durante a limpeza do histórico: {e}'))
            logger.error(f'Erro ao executar o comando cleanup_history: {e}', exc_info=True)