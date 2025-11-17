import logging
from django.template.loader import render_to_string
from django.db.models import Q
from backend.accounts.models import User
from backend.accounts.brevo_service import send_brevo_email, test_brevo_connection

logger = logging.getLogger(__name__)


def verificar_configuracao_email():
    """
    Verifica se o serviço de email está configurado corretamente
    """
    logger.info("🔍 Verificando configuração de email...")

    # Testa a conexão com Brevo
    conexao_ok = test_brevo_connection()

    if not conexao_ok:
        logger.error("❌ Configuração de email com problemas")
        logger.error("💡 Verifique:")
        logger.error("   1. BREVO_API_KEY nas settings")
        logger.error("   2. IP autorizado no Brevo")
        logger.error("   3. Conexão com internet")
        return False

    logger.info("✅ Configuração de email: OK")
    return True


def enviar_email_atualizacao_consolidada(chamado, changes_data):
    """
    Envia email consolidado com todas as atualizações do chamado (Admin → Usuário)
    """
    # Verifica configuração antes de tentar enviar
    if not verificar_configuracao_email():
        logger.warning("⚠️ Serviço de email não configurado, pulando envio")
        return False

    try:
        subject = f"🔄 Atualização do Chamado {chamado.protocolo} - SisCoE"

        context = {
            "chamado": chamado,
            "status_changed": changes_data.get("status_changed", False),
            "tecnico_changed": changes_data.get("tecnico_changed", False),
            "old_status_display": changes_data.get("old_status_display", ""),
            "new_status_display": changes_data.get("new_status_display", ""),
            "novo_tecnico": changes_data.get("novo_tecnico", ""),
            "novo_comentario": changes_data.get("novo_comentario"),
        }

        html_content = render_to_string(
            "tickets/email/atualizacao_consolidada.html", context
        )

        result = send_brevo_email(
            subject=subject,
            html_content=html_content,
            to_email=chamado.solicitante_email,
            from_name="SisCoE - Sistema de Chamados",
        )

        if result:
            logger.info(
                f"✅ Email de atualização consolidada enviado para {chamado.solicitante_email}"
            )
        else:
            logger.error(
                f"❌ Falha ao enviar email de atualização consolidada para {chamado.solicitante_email}"
            )

        return result

    except Exception as e:
        logger.error(
            f"❌ Erro ao enviar email de atualização consolidada: {str(e)}",
            exc_info=True,
        )
        return False


def enviar_email_comentario_usuario(chamado, comentario):
    """
    Envia email quando um usuário adiciona um comentário ao chamado (Usuário → Admin)
    """
    if not verificar_configuracao_email():
        logger.warning("⚠️ Serviço de email não configurado, pulando envio")
        return False

    try:
        # Busca todos os técnicos/admin para notificar
        tecnicos = User.objects.filter(Q(is_admin=True) | Q(is_superuser=True))
        emails_tecnicos = [tecnico.email for tecnico in tecnicos if tecnico.email]

        if not emails_tecnicos:
            logger.warning("Nenhum técnico encontrado para notificação")
            return False

        subject = f"💬 Resposta do Usuário - Chamado {chamado.protocolo}"

        html_content = render_to_string(
            "tickets/email/resposta_usuario.html",
            {
                "chamado": chamado,
                "comentario": comentario,
                "comentarios": chamado.comentarios.all().order_by("criado_em"),
            },
        )

        # Envia para todos os técnicos
        success_count = 0
        for email_tecnico in emails_tecnicos:
            result = send_brevo_email(
                subject=subject,
                html_content=html_content,
                to_email=email_tecnico,
                from_name="SisCoE - Sistema de Chamados",
            )

            if result:
                logger.info(
                    f"✅ Email de resposta do usuário enviado para {email_tecnico}"
                )
                success_count += 1
            else:
                logger.error(
                    f"❌ Falha ao enviar email de resposta do usuário para {email_tecnico}"
                )

        return success_count > 0

    except Exception as e:
        logger.error(
            f"❌ Erro ao enviar email de resposta do usuário: {str(e)}", exc_info=True
        )
        return False


def enviar_email_chamado_aberto(chamado):
    """
    Envia email quando um chamado é aberto com histórico
    """
    if not verificar_configuracao_email():
        logger.warning("⚠️ Serviço de email não configurado, pulando envio")
        return False

    try:
        # Busca comentários públicos do chamado
        comentarios = chamado.comentarios.filter(privado=False).order_by("criado_em")

        subject = f"🎫 Chamado Aberto - Protocolo: {chamado.protocolo}"

        html_content = render_to_string(
            "tickets/email/novo_chamado.html",
            {
                "chamado": chamado,
                "comentarios": comentarios,
            },
        )

        result = send_brevo_email(
            subject=subject,
            html_content=html_content,
            to_email=chamado.solicitante_email,
            from_name="SisCoE - Sistema de Chamados",
        )

        if result:
            logger.info(
                f"✅ Email de abertura enviado para {chamado.solicitante_email}"
            )
        else:
            logger.error(
                f"❌ Falha ao enviar email de abertura para {chamado.solicitante_email}"
            )

        return result

    except Exception as e:
        logger.error(f"❌ Erro ao enviar email de abertura: {str(e)}", exc_info=True)
        return False


def enviar_email_mudanca_status(chamado, old_status, new_status, comentario=None):
    """
    Envia email quando o status do chamado muda com histórico completo
    """
    if not verificar_configuracao_email():
        logger.warning("⚠️ Serviço de email não configurado, pulando envio")
        return False

    try:
        # Busca TODOS os comentários do chamado (para histórico completo)
        comentarios = chamado.comentarios.all().order_by("criado_em")

        subject = f"🔄 Atualização do Chamado {chamado.protocolo}"

        html_content = render_to_string(
            "tickets/email/mudanca_status.html",
            {
                "chamado": chamado,
                "old_status": old_status,
                "new_status": new_status,
                "old_status_display": chamado.get_status_display_color()
                .replace(old_status, "")
                .strip(),
                "new_status_display": chamado.get_status_display_color()
                .replace(new_status, "")
                .strip(),
                "comentario": comentario,  # Comentário específico da mudança
                "comentarios": comentarios,  # Histórico completo
            },
        )

        result = send_brevo_email(
            subject=subject,
            html_content=html_content,
            to_email=chamado.solicitante_email,
            from_name="SisCoE - Sistema de Chamados",
        )

        if result:
            logger.info(
                f"✅ Email de mudança de status enviado para {chamado.solicitante_email}"
            )
        else:
            logger.error(
                f"❌ Falha ao enviar email de status para {chamado.solicitante_email}"
            )

        return result

    except Exception as e:
        logger.error(
            f"❌ Erro ao enviar email de mudança de status: {str(e)}", exc_info=True
        )
        return False


def enviar_email_comentario_adicionado(chamado, comentario):
    """
    Envia email quando um comentário é adicionado ao chamado
    """
    if not verificar_configuracao_email():
        logger.warning("⚠️ Serviço de email não configurado, pulando envio")
        return False

    try:
        # Busca histórico completo de comentários
        comentarios = chamado.comentarios.all().order_by("criado_em")

        subject = f"💬 Novo Comentário - Chamado {chamado.protocolo}"

        html_content = render_to_string(
            "tickets/email/novo_comentario.html",
            {
                "chamado": chamado,
                "comentario": comentario,
                "comentarios": comentarios,
            },
        )

        result = send_brevo_email(
            subject=subject,
            html_content=html_content,
            to_email=chamado.solicitante_email,
            from_name="SisCoE - Sistema de Chamados",
        )

        if result:
            logger.info(
                f"✅ Email de comentário enviado para {chamado.solicitante_email}"
            )
        else:
            logger.error(
                f"❌ Falha ao enviar email de comentário para {chamado.solicitante_email}"
            )

        return result

    except Exception as e:
        logger.error(f"❌ Erro ao enviar email de comentário: {str(e)}", exc_info=True)
        return False
