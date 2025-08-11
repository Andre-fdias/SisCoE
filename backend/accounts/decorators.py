# accounts/decorators.py
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from django.db.models import QuerySet # Importa QuerySet para anotação de tipo
from backend.accounts.models import User # Importa o modelo User para usar o método filter_by_permissions

def _redirect_with_message(request, message, redirect_to_self=False):
    """
    Função auxiliar para adicionar uma mensagem de erro e redirecionar o usuário.
    Se 'redirect_to_self' for True e o usuário estiver autenticado, redireciona para
    o perfil do próprio usuário. Caso contrário, redireciona para a página de login.
    """
    messages.error(request, message)
    if redirect_to_self and request.user.is_authenticated and hasattr(request.user, 'pk'):
        # Redireciona para o perfil do usuário logado (assumindo 'accounts:user_detail' com pk)
        return redirect('accounts:user_detail', pk=request.user.pk)
    # Redirecionamento padrão para a página de login
    return redirect('accounts:login')

def permissao_necessaria(level):
    """
    Decorador que verifica se o usuário tem um nível de permissão mínimo
    (baseado no campo 'permissoes' do modelo User).

    Exemplo de uso em uma view:
    @login_required
    @permissao_necessaria(level='gestor')
    def minha_view(request):
        # ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Primeiro, verifica se o usuário está autenticado
            if not request.user.is_authenticated:
                return _redirect_with_message(request, "Por favor, faça login para acessar esta página.")
            
            # Se autenticado, verifica o nível de permissão usando o método personalizado
            if request.user.has_permission_level(level):
                return view_func(request, *args, **kwargs)
            else:
                # Caso não tenha permissão, redireciona com mensagem de erro
                return _redirect_with_message(request, "Você não tem permissão para acessar esta página.", redirect_to_self=True)
        return _wrapped_view
    return decorator

# NOVO DECORADOR para aplicar o filtro de permissões do modelo
def apply_model_permissions_filter(model_class):
    """
    Decorador que aplica o filtro de permissões baseado no SGB do usuário
    (definido no método filter_by_permissions do modelo User)
    ao QuerySet de um modelo específico e o anexa ao objeto request.
    
    A view decorada poderá acessar o QuerySet filtrado via request.filtered_queryset.
    
    Args:
        model_class (models.Model): A classe do modelo Django a ser filtrada (ex: Cadastro).
    
    Exemplo de uso em uma view:
    @login_required
    @permissao_necessaria(level='sgb') # Pode ser combinado com outros decoradores de permissão
    @apply_model_permissions_filter(Cadastro) # Aplica o filtro ao QuerySet de Cadastro
    def minha_view(request):
        # Agora, request.filtered_queryset contém os objetos Cadastro filtrados
        # de acordo com as permissões do usuário logado.
        # Você pode então aplicar filtros adicionais a este QuerySet já filtrado.
        cadastros_efetivos = request.filtered_queryset.filter(latest_status='Efetivo')
        # ... o restante da sua lógica da view
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # É crucial que o usuário esteja autenticado para que request.user exista.
            # O decorador @login_required (ou permissao_necessaria) deve ser aplicado antes deste.
            if not request.user.is_authenticated:
                # Caso este decorador seja usado sem @login_required, garante o redirecionamento
                return _redirect_with_message(request, "Por favor, faça login para acessar esta página.")

            # Aplica o filtro de permissões do usuário ao QuerySet base do modelo
            # e anexa o resultado ao objeto request.
            # Usa 'model_class.objects.all()' para obter o QuerySet base do modelo especificado.
            request.filtered_queryset = request.user.filter_by_permissions(model_class.objects.all())
            
            # Chama a view original
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def permission_required(perm):
    """
    Decorador que verifica se o usuário tem uma permissão específica do Django
    (e.g., 'app_name.can_do_something').

    Exemplo de uso em uma view:
    @login_required
    @permission_required('efetivo.acesso_painel_admin')
    def outra_view(request):
        # ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Primeiro, verifica se o usuário está autenticado
            if not request.user.is_authenticated:
                return _redirect_with_message(request, "Por favor, faça login para acessar esta página.")
            
            # Superusuários sempre têm todas as permissões
            if request.user.is_superuser or request.user.has_perm(perm):
                return view_func(request, *args, **kwargs)
            else:
                # Caso não tenha permissão, redireciona com mensagem de erro
                return _redirect_with_message(request, "Acesso negado: Permissão insuficiente.", redirect_to_self=True)
        return _wrapped_view
    return decorator

def group_required(*group_names):
    """
    Decorador que verifica se o usuário pertence a um dos grupos especificados.

    Exemplo de uso em uma view:
    @login_required
    @group_required('Administradores', 'Gerentes')
    def view_por_grupo(request):
        # ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Primeiro, verifica se o usuário está autenticado
            if not request.user.is_authenticated:
                return _redirect_with_message(request, "Por favor, faça login para acessar esta página.")
            
            # Superusuários sempre têm todas as permissões
            if request.user.is_superuser or request.user.groups.filter(name__in=group_names).exists():
                return view_func(request, *args, **kwargs)
            else:
                # Caso não tenha permissão, redireciona com mensagem de erro
                return _redirect_with_message(request, "Acesso negado: Grupo não autorizado.", redirect_to_self=True)
        return _wrapped_view
    return decorator
