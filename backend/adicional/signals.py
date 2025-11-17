# adicional/signals.py
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils import timezone
from .models import Cadastro_adicional
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

# Variável global para controle de signals.
# É crucial que isso seja um controle simples.
_disable_signals_status = False


@contextmanager
def disable_signals():
    """
    Context manager para desabilitar temporariamente os signals.
    Uso:
    with disable_signals():
        obj.save() # Signals não serão disparados para este save
    """
    global _disable_signals_status
    original_status = _disable_signals_status
    _disable_signals_status = True
    try:
        yield
    finally:
        _disable_signals_status = original_status  # Restaura o status original


@receiver(post_save, sender=Cadastro_adicional)
def check_adicional_status(sender, instance, created, **kwargs):
    """
    Verifica e atualiza o status do adicional baseado na data de vencimento.
    Este signal deve ser mais simples e focado apenas na atualização do status
    de 'aguardando_requisitos' para 'vencido_pendente' (ou 'faz_jus').
    """
    if _disable_signals_status:
        return

    # Esta signal só deve agir em UPDATES, não em CREATES
    if created:
        return

    # Evita loop de save infinito
    if hasattr(instance, "_checking_status_signal_active"):
        return
    instance._checking_status_signal_active = True

    try:
        hoje = timezone.now().date()

        # Se o adicional está Aguardando Requisitos e a data do próximo adicional chegou ou passou
        if (
            instance.status_adicional
            == Cadastro_adicional.StatusAdicional.AGUARDANDO_REQUISITOS
            and instance.proximo_adicional
            and hoje >= instance.proximo_adicional
        ):

            # Somente atualiza se o status for realmente diferente do que será salvo.
            # Isso evita saves desnecessários e potencial loop.
            if (
                instance.status_adicional != Cadastro_adicional.StatusAdicional.FAZ_JUS
            ):  # Assumindo que VENCIDO_PENDENTE significa FAZ_JUS
                instance.status_adicional = Cadastro_adicional.StatusAdicional.FAZ_JUS
                # Salva apenas o campo modificado para evitar disparar todos os signals novamente
                with disable_signals():  # Use o gerenciador de contexto para evitar recursão
                    instance.save(
                        update_fields=["status_adicional", "updated_at", "user_updated"]
                    )
                logger.info(
                    f"Status do Adicional ID {instance.id} atualizado para 'Faz Jus' devido à data."
                )

    except Exception as e:
        logger.error(
            f"Erro ao verificar status para Adicional ID {instance.id}: {e}",
            exc_info=True,
        )
    finally:
        if hasattr(instance, "_checking_status_signal_active"):
            del instance._checking_status_signal_active
