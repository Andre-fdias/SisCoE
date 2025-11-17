# brevo_service.py

from django.conf import settings
import requests
import json
import logging
from time import sleep

logger = logging.getLogger(__name__)


def test_brevo_connection():
    """
    Função para testar a conexão com o Brevo
    """
    logger.info("🧪 Testando conexão com Brevo...")

    try:
        brevo_api_key = getattr(settings, "BREVO_API_KEY", None)
        if not brevo_api_key:
            logger.error("❌ BREVO_API_KEY não encontrada nas settings")
            return False

        # Testa a autenticação fazendo uma requisição simples
        test_url = "https://api.brevo.com/v3/account"
        headers = {"api-key": brevo_api_key, "Accept": "application/json"}

        response = requests.get(test_url, headers=headers, timeout=10)

        if response.status_code == 200:
            logger.info("✅ Conexão com Brevo: OK")
            return True
        elif response.status_code == 401:
            error_data = response.json()
            logger.error(f"❌ Falha na autenticação Brevo: {error_data}")
            if "IP" in str(error_data):
                logger.critical(
                    "🚨 IP não autorizado! Adicione o IP em: https://app.brevo.com/security/authorised_ips"
                )
            return False
        else:
            logger.error(f"❌ Erro na conexão Brevo: Status {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"❌ Erro ao testar conexão Brevo: {str(e)}")
        return False


def send_brevo_email(
    subject, html_content, to_email, from_email=None, from_name=None, max_retries=2
):
    """
    Versão aprimorada com retry e melhor tratamento de erros
    """
    # Verificação da chave API
    try:
        brevo_api_key = getattr(settings, "BREVO_API_KEY", None)
        if not brevo_api_key:
            logger.error("❌ Chave API do Brevo não configurada nas settings")
            return False

        logger.debug(f"✅ API Key encontrada: {brevo_api_key[:10]}...")

    except AttributeError as e:
        logger.error(f"❌ Erro ao acessar settings.BREVO_API_KEY: {e}")
        return False

    brevo_api_url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "api-key": brevo_api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    sender_name = from_name or getattr(settings, "DEFAULT_FROM_NAME", "SisCoE Sistema")
    sender_email = from_email or getattr(
        settings, "DEFAULT_FROM_EMAIL", "andrefonsecadias21@gmail.com"
    )

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
        "sender": {"name": sender_name, "email": sender_email},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content,
    }

    # Tentativa com retry
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"📧 Tentativa {attempt + 1} - Enviando e-mail para {to_email}")
            logger.debug(f"Remetente: {sender_name} <{sender_email}>")
            logger.debug(f"Assunto: {subject}")

            response = requests.post(
                brevo_api_url, headers=headers, data=json.dumps(payload), timeout=30
            )

            if response.status_code == 401:
                error_data = response.json()
                if "unauthorized" in error_data.get(
                    "message", ""
                ).lower() and "IP" in error_data.get("message", ""):
                    logger.error("❌ ERRO CRÍTICO: IP não autorizado no Brevo")
                    logger.error(
                        "🔧 Solução: Adicione o IP 177.84.247.135 em: https://app.brevo.com/security/authorised_ips"
                    )
                    return False

            response.raise_for_status()
            response_data = response.json()

            logger.info(f"✅ E-mail enviado com sucesso para {to_email}")
            logger.debug(f"Resposta Brevo: {response_data}")

            return True

        except requests.exceptions.RequestException as e:
            error_msg = (
                f"❌ Tentativa {attempt + 1} - Falha ao enviar e-mail para {to_email}"
            )

            if hasattr(e, "response") and e.response is not None:
                error_msg += f" - Status: {e.response.status_code}"
                try:
                    error_details = e.response.json()
                    error_msg += f" - Detalhes: {error_details}"

                    # Tratamento específico para erro de IP não autorizado
                    if e.response.status_code == 401 and "IP" in str(error_details):
                        logger.critical("🚨 IP NÃO AUTORIZADO NO BREVO")
                        logger.critical(
                            "🔧 Acesse: https://app.brevo.com/security/authorised_ips"
                        )
                        logger.critical("🔧 Adicione o IP: 177.84.247.135")
                        break  # Não tente novamente para este erro

                except:
                    error_msg += f" - Response: {e.response.text}"
            else:
                error_msg += f" - Erro: {str(e)}"

            logger.error(error_msg)

            # Se não for a última tentativa, espera antes de tentar novamente
            if attempt < max_retries:
                wait_time = 2**attempt  # Exponential backoff
                logger.info(f"⏳ Aguardando {wait_time}s antes da próxima tentativa...")
                sleep(wait_time)
            else:
                logger.error("❌ Todas as tentativas de envio falharam")

        except Exception as e:
            logger.error(
                f"❌ Erro inesperado ao enviar e-mail: {str(e)}", exc_info=True
            )
            if attempt < max_retries:
                sleep(2**attempt)
            else:
                return False

    return False
