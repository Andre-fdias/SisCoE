import socket
from backend.efetivo.models import Promocao, DetalhesSituacao

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

def get_user_display_name(user):
    """
    Gera o nome de exibição formatado para um usuário de forma robusta.
    Formato: posto_grad re-dig nome_de_guerra - sgb
    """
    # Define um nome de fallback seguro desde o início
    fallback_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email

    try:
        if hasattr(user, 'cadastro') and user.cadastro:
            cadastro = user.cadastro
            promocao = Promocao.objects.filter(cadastro=cadastro).order_by('-ultima_promocao').first()
            situacao = DetalhesSituacao.objects.filter(cadastro=cadastro).order_by('-data_alteracao').first()

            parts = []
            if promocao and promocao.posto_grad:
                parts.append(promocao.posto_grad)

            if cadastro.re and cadastro.dig and cadastro.nome_de_guerra:
                parts.append(f"{cadastro.re}-{cadastro.dig}")
                parts.append(cadastro.nome_de_guerra)
            else:
                # Se os dados essenciais não existirem, retorna o fallback
                return fallback_name

            main_name = " ".join(parts)

            if situacao and situacao.sgb:
                return f"{main_name} - {situacao.sgb}"
            
            return main_name
        else:
            # Se o usuário não tiver um perfil 'cadastro', retorna o fallback
            return fallback_name
    except Exception:
        # Se qualquer outro erro ocorrer, retorna o fallback
        return fallback_name