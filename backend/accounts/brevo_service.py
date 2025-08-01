from django.conf import settings
import requests
import json
import logging
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

def send_brevo_email(subject, html_content, to_email, from_email=None, from_name=None):
    """
    Versão aprimorada com mais logs e tratamento de erros
    """
    brevo_api_url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "api-key": settings.BREVO_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    sender_name = from_name or settings.DEFAULT_FROM_NAME
    sender_email = from_email or settings.DEFAULT_FROM_EMAIL

    # Verificação básica dos parâmetros
    if not settings.BREVO_API_KEY:
        logger.error("Chave API do Brevo não configurada")
        return False

    payload = {
        "sender": {
            "name": sender_name,
            "email": sender_email
        },
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content
    }

    try:
        logger.info(f"Preparando para enviar e-mail para {to_email}")
        logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            brevo_api_url,
            headers=headers,
            data=json.dumps(payload),
            timeout=30
        )
        
        response.raise_for_status()
        response_data = response.json()
        
        logger.info(f"E-mail enviado com sucesso para {to_email}")
        logger.debug(f"Resposta Brevo: {response_data}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Falha ao enviar e-mail para {to_email}"
        
        if hasattr(e, 'response'):
            error_msg += f" - Status: {e.response.status_code}"
            try:
                error_details = e.response.json()
                error_msg += f" - Detalhes: {error_details}"
            except:
                error_msg += f" - Response: {e.response.text}"
        
        logger.error(error_msg, exc_info=True)
        return False
        
    except Exception as e:
        logger.error(f"Erro inesperado ao enviar e-mail: {str(e)}", exc_info=True)
        return False
