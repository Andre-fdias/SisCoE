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


def get_user_display_name(user):
    """
    Retorna o nome de exibição mais apropriado para o usuário.
    A ordem de preferência é: nome de guerra, nome completo, email.
    """
    if hasattr(user, "cadastro") and user.cadastro and user.cadastro.nome_de_guerra:
        return user.cadastro.nome_de_guerra

    full_name = user.get_full_name()
    if full_name:
        return full_name

    return user.email
