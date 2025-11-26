# backend/accounts/services.py

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.conf import settings
from .tokens import account_activation_token
from .models import UserActionLog
from .utils import get_client_ip, get_computer_name
from django.contrib.auth import get_user_model
import logging
from django.utils import timezone

# Importar o serviço Brevo corrigido
from .brevo_service import send_brevo_email

# Importar o modelo Cadastro
from backend.efetivo.models import Cadastro

# Importar o signal user_logged_in e o decorador receiver
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

import socket
from datetime import timedelta


logger = logging.getLogger(__name__)
User = get_user_model()


def send_email(subject, html_content, recipient_email):
    """
    Função auxiliar para enviar e-mails usando a API do Brevo.
    """
    logger.info(f"🔄 Iniciando envio de email para: {recipient_email}")

    try:
        result = send_brevo_email(
            subject=subject,
            html_content=html_content,
            to_email=recipient_email,
            from_email=settings.DEFAULT_FROM_EMAIL,
            from_name=settings.DEFAULT_FROM_NAME,
        )

        if result:
            logger.info(f"✅ Email enviado com sucesso para {recipient_email}")
        else:
            logger.error(f"❌ Falha no envio do email para {recipient_email}")

        return result

    except Exception as e:
        logger.error(f"❌ Erro inesperado em send_email: {str(e)}", exc_info=True)
        return False


def send_mail_to_user(request, user):
    """
    Envia e-mail de redefinição de senha.
    """
    current_site = get_current_site(request)
    subject = "Redefinição de senha - SisCoE"
    html_content = render_to_string(
        "email/password_reset_email.html",
        {
            "user": user,
            "protocol": "https" if request.is_secure() else "http",
            "domain": current_site.domain,
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": account_activation_token.make_token(user),
        },
    )

    return send_email(subject, html_content, user.email)


def send_generated_password_email(request, user, password):
    """
    Envia e-mail com senha gerada para novo usuário
    """
    logger.info(f"🔄 Preparando email de senha para: {user.email}")

    current_site = get_current_site(request)
    subject = "Sua Nova Senha de Acesso ao SisCoE"

    # Tentar obter o objeto Cadastro associado ao usuário
    cadastro_data = None
    try:
        if hasattr(user, "profile") and user.profile.cadastro:
            cadastro_data = user.profile.cadastro
        else:
            cadastro_data = Cadastro.objects.filter(email=user.email).first()
    except Exception as e:
        logger.warning(f"⚠️ Não foi possível obter dados do cadastro: {e}")

    html_content = render_to_string(
        "email/account_activated_with_password.html",
        {
            "user": user,
            "password": password,
            "protocol": "https" if request.is_secure() else "http",
            "domain": current_site.domain,
            "cadastro_data": cadastro_data,
        },
    )

    # Log da ação
    log_user_action(
        user=user,
        action=f"Envio de e-mail com senha temporária para {user.email}",
        request=request,
    )

    # Enviar email
    try:
        result = send_email(subject, html_content, user.email)
        if result:
            logger.info(f"✅ Email de senha enviado com sucesso para {user.email}")
        else:
            logger.error(f"❌ Falha ao enviar email de senha para {user.email}")
        return result
    except Exception as e:
        logger.error(f"❌ Erro ao enviar e-mail de senha: {str(e)}", exc_info=True)
        return False


def log_user_action(user, action, request=None):
    """
    Registra ações do usuário no sistema
    """
    ip_address = get_client_ip(request) if request else None
    computer_name = get_computer_name(ip_address) if ip_address else None

    try:
        UserActionLog.objects.create(
            user=user,
            action=action,
            timestamp=timezone.now(),
            ip_address=ip_address,
            computer_name=computer_name,
        )
        return True
    except Exception as e:
        logger.error(f"Erro ao registrar ação do usuário: {str(e)}", exc_info=True)
        return False


# ... (funções send_email, send_mail_to_user, send_generated_password_email)


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def get_computer_name(ip_address):
    if not ip_address:
        return None
    try:
        # Tenta resolver o nome do host a partir do IP
        # Pode ser lento ou falhar em algumas redes/configurações
        name, aliaslist, ipaddrlist = socket.gethostbyaddr(ip_address)
        return name
    except socket.herror:
        return None
    except Exception as e:
        logger.warning(f"Erro ao obter nome do computador para IP {ip_address}: {e}")
        return None


def log_user_action(user, action, request=None):
    """
    Registra ações do usuário no sistema
    """
    ip_address = get_client_ip(request) if request else None
    computer_name = get_computer_name(ip_address) if ip_address else None

    try:
        UserActionLog.objects.create(
            user=user,
            action=action,
            timestamp=timezone.now(),
            ip_address=ip_address,
            computer_name=computer_name,
        )
        # Atualiza last_login_ip e last_login_computer_name no modelo User
        user.last_login_ip = ip_address
        user.last_login_computer_name = computer_name
        user.save(
            update_fields=["last_login_ip", "last_login_computer_name"]
        )  # Salva apenas os campos alterados
        return True
    except Exception as e:
        logger.error(f"Erro ao registrar ação do usuário: {str(e)}", exc_info=True)
        return False


# Conecta ao signal user_logged_in do Django para garantir que o last_login seja atualizado
@receiver(user_logged_in)
def update_user_last_login_data(sender, request, user, **kwargs):
    ip_address = get_client_ip(request)
    computer_name = get_computer_name(ip_address)

    user.last_login_ip = ip_address
    user.last_login_computer_name = computer_name

    # Marca explicitamente como online e evita que o pre_save override
    user.is_online = True
    # user._force_online = True  # Esta flag não é mais necessária se o save for feito aqui

    # AQUI ESTÁ A LINHA CRÍTICA QUE ESTAVA FALTANDO OU FOI REMOVIDA
    user.update_login_history(
        ip=ip_address, computer_name=computer_name, login_time=timezone.now()
    )

    # Garante que last_login também é salvo, pois o pre_save em signals.py depende dele
    # E que login_history é salvo
    user.save(
        update_fields=[
            "last_login_ip",
            "last_login_computer_name",
            "is_online",
            "last_login",
            "login_history",
        ]
    )

    # Se a flag for usada em outro lugar, pode ser mantida, mas não é estritamente necessária aqui
    # if hasattr(user, '_force_online'):
    #     del user._force_online


def cleanup_history_data():
    """
    Exclui registros de histórico de ações e acessos com mais de 6 meses.
    """
    logger.info("Iniciando a limpeza de registros de histórico...")

    # Define o período de retenção (6 meses)
    six_months_ago = timezone.now() - timedelta(days=180)

    # 1. Limpeza do UserActionLog
    try:
        action_logs_to_delete = UserActionLog.objects.filter(timestamp__lt=six_months_ago)
        count_action_logs = action_logs_to_delete.count()
        if count_action_logs > 0:
            action_logs_to_delete.delete()
            logger.info(f'{count_action_logs} registros de UserActionLog foram excluídos.')
        else:
            logger.info('Nenhum registro de UserActionLog para excluir.')
    except Exception as e:
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
            logger.info(f'{total_entries_removed} entradas de login_history foram removidas de {total_users_processed} usuários.')
        else:
            logger.info('Nenhum registro de login_history para excluir.')

    except Exception as e:
        logger.error(f'Erro ao limpar login_history: {e}', exc_info=True)

    logger.info('Limpeza de histórico concluída com sucesso!')
