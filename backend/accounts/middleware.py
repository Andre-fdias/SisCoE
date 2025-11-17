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
            reverse("accounts:force_password_change"),
            reverse("accounts:logout"),
            reverse("accounts:admin_login"),
            "/static/",
            "/admin/",
            "/media/",
        ]

    def __call__(self, request):
        # Ignora middleware para superusuários
        if request.user.is_authenticated and request.user.is_superuser:
            return self.get_response(request)

        # Verifica se precisa redirecionar para troca de senha
        if (
            request.user.is_authenticated
            and request.user.must_change_password
            and not any(request.path.startswith(url) for url in self.exempt_urls)
            and request.path not in self.exempt_urls
        ):

            return redirect("accounts:force_password_change")

        return self.get_response(request)


from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta

User = get_user_model()


class UpdateLastActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated:
            # Atualiza o last_login a cada request para manter o usuário online
            threshold = timezone.now() - timedelta(minutes=15)
            if not request.user.last_login or request.user.last_login < threshold:
                User.objects.filter(pk=request.user.pk).update(
                    last_login=timezone.now(), is_online=True
                )

        return response
