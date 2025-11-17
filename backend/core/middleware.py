from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
import re
from django.contrib import messages
from django.http import JsonResponse


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.login_url = settings.LOGIN_URL
        self.exempt_urls = [reverse(self.login_url).lstrip("/")]
        if hasattr(settings, "LOGIN_EXEMPT_URLS"):
            self.exempt_urls += [url.lstrip("/") for url in settings.LOGIN_EXEMPT_URLS]

        # Adicionar URLs de redefinição de senha à lista de isenção
        self.exempt_urls += [
            "accounts/password_reset/",
            "accounts/password_reset/done/",
            "accounts/reset/<uidb64>/<token>/",
            "accounts/reset/done/",
        ]

        # Adicionar URLs de admin, static e media
        self.exempt_urls += [
            settings.STATIC_URL.lstrip("/"),
            settings.MEDIA_URL.lstrip("/"),
            "admin/".lstrip("/"),
        ]

    def __call__(self, request):
        # Verifica se o caminho da requisição corresponde a alguma URL isenta
        path = request.path_info.lstrip("/")
        if not request.user.is_authenticated:
            if not any(re.match(url, path) for url in self.exempt_urls):
                return redirect(self.login_url)

        response = self.get_response(request)
        return response


class JSONMessagesMiddleware:
    """
    Este middleware processa mensagens do Django para requisições AJAX (HTMX).
    Se houver mensagens, ele as retorna em uma resposta JSON.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_template_response(self, request, response):
        # Verifica se é uma requisição HTMX ou AJAX
        is_htmx = request.headers.get("HX-Request") == "true"
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if is_htmx or is_ajax:
            # Coleta as mensagens
            django_messages = []
            for message in messages.get_messages(request):
                django_messages.append(
                    {"level": message.level_tag, "message": message.message}
                )

            if django_messages:
                # Adiciona as mensagens ao contexto do template
                if hasattr(response, "context_data"):
                    response.context_data["messages"] = django_messages

                # Para algumas requisições, pode ser melhor retornar um JSON puro
                # Aqui, estamos apenas adicionando ao contexto,
                # mas você poderia retornar um JsonResponse se a lógica do frontend preferir.
                # Exemplo:
                # return JsonResponse({"messages": django_messages})

        return response
