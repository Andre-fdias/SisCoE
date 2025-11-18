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


from django.utils.deprecation import MiddlewareMixin
import re

class SpinnerMiddleware(MiddlewareMixin):
    """
    Middleware inteligente que so injeta spinner em paginas HTML completas
    """
    
    def process_response(self, request, response):
        # Verifica se e uma resposta HTML completa (nao partials/JSON)
        content_type = response.get('Content-Type', '')
        is_html = 'text/html' in content_type 
        is_success = response.status_code == 200
        
        # NAO injeta em:
        # - Requisicoes HTMX
        # - Respostas JSON
        # - Partial responses
        # - API calls
        # - Requests com headers especificos
        is_htmx = request.headers.get('HX-Request') == 'true'
        is_api = any([
            '/api/' in request.path,
            request.path.startswith('/ajax/'),
            'application/json' in content_type,
            request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        ])
        
        should_inject = (is_html and is_success and 
                        not is_htmx and not is_api and
                        hasattr(response, 'content') and response.content)
        
        if should_inject:
            try:
                content = response.content.decode('utf-8')
                
                # Verifica se e uma pagina completa com estrutura HTML
                is_full_page = all([
                    '<!DOCTYPE html>' in content or '<html' in content,
                    '<head>' in content,
                    '<body>' in content
                ])
                
                # So injeta em paginas completas que nao tenham spinner
                has_spinner = 'global-spinner-container' in content
                
                if is_full_page and not has_spinner:
                    
                    spinner_html = """
<!-- SPINNER INJETADO POR MIDDLEWARE -->
<div id="global-spinner-container" class="fixed inset-0 z-[9999] flex items-center justify-center bg-gray-900 bg-opacity-80 hidden">
    <div class="bg-white p-6 rounded-lg shadow-xl flex flex-col items-center">
        <div class="flex space-x-2 mb-4">
            <div class="w-4 h-4 bg-blue-500 rounded-full animate-bounce"></div>
            <div class="w-4 h-4 bg-green-500 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
            <div class="w-4 h-4 bg-purple-500 rounded-full animate-bounce" style="animation-delay: 0.4s"></div>
        </div>
        <p class="text-gray-700 font-medium">SisCoE - Carregando...</p>
    </div>
</div>

<script>
// SPINNER AUTOMATICO - MIDDLEWARE
(function() {
    'use strict';
    
    // So executa se nao houver conflito
    if (typeof window.GlobalSpinner !== 'undefined') return;
    
    const spinner = document.getElementById('global-spinner-container');
    
    window.GlobalSpinner = {
        show: function() { 
            if(spinner) {
                spinner.classList.remove('hidden');
                // Forcar reflow para animacao
                setTimeout(() => spinner.style.opacity = '1', 10);
            }
        },
        hide: function() { 
            if(spinner) {
                spinner.style.opacity = '0';
                setTimeout(() => spinner.classList.add('hidden'), 300);
            }
        }
    };
    
    // Eventos basicos - prevenindo duplicacao
    let eventsRegistered = false;
    
    function setupEvents() {
        if (eventsRegistered) return;
        
        // Esconder quando DOM estiver pronta
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                setTimeout(() => GlobalSpinner.hide(), 100);
            });
        } else {
            setTimeout(() => GlobalSpinner.hide(), 100);
        }
        
        // Navegacao por links
        document.addEventListener('click', function(e) {
            const target = e.target.closest('a');
            if (target && 
                target.href && 
                !target.href.startsWith('javascript:') && 
                !target.hasAttribute('data-no-spinner') &&
                target.target !== '_blank' &&
                target.hostname === window.location.hostname) {
                setTimeout(() => GlobalSpinner.show(), 150);
            }
        });
        
        // Formularios
        document.addEventListener('submit', function(e) {
            if (!e.target.hasAttribute('data-no-spinner')) {
                GlobalSpinner.show();
            }
        });
        
        // Before unload
        window.addEventListener('beforeunload', function() {
            GlobalSpinner.show();
        });
        
        eventsRegistered = true;
    }
    
    // Iniciar eventos
    setupEvents();
    
})();
</script>
"""
                    
                    if '</body>' in content:
                        content = content.replace('</body>', spinner_html + '</body>')
                        response.content = content.encode('utf-8')
                        
            except (UnicodeDecodeError, AttributeError):
                # Ignora silenciosamente
                pass
                
        return response