# accounts/middleware.py

from django.utils.deprecation import MiddlewareMixin
from .services import log_user_action

class UserActionLoggingMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated:
            action = f"Accessed {view_func.__name__} view"
            log_user_action(request.user, action, request)
        return None
    
from django.urls import reverse
from django.shortcuts import redirect

class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_urls = [
            reverse('accounts:force_password_change'),
            reverse('accounts:logout'),
            reverse('accounts:admin_login'),
            '/static/',
            '/admin/',
            '/media/'
        ]

    def __call__(self, request):
        # Ignora middleware para superusuários
        if request.user.is_authenticated and request.user.is_superuser:
            return self.get_response(request)
            
        # Verifica se precisa redirecionar para troca de senha
        if (request.user.is_authenticated and 
            request.user.must_change_password and
            not any(request.path.startswith(url) for url in self.exempt_urls) and
            request.path not in self.exempt_urls):
            
            return redirect('accounts:force_password_change')
        
        return self.get_response(request)