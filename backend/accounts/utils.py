import socket


def get_client_ip(request):
    """Obtém o endereço IP real do cliente"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def get_computer_name(request):
    """Tenta obter o nome do computador do cliente"""
    try:
        ip = get_client_ip(request)
        if ip:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname.split(".")[0]  # Retorna apenas o nome sem o domínio
    except:
        pass
    return None


from backend.efetivo.models import Promocao, DetalhesSituacao


def get_client_ip(request):
    """Obtém o endereço IP real do cliente"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def get_computer_name(request):
    """Tenta obter o nome do computador do cliente"""
    try:
        ip = get_client_ip(request)
        if ip:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname.split(".")[0]  # Retorna apenas o nome sem o domínio
    except:
        pass
    return None


def get_user_display_name(user):
    """
    Retorna o nome de exibição formatado para o usuário.
    Formato: Posto/grad RE/Díg Nome de Guerra - SGB.
    """
    if hasattr(user, "cadastro") and user.cadastro:
        cadastro = user.cadastro
        parts = []

        # 1. Posto/Graduação (da última promoção)
        ultima_promocao = Promocao.objects.filter(cadastro=cadastro).order_by('-ultima_promocao').first()
        if ultima_promocao:
            parts.append(ultima_promocao.posto_grad)
        
        # 2. RE e Dígito
        if cadastro.re and cadastro.dig:
            parts.append(f"{cadastro.re}-{cadastro.dig}")

        # 3. Nome de Guerra
        if cadastro.nome_de_guerra:
            parts.append(cadastro.nome_de_guerra)

        # 4. SGB (do último detalhe de situação)
        ultimo_detalhe = DetalhesSituacao.objects.filter(cadastro=cadastro).order_by('-data_alteracao').first()
        if ultimo_detalhe and ultimo_detalhe.sgb:
            parts.append(f"- {ultimo_detalhe.sgb}")

        if parts:
            return " ".join(parts)

    # Fallback para nome completo ou email
    full_name = user.get_full_name()
    if full_name:
        return full_name

    return user.email
