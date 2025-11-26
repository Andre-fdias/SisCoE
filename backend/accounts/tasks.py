# backend/accounts/tasks.py

from celery import shared_task
from backend.accounts.services import cleanup_history_data
import logging

logger = logging.getLogger(__name__)

@shared_task(name="cleanup_old_history_logs")
def cleanup_old_history_logs():
    """
    Tarefa Celery para limpar registros de histórico de ações e acessos com mais de 6 meses.
    """
    logger.info("Executando a tarefa agendada: cleanup_old_history_logs")
    try:
        cleanup_history_data()
        logger.info("Tarefa cleanup_old_history_logs concluída com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao executar a tarefa cleanup_old_history_logs: {e}", exc_info=True)
