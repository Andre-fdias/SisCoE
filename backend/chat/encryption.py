import base64
from django.conf import settings
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def get_key():
    """
    Deriva uma chave de criptografia da CHAT_ENCRYPTION_KEY.
    Isso garante que a chave tenha o comprimento correto para o Fernet.
    """
    password = settings.CHAT_ENCRYPTION_KEY.encode()
    # O salt pode ser fixo se você quiser que a mesma chave seja gerada sempre.
    # Idealmente, para maior segurança, o salt deveria ser armazenado e único,
    # mas para este caso de uso (descriptografar dados existentes), ele precisa ser constante.
    salt = b"siscoe-chat-salt"
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    return key


def encrypt_message(text):
    """Criptografa uma mensagem."""
    if not settings.CHAT_ENCRYPTION_KEY or not text:
        return text

    try:
        f = Fernet(get_key())
        encrypted_text = f.encrypt(text.encode())
        return encrypted_text.decode()
    except Exception:
        # Se a criptografia falhar, retorne o texto original
        return text


def decrypt_message(encrypted_text):
    """Descriptografa uma mensagem."""
    if not settings.CHAT_ENCRYPTION_KEY or not encrypted_text:
        return encrypted_text

    try:
        f = Fernet(get_key())
        # Tenta decodificar como string, depois converte para bytes
        decrypted_text = f.decrypt(encrypted_text.encode())
        return decrypted_text.decode()
    except Exception:
        # Se a descriptografia falhar (pode ser texto plano), retorne o texto como está
        return encrypted_text
