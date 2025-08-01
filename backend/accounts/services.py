# backend/accounts/services.py

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.conf import settings
from .tokens import account_activation_token
from .models import UserActionLog, TermosAceite
from .utils import get_client_ip, get_computer_name
from django.contrib.auth import get_user_model
import logging
import requests
import json
from django.utils import timezone

# Importar o modelo Cadastro
from backend.efetivo.models import Cadastro 

logger = logging.getLogger(__name__)
User = get_user_model()


def send_email(subject, html_content, recipient_email):
    """
    Função auxiliar para enviar e-mails usando a API do Brevo.
    """
    brevo_api_url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "api-key": settings.BREVO_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    sender_name = "SisCoE Suporte"
    sender_email = settings.DEFAULT_FROM_EMAIL

    payload = {
        "sender": {
            "name": sender_name,
            "email": sender_email
        },
        "to": [
            {
                "email": recipient_email
            }
        ],
        "subject": subject,
        "htmlContent": html_content
    }

    try:
        response = requests.post(brevo_api_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        logger.info(f"E-mail enviado com sucesso para {recipient_email} via API do Brevo. Resposta: {response.json()}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao enviar e-mail para {recipient_email} via API do Brevo: {e}", exc_info=True)
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_details = e.response.json()
                logger.error(f"Detalhes do erro da API do Brevo: {error_details}")
            except json.JSONDecodeError:
                logger.error(f"Resposta de erro da API do Brevo não é JSON: {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"Erro inesperado ao enviar e-mail para {recipient_email}: {e}", exc_info=True)
        return False


def send_mail_to_user(request, user):
    """
    Envia e-mail de redefinição de senha.
    """
    current_site = get_current_site(request)
    subject = 'Redefinição de senha'
    html_content = render_to_string('email/password_reset_email.html', {
        'user': user,
        'protocol': 'https' if request.is_secure() else 'http',
        'domain': current_site.domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
    })
    
    return send_email(subject, html_content, user.email)

def send_generated_password_email(request, user, password):
    """
    Envia e-mail com senha gerada para novo usuário
    """
    current_site = get_current_site(request)
    subject = 'Sua Nova Senha de Acesso ao SisCoE'

    # Tentar obter o objeto Cadastro associado ao usuário
    cadastro_data = None
    try:
        # Assumindo que o Profile do usuário tem um campo 'cadastro' que aponta para o modelo Cadastro
        # Ou que o User tem um OneToOneField para Cadastro, ou que o Cadastro tem um ForeignKey para User
        # Se o seu modelo User tem um campo 'cadastro' diretamente:
        # cadastro_data = user.cadastro 
        
        # Se o Profile está linkado ao User e o Profile tem o campo 'cadastro':
        if hasattr(user, 'profile') and user.profile.cadastro:
            cadastro_data = user.profile.cadastro
        else:
            # Fallback: tentar encontrar Cadastro pelo email do usuário, se não houver profile ou link direto
            cadastro_data = Cadastro.objects.filter(email=user.email).first()

    except Cadastro.DoesNotExist:
        logger.warning(f"Cadastro não encontrado para o usuário {user.email} ao enviar e-mail de senha.")
    except Exception as e:
        logger.error(f"Erro ao buscar dados de Cadastro para o usuário {user.email}: {e}", exc_info=True)

    html_content = render_to_string('email/account_activated_with_password.html', {
        'user': user,
        'password': password,
        'protocol': 'https' if request.is_secure() else 'http',
        'domain': current_site.domain,
        'cadastro_data': cadastro_data, # Passa o objeto cadastro_data para o template
    })
    
    log_user_action(
        user=user,
        action=f"Envio de e-mail com senha temporária para {user.email}",
        request=request
    )
    
    try:
        return send_email(subject, html_content, user.email)
    except Exception as e:
        logger.error(f"Erro ao enviar e-mail de senha: {str(e)}", exc_info=True)
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
            computer_name=computer_name
        )
        return True
    except Exception as e:
        logger.error(f"Erro ao registrar ação do usuário: {str(e)}", exc_info=True)
        return False

