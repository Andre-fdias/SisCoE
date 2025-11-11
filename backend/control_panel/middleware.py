
import time

from django.core.cache import cache



class PerformanceMetricsMiddleware:

    def __init__(self, get_response):

        self.get_response = get_response

        # Garante que as chaves existam no cache. Usa set() que é seguro.

        # O timeout=None garante que as chaves não expirem.

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



        # Usa uma abordagem get/set que é compatível com todos os backends de cache

        total_requests = cache.get('total_requests', 0) + 1

        total_request_time = cache.get('total_request_time', 0.0) + duration

        

        cache.set('total_requests', total_requests, None)

        cache.set('total_request_time', total_request_time, None)



        if 400 <= response.status_code < 500:

            error_count_4xx = cache.get('error_count_4xx', 0) + 1

            cache.set('error_count_4xx', error_count_4xx, None)

        elif 500 <= response.status_code < 600:

            error_count_5xx = cache.get('error_count_5xx', 0) + 1

            cache.set('error_count_5xx', error_count_5xx, None)



        return response


