import time
from functools import wraps
from prometheus_client import Histogram

# ==============================================================================
# MÉTRICAS E DECORATORS PARA MONITORAMENTO DE PERFORMANCE
# ==============================================================================

# --- 1. Histogram: Latência de execução de funções críticas ---
# Usamos um Histogram para agrupar as durações em "buckets" (faixas de tempo).
# Isso nos permite calcular não apenas a média, mas também percentis (p95, p99),
# que são essenciais para entender a performance real da aplicação.
FUNCTION_LATENCY_SECONDS = Histogram(
    "function_latency_seconds",
    "Latência de execução para funções monitoradas",
    ["function_name"],  # Label para identificar a função que foi medida
)


# --- 2. Decorator: @track_function_latency ---
def track_function_latency(func):
    """
    Um decorator que mede o tempo de execução da função decorada e
    registra a duração no histograma FUNCTION_LATENCY_SECONDS.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            return func(*args, **kwargs)
        finally:
            end_time = time.time()
            duration = end_time - start_time
            # Registra a duração na métrica, usando o nome da função como label.
            FUNCTION_LATENCY_SECONDS.labels(function_name=func.__name__).observe(
                duration
            )

    return wrapper
