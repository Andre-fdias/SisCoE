from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from .models import Message, Attachment
from django.db.models import Q


@shared_task
def delete_old_messages():
    """
    Marca mensagens de chat com mais de 2 dias como excluídas (soft delete).
    Esta tarefa é projetada para ser executada diariamente.
    Retorna relatório detalhado da execução.
    """
    cutoff_date = timezone.now() - timedelta(days=2)
    # Seleciona apenas mensagens não excluídas que são mais antigas que a data de corte
    old_messages = Message.objects.filter(
        created_at__lt=cutoff_date, deleted_at__isnull=True
    )
    count = old_messages.count()

    execution_time = timezone.now()
    report_lines = [
        "=== RELATÓRIO DE LIMPEZA AUTOMÁTICA (SOFT DELETE) ===",
        f"Data/Hora: {execution_time}",
        f"Data de corte: {cutoff_date}",
        f"Total de mensagens antigas para marcar como excluídas: {count}",
    ]

    if count > 0:
        # Agrupa por conversa para o relatório
        from django.db.models import Count

        by_conversation = old_messages.values(
            "conversation__id", "conversation__name"
        ).annotate(message_count=Count("id"))

        report_lines.append("\nDistribuição por conversa:")
        for conv in by_conversation:
            conv_name = (
                conv["conversation__name"] or f"Conversa {conv['conversation__id']}"
            )
            report_lines.append(f"  - {conv_name}: {conv['message_count']} mensagens")

        # Executa o soft delete em massa
        old_messages.update(deleted_at=timezone.now())
        report_lines.append(
            f"\n✅ {count} mensagens marcadas como excluídas com sucesso!"
        )

        # Log detalhado
        print("\n".join(report_lines))

        # Opcional: Envia email de relatório para admins
        if hasattr(settings, "ADMINS") and settings.ADMINS:
            try:
                send_mail(
                    subject=f"[SisCoE] Relatório de Limpeza de Mensagens - {execution_time.date()}",
                    message="\n".join(report_lines),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[admin[1] for admin in settings.ADMINS],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Erro ao enviar email de relatório: {e}")

        return f"Marcadas {count} mensagens antigas como excluídas."
    else:
        report_lines.append("\n✅ Nenhuma mensagem antiga para marcar como excluída.")
        print("\n".join(report_lines))
        return "Nenhuma mensagem antiga para excluir"


@shared_task
def cleanup_old_attachments():
    """
    Limpa anexos órfãos ou de mensagens excluídas há mais de 30 dias.
    Execução semanal recomendada.
    """
    thirty_days_ago = timezone.now() - timedelta(days=30)

    # Condição 1: Anexos de mensagens que foram soft-deleted há mais de 30 dias.
    # Condição 2: Anexos que não têm nenhuma mensagem associada (órfãos).
    attachments_to_delete = Attachment.objects.filter(
        Q(message__deleted_at__lt=thirty_days_ago) | Q(message__isnull=True)
    )

    count = attachments_to_delete.count()

    if count > 0:
        # Para evitar problemas de performance em deleções massivas e callbacks,
        # é mais seguro iterar em blocos.
        for attachment in attachments_to_delete.iterator():
            attachment.file.delete(save=False)  # Apaga o arquivo do storage
            attachment.delete()  # Apaga o registro do banco

        return f"Excluídos {count} anexos órfãos ou de mensagens antigas."

    return "Nenhum anexo para limpar."
