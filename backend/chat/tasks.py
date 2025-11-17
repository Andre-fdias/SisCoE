from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from .models import Message


@shared_task
def delete_old_messages():
    """
    Exclui mensagens de chat com mais de 2 dias de idade.
    Esta tarefa é projetada para ser executada diariamente.
    Retorna relatório detalhado da execução.
    """
    cutoff_date = timezone.now() - timedelta(days=2)
    old_messages = Message.objects.filter(created_at__lt=cutoff_date)
    count = old_messages.count()

    execution_time = timezone.now()
    report_lines = [
        "=== RELATÓRIO DE LIMPEZA AUTOMÁTICA ===",
        f"Data/Hora: {execution_time}",
        f"Data de corte: {cutoff_date}",
        f"Total de mensagens antigas: {count}",
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

        # Executa a exclusão
        old_messages.delete()
        report_lines.append(f"\n✅ {count} mensagens excluídas com sucesso!")

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

        return f"Excluídas {count} mensagens antigas"
    else:
        report_lines.append("\n✅ Nenhuma mensagem antiga para excluir")
        print("\n".join(report_lines))
        return "Nenhuma mensagem antiga para excluir"


@shared_task
def cleanup_old_attachments():
    """
    Limpa anexos órfãos (sem mensagem associada).
    Execução semanal recomendada.
    """
    from .models import Attachment
    from django.utils import timezone
    from datetime import timedelta

    # Encontra anexos sem mensagem associada ou muito antigos
    orphan_attachments = Attachment.objects.filter(
        message__isnull=True
    ) | Attachment.objects.filter(uploaded_at__lt=timezone.now() - timedelta(days=7))

    count = orphan_attachments.count()

    if count > 0:
        orphan_attachments.delete()
        return f"Excluídos {count} anexos órfãos/antigos"

    return "Nenhum anexo órfão/antigo para excluir"
