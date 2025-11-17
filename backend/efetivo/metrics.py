from prometheus_client import Counter, Gauge

# ==============================================================================
# MÉTRICAS DE NEGÓCIO PARA O APP EFETIVO
# ==============================================================================

# --- 1. Gauge: Total de militares por categoria (Ativo, Inativo, LTS, etc.) ---
# Usamos um Gauge porque o valor pode tanto aumentar quanto diminuir.
# A métrica terá um "label" (etiqueta) chamado "categoria" para segmentar os dados.
efetivo_militares_por_categoria = Gauge(
    "efetivo_militares_por_categoria_total",
    "Total de militares por categoria de efetivo (ATIVO, INATIVO, LTS, etc.)",
    ["categoria"],
)

# --- 2. Counter: Total de atualizações na situação funcional ---
# Usamos um Counter porque este valor apenas incrementa.
# Ele nos dará a taxa de mudanças na situação funcional dos militares.
efetivo_situacao_funcional_updates_total = Counter(
    "efetivo_situacao_funcional_updates_total",
    "Total de atualizações (criação e modificação) na situação funcional de um militar.",
)
