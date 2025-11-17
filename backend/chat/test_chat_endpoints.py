#!/usr/bin/env python
import requests

# Configurações
BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/accounts/login/"
CHAT_CONVERSATIONS_URL = f"{BASE_URL}/api/chat/conversations/"

# Credenciais de teste
credentials = {
    "username": "seu_usuario",  # Substitua pelo seu usuário
    "password": "sua_senha",  # Substitua pela sua senha
}


def test_chat_endpoints():
    # Cria sessão
    session = requests.Session()

    # Primeiro, faça login para obter o CSRF token
    print("🔐 Fazendo login...")
    login_response = session.get(LOGIN_URL)

    # Extrai CSRF token
    csrf_token = None
    if "csrftoken" in session.cookies:
        csrf_token = session.cookies["csrftoken"]
    elif "csrf" in login_response.text:
        # Tenta extrair do HTML
        import re

        match = re.search(
            r'name="csrfmiddlewaretoken" value="([^"]+)"', login_response.text
        )
        if match:
            csrf_token = match.group(1)

    if not csrf_token:
        print("❌ Não foi possível obter CSRF token")
        return

    print(f"✅ CSRF Token obtido: {csrf_token[:20]}...")

    # Faz login
    login_data = credentials.copy()
    login_data["csrfmiddlewaretoken"] = csrf_token

    login_response = session.post(
        LOGIN_URL, data=login_data, headers={"Referer": LOGIN_URL}
    )

    if login_response.status_code == 200 and "login" not in login_response.url:
        print("✅ Login realizado com sucesso!")
    else:
        print("❌ Falha no login")
        return

    # Testa endpoint de conversas
    print("\n📋 Testando endpoint de conversas...")
    conversations_response = session.get(CHAT_CONVERSATIONS_URL)

    if conversations_response.status_code == 200:
        conversations = conversations_response.json()
        print(f"✅ Conversas obtidas: {len(conversations)} conversas encontradas")

        # Lista as conversas
        for conv in conversations:
            print(f"   - {conv.get('id')}: {conv.get('name', 'Sem nome')}")

            # Testa endpoint de exclusão de conversa
            delete_url = f"{CHAT_CONVERSATIONS_URL}{conv['id']}/delete_conversation/"
            print(f"   🔗 DELETE: {delete_url}")

    else:
        print(f"❌ Erro ao obter conversas: {conversations_response.status_code}")
        print(conversations_response.text)

    # Testa se há mensagens em alguma conversa
    if conversations:
        first_conv = conversations[0]
        conv_id = first_conv["id"]

        print(f"\n💬 Testando mensagens da conversa {conv_id}...")
        messages_url = f"{CHAT_CONVERSATIONS_URL}{conv_id}/messages/"
        messages_response = session.get(messages_url)

        if messages_response.status_code == 200:
            messages = messages_response.json()
            print(f"✅ Mensagens obtidas: {len(messages)} mensagens")

            # Lista algumas mensagens
            for msg in messages[:3]:  # Primeiras 3 mensagens
                print(f"   - {msg.get('id')}: {msg.get('text', 'Sem texto')[:50]}...")

                # Testa endpoint de exclusão de mensagem
                delete_msg_url = f"{messages_url}{msg['id']}/delete_message/"
                print(f"   🔗 DELETE: {delete_msg_url}")

        else:
            print(f"❌ Erro ao obter mensagens: {messages_response.status_code}")


if __name__ == "__main__":
    test_chat_endpoints()
