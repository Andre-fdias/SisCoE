import socket

def get_client_ip(request):
    """Obtém o endereço IP real do cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_computer_name(request):
    """Tenta obter o nome do computador do cliente"""
    try:
        ip = get_client_ip(request)
        if ip:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname.split('.')[0]  # Retorna apenas o nome sem o domínio
    except:
        pass
    return None