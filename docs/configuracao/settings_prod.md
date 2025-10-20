# Configurações de Produção (`prod.py`)

O arquivo `backend/settings/prod.py` é onde as configurações são ajustadas para o **ambiente de produção**. A segurança, o desempenho e a robustez são as principais prioridades aqui.

!!! danger "Ambiente de Produção"
    Este arquivo deve ser usado apenas em um servidor de produção. Para ativá-lo, a variável de ambiente `DJANGO_SETTINGS_MODULE` deve apontar para `backend.settings.prod`.

---

## Configurações Específicas

### `DEBUG`

É fundamental que o `DEBUG` seja `False` em produção para evitar a exposição de informações sensíveis sobre a configuração do projeto.

```python
DEBUG = False
```

### `ALLOWED_HOSTS`

Esta configuração é carregada da variável de ambiente `ALLOWED_HOSTS` e deve conter o(s) domínio(s) exato(s) onde a aplicação está hospedada.

```python
# Exemplo no .env: ALLOWED_HOSTS=meusite.com.br,www.meusite.com.br
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())
```

### `DATABASES`

Em produção, o SisCoE é configurado para usar **PostgreSQL**, um banco de dados relacional robusto e confiável. As credenciais de conexão (`DB_NAME`, `DB_USER`, etc.) são carregadas de forma segura a partir de variáveis de ambiente.

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        # ...
    }
}
```

### `CACHES` com Redis

Para otimizar o desempenho, a produção utiliza o **Redis** como um backend de cache de alto desempenho. Ele é usado para armazenar dados frequentemente acessados e também para gerenciar as sessões dos usuários, reduzindo a carga sobre o banco de dados.

```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        # ...
    }
}
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
```

### `EMAIL_BACKEND`

Para o envio de e-mails reais em produção, o sistema é configurado para usar um servidor **SMTP**, neste caso, o da **Brevo**. As credenciais são carregadas de variáveis de ambiente.

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp-relay.brevo.com'
# ...
EMAIL_HOST_USER = config('BREVO_SMTP_USER')
EMAIL_HOST_PASSWORD = config('BREVO_SMTP_PASSWORD')
```

### Diretivas de Segurança

Um conjunto de middlewares e configurações de segurança é ativado em produção para proteger a aplicação contra ataques comuns:

-   **`SECURE_SSL_REDIRECT`**: Redireciona todo o tráfego HTTP para HTTPS.
-   **`SESSION_COOKIE_SECURE`** e **`CSRF_COOKIE_SECURE`**: Garantem que os cookies só sejam enviados através de conexões seguras (HTTPS).
-   **`SECURE_HSTS_SECONDS`**: Ativa o HSTS (HTTP Strict Transport Security) para forçar o navegador a usar apenas conexões seguras por um longo período.
-   **`SECURE_BROWSER_XSS_FILTER`** e **`SECURE_CONTENT_TYPE_NOSNIFF`**: Adicionam camadas extras de proteção no navegador contra ataques de XSS e sniffing de tipo de conteúdo.