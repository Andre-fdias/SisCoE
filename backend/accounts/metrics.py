from prometheus_client import Counter

# ==============================================================================
# MÉTRICAS DE SEGURANÇA PARA O APP ACCOUNTS
# ==============================================================================

# --- 1. Counter: Total de tentativas de login falhas ---
# Usamos um Counter porque este valor apenas incrementa.
# É uma métrica de segurança crucial para detectar ataques de força bruta.
accounts_login_failures_total = Counter(
    'accounts_login_failures_total',
    'Total de tentativas de login que falharam.'
)
