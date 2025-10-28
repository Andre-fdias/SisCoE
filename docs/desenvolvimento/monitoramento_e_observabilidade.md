# 🛠️ Documentação do Sistema de Monitoramento e Observabilidade do SisCoE

Este documento detalha a arquitetura e a implementação do sistema de versionamento, monitoramento e observabilidade para a aplicação SisCoE, conforme o plano de DevOps solicitado.

## 1. Stack de Ferramentas

-   **Versionamento**: Git, Tags Semânticas e Changelog.
-   **Coleta de Métricas**: `django-prometheus` integrado ao Django.
-   **Armazenamento e Consulta de Métricas**: Prometheus.
-   **Visualização e Dashboards**: Grafana.
-   **Alertas**: Prometheus com Alertmanager (configuração inicial).

---

## 2. Estratégia de Versionamento

Foi definida uma estratégia de Versionamento Semântico (`MAJOR.MINOR.PATCH`) para governar as releases do projeto, com foco em compliance e auditoria.

> 📖 A documentação completa está disponível em: [`docs/desenvolvimento/versionamento.md`](./versionamento.md).

---

## 3. Coleta de Métricas na Aplicação Django

Para expor as métricas da aplicação, utilizamos a biblioteca `django-prometheus`.

### 3.1. Instalação

As seguintes dependências foram adicionadas ao `requirements.txt`:

```txt
django-prometheus
prometheus-client
```

### 3.2. Configuração no `settings.py`

O arquivo `backend/settings/base.py` foi modificado para registrar o app e seus middlewares:

-   `'django_prometheus'` foi adicionado ao `INSTALLED_APPS`.
-   Os middlewares `PrometheusBeforeMiddleware` (no início) e `PrometheusAfterMiddleware` (no fim) foram adicionados à lista `MIDDLEWARE` para medir a latência de todas as requisições.

### 3.3. Exposição do Endpoint de Métricas

No arquivo `backend/urls.py`, a seguinte rota foi adicionada para que o Prometheus possa acessar as métricas:

```python
path('prometheus/', include('django_prometheus.urls')),
```

---

## 4. Métricas Customizadas (Negócio e Segurança)

Além das métricas padrão, criamos métricas específicas para os requisitos do SisCoE, utilizando o sistema de Sinais (Signals) do Django.

### 4.1. Métricas de BI do Efetivo

-   **Objetivo**: Monitorar a quantidade de militares por categoria (Ativo, Inativo, etc.) e a taxa de atualização de suas situações funcionais.
-   **Implementação**:
    1.  **`backend/efetivo/metrics.py`**: Criado para definir as métricas `efetivo_militares_por_categoria_total` (Gauge) e `efetivo_situacao_funcional_updates_total` (Counter).
    2.  **`backend/efetivo/signals.py`**: Criado para definir os *handlers* que atualizam as métricas acima sempre que um objeto `CatEfetivo` ou `DetalhesSituacao` é salvo ou deletado.
    3.  **`backend/efetivo/apps.py`**: Modificado para importar e registrar os sinais na inicialização da aplicação.

### 4.2. Métricas de Segurança de Contas

-   **Objetivo**: Monitorar tentativas de login falhas para detectar possíveis ataques.
-   **Implementação**:
    1.  **`backend/accounts/metrics.py`**: Criado para definir a métrica `accounts_login_failures_total` (Counter).
    2.  **`backend/accounts/signals.py`**: Criado para definir um *handler* que escuta o sinal `user_login_failed` do Django e incrementa o contador.
    3.  **`backend/accounts/apps.py`**: Modificado para registrar o sinal de segurança.

---

## 5. Configuração do Prometheus e Alertas

### 5.1. Coleta de Métricas (`prometheus.yml`)

-   Um arquivo de configuração foi criado em `monitoring/prometheus.yml`.
-   Ele define um *job* chamado `siscoe_django_app` que coleta as métricas expostas pelo Django em `localhost:8000/prometheus/metrics`.

### 5.2. Regras de Alerta Inteligente

-   **Objetivo**: Ser notificado proativamente sobre possíveis incidentes de segurança.
-   **Implementação**:
    1.  O arquivo `monitoring/rules/security_alerts.yml` foi criado.
    2.  Nele, foi definida a regra `TaxaElevadaDeFalhasDeLogin`, que entra em estado de alerta se a taxa de falhas de login exceder 5 por minuto.
    3.  O arquivo `monitoring/prometheus.yml` foi atualizado para carregar este novo arquivo de regras.

---

## 6. Visualização com Grafana

-   **Objetivo**: Ter uma visão gráfica e intuitiva das métricas de negócio.
-   **Implementação**:
    -   Um template de dashboard foi criado em `monitoring/grafana_dashboards/efetivo_dashboard.json`.
    -   Este dashboard pode ser importado no Grafana e contém painéis para:
        -   Total de Militares Ativos (Gauge).
        -   Taxa de Atualização de Situação Funcional (Gráfico de Linha).
        -   Distribuição de Militares por Categoria (Gráfico de Barras).

---

## 7. Indicador de Versionamento na Interface

Para facilitar a identificação da versão da aplicação em execução, um indicador de versionamento foi adicionado à interface do usuário.

### 7.1. Implementação

1.  **`backend/__version__.py`:** Criado para armazenar a string da versão (ex: `"1.0.0"`).
2.  **`backend/core/context_processors.py`:** Criado para ler o valor de `__version__` e injetá-lo no contexto de todos os templates como `app_version`.
3.  **`backend/settings/base.py`:** O context processor `backend.core.context_processors.version_indicator` foi adicionado à lista `TEMPLATES['OPTIONS']['context_processors']`.
4.  **`backend/core/templates/landing.html`:** O valor `v{{ app_version }}` foi adicionado ao rodapé da página, próximo à informação de copyright.

---

## 8. Logging Estruturado com ELK Stack

Para uma observabilidade completa, configuramos o Django para gerar logs estruturados (JSON), que podem ser facilmente ingeridos e analisados por um ELK Stack (Elasticsearch, Logstash, Kibana).

### 8.1. Configuração no Django

-   **Dependência:** A biblioteca `python-json-logger` foi adicionada ao `requirements.txt`.
-   **`backend/settings/base.py`:** O dicionário `LOGGING` foi atualizado para incluir:
    -   Um novo formatador `json_formatter` usando `python_json_logger.json_logger.JsonFormatter`.
    -   Um novo handler `json_file` que escreve logs JSON no arquivo `logs/app.json.log`.
    -   O handler `json_file` foi adicionado aos `handlers` do logger `root` e do logger `django`.
-   **Diretório de Logs:** O diretório `logs/` foi criado na raiz do projeto para armazenar os logs JSON.

### 8.2. Integração com Docker Compose (ELK Stack)

Os seguintes serviços foram adicionados ao `docker-compose.yml` para orquestrar o ELK Stack:

-   **`elasticsearch`:** Armazena e indexa os logs.
-   **`logstash`:** Processa os logs JSON do Django e os envia para o Elasticsearch.
    -   O volume `./logs:/var/log/django_app` foi montado no serviço `app` e no `logstash` para que o Logstash possa ler o `app.json.log` gerado pelo Django.
    -   O arquivo de configuração `monitoring/logstash/pipeline/logstash.conf` foi criado para definir o pipeline de ingestão.
-   **`kibana`:** Fornece a interface de usuário para buscar, visualizar e criar dashboards com os logs.

### 8.3. Configuração do Logstash (`monitoring/logstash/pipeline/logstash.conf`)

Este arquivo define o pipeline de ingestão do Logstash:

```conf
input {
  file {
    path => "/var/log/django_app/app.json.log" # Caminho dentro do container Logstash
    start_position => "beginning"
    sincedb_path => "/dev/null" # Em produção, use um caminho persistente.
    codec => json # Informa ao Logstash que o conteúdo é JSON
    type => "django_json_log"
  }
}

filter {
  # Adiciona campos úteis para o Kibana
  mutate {
    add_field => { "[@metadata][beat]" => "filebeat" }
    add_field => { "[@metadata][version]" => "7.17.9" }
  }
  # Renomeia o campo 'message' para 'log.original' para compatibilidade com ECS
  if [message] {
    rename => { "message" => "log.original" }
  }
  # Adiciona o nome do serviço
  mutate {
    add_field => { "service.name" => "siscoe-django" }
  }
  # Adiciona o tipo de log
  mutate {
    add_field => { "event.dataset" => "siscoe.log" }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"] # Aponta para o serviço Elasticsearch no Docker Compose
    index => "siscoe-logs-%{+YYYY.MM.dd}"
  }
  stdout { codec => rubydebug } # Para depuração
}
```

### 8.4. Como Usar o ELK Stack

1.  **Inicie os serviços Docker:**
    ```bash
    docker-compose up -d
    ```
2.  **Acesse o Kibana:** `http://localhost:5601`
3.  **Crie um Index Pattern:** No Kibana, vá para "Stack Management" -> "Index Patterns" e crie um novo com o nome `siscoe-logs-*` e selecione `@timestamp` como campo de tempo.
4.  **Visualize:** Em "Analytics" -> "Discover", selecione o index pattern para ver seus logs estruturados.


