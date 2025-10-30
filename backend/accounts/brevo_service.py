# brevo_service.py

from django.conf import settings
import requests
import json
import logging

logger = logging.getLogger(__name__)

def send_brevo_email(subject, html_content, to_email, from_email=None, from_name=None):
    """
    Versão aprimorada com mais logs e tratamento de erros
    """
    # Verificação da chave API com tratamento mais robusto
    try:
        brevo_api_key = getattr(settings, 'BREVO_API_KEY', None)
        if not brevo_api_key:
            logger.error("❌ Chave API do Brevo não configurada nas settings")
            logger.error("❌ Verifique se BREVO_API_KEY está definida no .env")
            return False
        
        logger.debug(f"✅ API Key encontrada: {brevo_api_key[:10]}...")
        
    except AttributeError as e:
        logger.error(f"❌ Erro ao acessar settings.BREVO_API_KEY: {e}")
        return False

    brevo_api_url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "api-key": brevo_api_key,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    sender_name = from_name or getattr(settings, 'DEFAULT_FROM_NAME', 'SisCoE Sistema')
    sender_email = from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', 'andrefonsecadias21@gmail.com')

    # Verificação básica dos parâmetros
    if not to_email:
        logger.error("❌ Email do destinatário não especificado")
        return False
        
    if not subject:
        logger.error("❌ Assunto do email não especificado")
        return False
        
    if not html_content:
        logger.error("❌ Conteúdo HTML do email não especificado")
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
        logger.info(f"📧 Preparando para enviar e-mail para {to_email}")
        logger.debug(f"Remetente: {sender_name} <{sender_email}>")
        logger.debug(f"Assunto: {subject}")
        
        response = requests.post(
            brevo_api_url,
            headers=headers,
            data=json.dumps(payload),
            timeout=30
        )
        
        response.raise_for_status()
        response_data = response.json()
        
        logger.info(f"✅ E-mail enviado com sucesso para {to_email}")
        logger.debug(f"Resposta Brevo: {response_data}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        error_msg = f"❌ Falha ao enviar e-mail para {to_email}"
        
        if hasattr(e, 'response') and e.response is not None:
            error_msg += f" - Status: {e.response.status_code}"
            try:
                error_details = e.response.json()
                error_msg += f" - Detalhes: {error_details}"
            except:
                error_msg += f" - Response: {e.response.text}"
        else:
            error_msg += f" - Erro: {str(e)}"
        
        logger.error(error_msg, exc_info=True)
        return False
        
    except Exception as e:
        logger.error(f"❌ Erro inesperado ao enviar e-mail: {str(e)}", exc_info=True)
        return False