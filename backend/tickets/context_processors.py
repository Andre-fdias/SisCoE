from .models import Chamado

def tickets_count(request):
    """
    Context processor para incluir contagem de tickets abertos em todas as páginas
    """
    if request.user.is_authenticated and request.user.is_admin:
        tickets_abertos_count = Chamado.objects.filter(status='aberto').count()
    else:
        tickets_abertos_count = 0
        
    return {
        'tickets_abertos_count': tickets_abertos_count
    }