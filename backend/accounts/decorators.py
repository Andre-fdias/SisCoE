# accounts/decorators.py
from django.http import HttpResponseForbidden
from functools import wraps

def permission_required(perm):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
                
            if request.user.has_perm(perm):
                return view_func(request, *args, **kwargs)
                
            return HttpResponseForbidden("Acesso negado: Permissão insuficiente")
        return _wrapped_view
    return decorator

def group_required(*group_names):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
                
            if request.user.groups.filter(name__in=group_names).exists():
                return view_func(request, *args, **kwargs)
                
            return HttpResponseForbidden("Acesso negado: Grupo não autorizado")
        return _wrapped_view
    return decorator