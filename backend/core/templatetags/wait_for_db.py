# backend/core/management/commands/wait_for_db.py
import time
from django.db import connections
from django.db.utils import OperationalError
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    """Django command to pause execution until database is available"""

    def handle(self, *args, **options):
        self.stdout.write('🔄 Aguardando banco de dados...')
        db_conn = None
        while not db_conn:
            try:
                db_conn = connections['default']
                db_conn.cursor()
                self.stdout.write(self.style.SUCCESS('✅ Banco de dados disponível!'))
            except OperationalError:
                self.stdout.write('⏳ Banco de dados indisponível, aguardando 1 segundo...')
                time.sleep(1)