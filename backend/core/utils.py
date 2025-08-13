# backend/core/utils.py
from django.db.models import Q
from backend.efetivo.models import DetalhesSituacao

def filter_by_user_sgb(queryset, user):
    """
    Filtra um queryset de Cadastro ou modelos relacionados pelo SGB do usuário
    """
    if user.is_superuser or user.permissoes in ['admin', 'gestor']:
        return queryset
    
    if user.permissoes == 'sgb':
        # Obtém o SGB do usuário logado
        user_sgb = None
        if hasattr(user, 'cadastro') and user.cadastro:
            latest_situacao = DetalhesSituacao.objects.filter(
                cadastro=user.cadastro
            ).order_by('-data_alteracao').first()
            if latest_situacao:
                user_sgb = latest_situacao.sgb
        
        if user_sgb:
            # Filtra os cadastros que têm pelo menos um DetalhesSituacao com o mesmo SGB
            return queryset.filter(
                detalhes_situacao__sgb=user_sgb
            ).distinct()
        else:
            return queryset.none()
    
    return queryset.none()