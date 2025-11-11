
import time
from django.core.cache import cache

class PerformanceMetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Inicializa as métricas no cache se não existirem
        cache.add('total_requests', 0)
        cache.add('total_request_time', 0.0)
        cache.add('error_count_4xx', 0)
        cache.add('error_count_5xx', 0)

    def __call__(self, request):
        # Ignora as requisições do próprio painel de controle para não inflar as métricas
        if request.path.startswith('/control-panel'):
            return self.get_response(request)

        start_time = time.time()
        
        response = self.get_response(request)
        
        duration = time.time() - start_time

        # Incrementa as métricas no cache de forma atômica
        cache.incr('total_requests')
        cache.incr_by('total_request_time', duration)

        if 400 <= response.status_code < 500:
            cache.incr('error_count_4xx')
        elif 500 <= response.status_code < 600:
            cache.incr('error_count_5xx')

        return response
